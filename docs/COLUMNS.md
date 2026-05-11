# GMP AI Use Data — Column Reference

A reference for every column in the GMP survey export that relates to AI
use, plus the demographic stratifiers the tracker uses. This is the
**source-side** companion to [`TRACKER.md`](TRACKER.md), which documents
the metric layer built on top.

Source: GMP AI Use Data column inventory (see
[`GMP AI Use Data Columns.pdf`](GMP%20AI%20Use%20Data%20Columns.pdf)).

---

## Contents

- [1. Quick map](#1-quick-map)
- [2. Survey question columns](#2-survey-question-columns)
- [3. Demographic stratifier columns](#3-demographic-stratifier-columns)
- [4. How columns map to dashboard metrics](#4-how-columns-map-to-dashboard-metrics)
- [5. Reserved (currently unused) columns](#5-reserved-currently-unused-columns)

---

## 1. Quick map

| Column | Role | Used by tracker? |
|---|---|---|
| `ai_freq` | AI-use frequency (exposure) | ✓ Adoption Rate · Frequency Mean · dose-response |
| `ai_impact_work` | Self-reported AI impact on work (outcome) | ✓ All impact metrics (12 metrics in §4) |
| `ai_use_general` | What AI is used for in general life | — Reserved for future use |
| `ai_use_social` | Use of AI in social contexts | — Reserved for future use |
| `ai_impact_personal` | Self-reported AI impact on personal life | — Reserved for future use |
| `country` | Country (stratifier) | ✓ All country-stratum metrics |
| `gender`, `biological_sex` | Gender (stratifier; biological\_sex is fallback) | ✓ Gender-stratum metrics |
| `age` | Age (stratifier; coerced to band) | ✓ Age-band stratum metrics |
| `year`, `month` | Time grain | ✓ Monthly partitioning |

## 2. Survey question columns

### 2.1 `ai_freq` — AI-use frequency

The headline **exposure** variable. Captures how often a respondent uses an
AI assistant. Seven canonical ordinal levels are recognised, with the
following raw-value mappings:

| Integer | Canonical label | Raw values mapped |
|---|---|---|
| 0 | Never | "I have never used an AI assistant" |
| 1 | Rarely | "Rarely" |
| 2 | Monthly | "A few times a month" |
| 3 | Weekly | "Several days a week" |
| 4 | Daily | "Several times a day" |
| 5 | Constantly | "Constantly", "Constamment", "Constantly (when awake)" |
| 6 | Always | "All of the time" |
| — | (null) | "N/A" or any other value |

Notes:
- `Constamment` is the French rendering and `Constantly (when awake)` is a
  spec variant; both map to level 5.
- Respondents at level 0 ("Never") are **excluded** from impact metrics
  but counted toward the adoption-rate denominator.

### 2.2 `ai_impact_work` — Self-reported AI impact on work

The headline **outcome** variable. Multi-select; raw value is pipe-delimited
(`|`). Each atomic option is split out into a binary flag:

| Flag | Atomic option (raw) | Sentiment |
|---|---|---|
| `impact_none` | "No impact" · "Nenhum impacto" | Neutral |
| `impact_improved_quality` | "Improved my work quality or output" | **Positive** |
| `impact_new_opportunities` | "Created new job or income opportunities" | **Positive** |
| `impact_adaptation_pressure` | "Increased pressure to adapt or work faster" | **Negative** |
| `impact_job_anxiety` | "Made me worry about the future of my job or industry" | **Negative** |
| `impact_job_loss` | "Caused me to lose my job" | **Negative** |
| `impact_reduced_income` | "Reduced my income or made it harder to find work" | **Negative** |
| `impact_other` | "Another impact not listed here" | Neutral |
| `impact_not_sure` | "Not sure" · "No estoy seguro/a" · "Not No estoy seguro/a" | Neutral |
| `impact_na` | All-N/A or blank | — |

Notes:
- Respondents can pick multiple options, so multiple flags may be true for
  the same person.
- Unknown atomic options fall through to `impact_other`.
- Rows where all answers are "N/A" or blank get `impact_na = true` and are
  **excluded** from impact-share denominators (but still counted toward
  adoption-rate denominators).
- Translation variants (e.g. Portuguese "Nenhum impacto", Spanish "No
  estoy seguro/a") are observed in the data and mapped to their English
  canonical flag.

## 3. Demographic stratifier columns

### 3.1 `country`

Free-text country name. The tracker canonicalises against an ISO-3166
dictionary (English long-form), with explicit aliases for non-Latin-script
variants observed in the data — for example, Devanagari "भारत (इंडिया)"
and its MacRoman-mangled rendering both map to "India".

The dashboard separately maps the canonical English name to the
Natural Earth atlas form for choropleth rendering — see [DASHBOARD.md §8](DASHBOARD.md).

### 3.2 `gender` / `biological_sex`

Two related columns. The tracker uses `gender` when present and non-null;
falls back to `biological_sex` otherwise. Valid values:

- Female
- Male
- Non-binary
- Other/Intersex
- Prefer not to say

Any other value is coerced to `null`.

### 3.3 `age`

Mixed type. May arrive as an integer age (handled specially for 18–20) or
as a pre-existing age-band string. The tracker normalises to one of nine
canonical bands:

`18-20` · `21-24` · `25-34` · `35-44` · `45-54` · `55-64` · `65-74` ·
`75-84` · `85+`

Integer ages 18–20 are mapped to `"18-20"`. Any other value that doesn't
match a canonical band becomes `null`.

### 3.4 `year`, `month`

Survey-submission year and integer month (1–12). Used as the time grain
for every metric table in the Parquet output.

## 4. How columns map to dashboard metrics

| Dashboard metric | Source column(s) | How |
|---|---|---|
| Weighted Impact Index | `ai_impact_work` (× `ai_freq` for the user filter) | Sum of signed weights across all impact flags, averaged over AI users with any impact response |
| Net Impact Index | `ai_impact_work` | Share with any positive flag − share with any negative flag |
| AI Adoption Rate | `ai_freq` | Share with `ai_freq != Never` |
| Frequency Mean | `ai_freq` | Mean of the 0–6 integer scale |
| Improved Quality (share) | `ai_impact_work` | `impact_improved_quality` flag share within impact denominator |
| New Opportunities (share) | `ai_impact_work` | `impact_new_opportunities` flag share |
| Adaptation Pressure (share) | `ai_impact_work` | `impact_adaptation_pressure` flag share |
| Job Anxiety (share) | `ai_impact_work` | `impact_job_anxiety` flag share |
| Job Loss (share) | `ai_impact_work` | `impact_job_loss` flag share |
| Reduced Income (share) | `ai_impact_work` | `impact_reduced_income` flag share |
| Dose-response | `ai_freq` × `ai_impact_work` | Net impact computed separately within each `ai_freq` level |
| Respondents | (all rows) | Count after stratification |
| Impact Denominator | `ai_freq`, `ai_impact_work` | Count of AI users with any non-blank impact response |

Stratification: every metric is computed once for each combination of
`country`, `gender`, `age_band`, and (`year`, `month`). See
[`TRACKER.md` §2](TRACKER.md) for the eight stratum levels.

## 5. Reserved (currently unused) columns

These columns are present in the GMP AI Use export but are **not consumed
by the tracker today**. They are placeholders for future iterations.

| Column | Likely content | Possible future use |
|---|---|---|
| `ai_use_general` | What AI is used for outside of work (multi-select) | Tag-cloud of common use cases; cross-tab against impact |
| `ai_use_social` | How AI is used in social/relational contexts (multi-select) | Standalone impact track parallel to the work one |
| `ai_impact_personal` | Self-reported AI impact on personal life (multi-select) | Mental health, relationships, sleep, leisure — would mirror the work-impact pipeline |

Adding any of these is mechanical: implement an analogous `parse_*` step in
the normalisation layer, define share/index metrics in the metric layer,
and add a new stratum dimension if needed. The existing layout in
[`TRACKER.md`](TRACKER.md) accommodates additive columns under a minor
version bump.

---

## Related docs

- [`TRACKER.md`](TRACKER.md) — full metric specification and ETL contract
- [`DASHBOARD.md`](DASHBOARD.md) — dashboard architecture and algorithms
- [`DASHBOARD_SIMPLE.md`](DASHBOARD_SIMPLE.md) — plain-English dashboard guide
