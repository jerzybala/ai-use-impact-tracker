# AI Use Impact Tracker — Metric Specification

**Version:** 0.1 (draft)
**Owner:** Jerzy Bala, Chief Data Scientist, Sapien Labs
**Status:** For review — definitions below are the authoritative contract between ETL, metric layer, and dashboard

---

## 1. Purpose

This document formally defines every quantity computed by the AI Use Impact Tracker. It is the single source of truth for the ETL pipeline, the metric layer, and the dashboard. Any change to a definition here requires a version bump and a rebuild of the Parquet outputs.

## 2. Grain

All metrics are computed at the following grain:

```
(stratum_level, stratum_value, year, month)
```

where `stratum_level` is one of `{global, country, gender, age_band, country_gender, country_age_band, gender_age_band, country_gender_age_band}`. Each stratum level is emitted as a separate Parquet partition.

Respondent-level records are intermediate; the tracker only publishes stratified aggregates.

## 3. Input Columns (from GMP)

| Source column | Role | Type |
|---|---|---|
| `ai_freq` | Exposure | 7-level ordinal (string) |
| `ai_impact_work` | Outcome | Multi-select, pipe-delimited (string) |
| `country` | Stratifier | Categorical (string) |
| `gender` / `biological_sex` | Stratifier | Categorical (string) |
| `age` | Stratifier | Mixed integer + band (string/int) |
| `year`, `month` | Time | Integer |

## 4. Normalisation Rules

### 4.1 `ai_freq` → integer scale

| Canonical label | Integer | Raw values mapped |
|---|---|---|
| Never | 0 | "I have never used an AI assistant" |
| Rarely | 1 | "Rarely" |
| Monthly | 2 | "A few times a month" |
| Weekly | 3 | "Several days a week" |
| Daily | 4 | "Several times a day" |
| Constantly | 5 | "Constantly", "Constamment", "Constantly (when awake)" |
| Always | 6 | "All of the time" |
| (null) | — | "N/A", any other value |

### 4.2 `ai_impact_work` → seven binary flags

The raw field is split on `|` and each atomic option yields one Boolean flag:

| Flag | Raw atomic option | Sentiment |
|---|---|---|
| `impact_none` | "No impact" | Neutral |
| `impact_improved_quality` | "Improved my work quality or output" | **Positive** |
| `impact_new_opportunities` | "Created new job or income opportunities" | **Positive** |
| `impact_adaptation_pressure` | "Increased pressure to adapt or work faster" | **Negative** |
| `impact_job_anxiety` | "Made me worry about the future of my job or industry" | **Negative** |
| `impact_other` | "Another impact not listed here" | Neutral |
| `impact_not_sure` | "Not sure", "No estoy seguro/a", "Not No estoy seguro/a" | Neutral |

Multiple flags may be true for the same respondent. An all-"N/A" cell yields `impact_na = true` and all other flags false; such rows are **excluded** from impact-share denominators but retained for adoption-rate denominators.

### 4.3 `age` → age band

Integer ages 18–20 map to band `"18-20"`. All other values pass through if they already match one of `{"21-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75-84", "85+"}`; any other value becomes `null`.

### 4.4 `gender`

Use `gender` when present and non-null; fall back to `biological_sex`. Values outside `{Female, Male, Non-binary, Other/Intersex, Prefer not to say}` are coerced to `null`.

### 4.5 `country`

Canonicalised against an ISO-3166 dictionary; non-Latin-script variants (e.g. Hindi rendering of "India") map to their canonical English name. Countries below the minimum-N threshold for a given month are pooled under `"(Other)"` in the country stratum but remain un-pooled in the global stratum.

## 5. Metrics

### 5.1 Core indicators (per stratum per month)

| Metric | Definition | Denominator |
|---|---|---|
| `n_respondents` | Count of respondents in stratum | — |
| `adoption_rate` | Share with `ai_freq >= 1` | All respondents in stratum |
| `freq_mean` | Mean of `ai_freq` integer scale | Respondents with non-null `ai_freq` |
| `freq_distribution` | Array of shares, one per ordinal level 0–6 | Respondents with non-null `ai_freq` |

### 5.2 Impact indicators (per stratum per month)

Denominator for every metric in this section: respondents with `ai_freq >= 1` AND at least one impact flag set (i.e. excludes "never used" and excludes all-N/A).

| Metric | Definition |
|---|---|
| `impact_share_improved_quality` | Share where `impact_improved_quality = true` |
| `impact_share_new_opportunities` | Share where `impact_new_opportunities = true` |
| `impact_share_adaptation_pressure` | Share where `impact_adaptation_pressure = true` |
| `impact_share_job_anxiety` | Share where `impact_job_anxiety = true` |
| `impact_share_none` | Share where `impact_none = true` |
| `impact_share_other` | Share where `impact_other = true` |
| `impact_share_not_sure` | Share where `impact_not_sure = true` |
| `positive_impact_share` | Share where `impact_improved_quality OR impact_new_opportunities` |
| `negative_impact_share` | Share where `impact_adaptation_pressure OR impact_job_anxiety` |
| **`net_impact_index`** | `positive_impact_share − negative_impact_share`, range [−1, 1] |

### 5.3 Dose-response

For each stratum × month, compute `net_impact_index` within each `ai_freq` level (0–6). This is emitted as a nested array column `dose_response` indexed by frequency level.

### 5.4 Confidence intervals

For all share metrics, compute a 95% Wilson score interval. For `freq_mean`, compute a standard-error-based 95% CI. CIs are emitted as `{metric}_ci_low` and `{metric}_ci_high` columns.

## 6. Minimum-N Suppression

Any stratum-month cell with `n_respondents < 50` is flagged `suppressed = true` and its metric values are written as `null`. The dashboard must not display suppressed cells.

For multi-dimensional strata (e.g. country × gender × age_band), the threshold is applied to the finest cell. Under-represented countries roll up to `"(Other)"` before the threshold is applied at the country level.

## 7. Output Schema Contract

Parquet is partitioned as:

```
output/v1/metrics/stratum_level={level}/year={YYYY}/month={MM}/part-0.parquet
```

Column order is fixed. Adding columns is allowed in minor versions; removing or renaming columns requires a major version bump (`v2/`).

## 8. Known Limitations (v0.1)

- No survey weights applied; metrics treat respondents as an equal-weighted sample.
- Self-selection bias not adjusted; associations between `ai_freq` and impact are descriptive.
- Composition effects not decomposed; month-over-month changes may reflect respondent mix, not attitude shift.
- CIs assume simple random sampling; will be revised when weights are introduced.

These are explicit Phase 1 scope boundaries. Phase 2 will add weighting and compositional adjustment.
