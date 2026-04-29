# AI Use Impact Tracker — Metric Specification

**Version:** 0.2
**Owner:** Jerzy Bala, Chief Data Scientist, Sapien Labs
**Status:** Authoritative contract between ETL, metric layer, and dashboard

**Changes since v0.1**
- §4.2 — added `impact_job_loss` and `impact_reduced_income` flags (negative sentiment).
- §5.2 — added `weighted_impact_index` (signed-weight per-respondent score, averaged over the impact denominator).
- §7 — added `country_gender`, `country_age_band`, `country_gender_age_band` cross-strata to the published Parquet output (already computed in v0.1, now part of the published contract).
- §9 — added rolling-window pooling rules used by the dashboard.

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

### 4.2 `ai_impact_work` → nine binary flags

The raw field is split on `|` and each atomic option yields one Boolean flag:

| Flag | Raw atomic option | Sentiment |
|---|---|---|
| `impact_none` | "No impact", "Nenhum impacto" | Neutral |
| `impact_improved_quality` | "Improved my work quality or output" | **Positive** |
| `impact_new_opportunities` | "Created new job or income opportunities" | **Positive** |
| `impact_adaptation_pressure` | "Increased pressure to adapt or work faster" | **Negative** |
| `impact_job_anxiety` | "Made me worry about the future of my job or industry" | **Negative** |
| `impact_job_loss` | "Caused me to lose my job" | **Negative** |
| `impact_reduced_income` | "Reduced my income or made it harder to find work" | **Negative** |
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
| `impact_share_job_loss` | Share where `impact_job_loss = true` |
| `impact_share_reduced_income` | Share where `impact_reduced_income = true` |
| `impact_share_none` | Share where `impact_none = true` |
| `impact_share_other` | Share where `impact_other = true` |
| `impact_share_not_sure` | Share where `impact_not_sure = true` |
| `positive_impact_share` | Share where `impact_improved_quality OR impact_new_opportunities` |
| `negative_impact_share` | Share where any of `impact_adaptation_pressure`, `impact_job_anxiety`, `impact_job_loss`, `impact_reduced_income` |
| **`net_impact_index`** | `positive_impact_share − negative_impact_share`, range [−1, 1] |
| **`weighted_impact_index`** | Mean across the impact denominator of the per-respondent score, where score = sum of `IMPACT_WEIGHTS[flag]` for each flag set true. See §5.2.1. |

Shares can sum to more than 100% because multiple flags may be true for the same respondent.

#### 5.2.1 `IMPACT_WEIGHTS` (Tara's weighted index)

| Flag | Weight |
|---|---:|
| `impact_new_opportunities` | +1.0 |
| `impact_improved_quality` | +0.5 |
| `impact_job_anxiety` | −0.25 |
| `impact_adaptation_pressure` | −0.5 |
| `impact_reduced_income` | −0.75 |
| `impact_job_loss` | −1.0 |
| `impact_none`, `impact_other`, `impact_not_sure` | 0 |

Range is roughly [−1, +1] but the distribution is **not symmetric** — a respondent must select multiple negative flags simultaneously to reach the lower bound. Confidence interval (`weighted_impact_index_ci_low/high`) is the 95% normal-approximation interval `mean ± 1.96 · SE`.

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

`{level}` is one of the eight values in §2. The `country_gender`, `country_age_band`, and `country_gender_age_band` cross-strata are required for the dashboard's combined gender × age filtering.

`dose_response` is a JSON-encoded string column: an object keyed by ai_freq integer level (`"0"`–`"6"`) with `net_impact_index` value or `null` when below `MIN_N` for that level.

Column order is fixed. Adding columns is allowed in minor versions; removing or renaming columns requires a major version bump (`v2/`).

## 8. Known Limitations

- No survey weights applied; metrics treat respondents as an equal-weighted sample.
- Self-selection bias not adjusted; associations between `ai_freq` and impact are descriptive.
- Composition effects not decomposed; month-over-month changes may reflect respondent mix, not attitude shift.
- CIs assume simple random sampling; will be revised when weights are introduced.
- `IMPACT_WEIGHTS` (§5.2.1) reflect editorial judgment by the Sapien Labs team about relative severity, not empirical calibration.

These are explicit Phase 1 scope boundaries. Phase 2 will add weighting and compositional adjustment.

## 9. Rolling-Window Pooling (dashboard only)

The dashboard's **Period** selector (Single month / Last 3 / Last 6) pools precomputed monthly cells into a rolling window. Pooling is performed client-side on the embedded JSON; it does not change the published Parquet output.

Pooling rules per (country × gender × age) cell across the window months:

| Field | Aggregation | Weight |
|---|---|---|
| `n_respondents`, `n_impact_denominator` | sum | — |
| `adoption_rate`, `freq_mean` | weighted mean | `n_respondents` |
| `weighted_impact_index`, `net_impact_index`, all `impact_share_*`, `positive_impact_share`, `negative_impact_share` | weighted mean | `n_impact_denominator` |
| `dose_response[k]` (for k = 1…6) | weighted mean | `n_impact_denominator` |

**This is approximate.** The exact pooled value would require re-running the metric layer on the pooled respondent-level data; the dashboard's weighted-mean of monthly aggregates is correct in expectation but ignores within-month variance. Suppression cells (originally below `MIN_N`) are dropped before pooling, so a country may appear in the rolling window even if some constituent months were individually suppressed.
