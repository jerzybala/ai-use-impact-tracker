---
title: Methodology
---

# Methodology

## Source

Data comes from the **Global Mind Project (GMP)** — Sapien Labs' ongoing global survey of cognitive and mental health. The tracker reads a monthly extract: Phase 1 as a local CSV, Phase 2 directly from GMP's Elasticsearch cluster. Refresh cadence is monthly (weekly capable).

## Exposure: ai_freq

A 7-level ordinal question. Mapped to integers 0–6 as follows:

| Integer | Label       | Raw response |
|---------|-------------|--------------|
| 0 | Never       | "I have never used an AI assistant" |
| 1 | Rarely      | "Rarely" |
| 2 | Monthly     | "A few times a month" |
| 3 | Weekly      | "Several days a week" |
| 4 | Daily       | "Several times a day" |
| 5 | Constantly  | "Constantly" |
| 6 | Always      | "All of the time" |

## Outcome: ai_impact_work

A **multi-select** question. Each respondent may choose any combination of atomic options. The tracker splits on `|` and produces seven binary flags:

- `impact_improved_quality` &nbsp; *(positive)*
- `impact_new_opportunities` &nbsp; *(positive)*
- `impact_adaptation_pressure` &nbsp; *(negative)*
- `impact_job_anxiety` &nbsp; *(negative)*
- `impact_none`, `impact_other`, `impact_not_sure`

### Net Impact Index

$$
\text{Net Impact Index} = \text{positive-impact share} - \text{negative-impact share}
$$

Range: [−1, +1]. Computed over AI users with at least one non-null impact response.

## Stratification

Respondents are bucketed into eight stratum levels: global, country, gender, age band, and all pairwise/three-way combinations. Age integers 18–20 are rolled into a "18-20" band to align with GMP's higher-age ordinal encoding.

## Suppression

Any stratum-month cell with fewer than **50 respondents** is suppressed. Confidence intervals for share metrics use the 95% Wilson score interval; CIs for `freq_mean` use a standard-error 95% interval.

## Phase 1 limitations

- No survey weights are applied. All metrics treat respondents as an equal-weighted sample.
- Associations between `ai_freq` and impact are **descriptive**. Self-selection bias is not adjusted; causal interpretation requires propensity weighting or covariate adjustment (Phase 2).
- Month-over-month changes may reflect respondent-mix composition rather than attitudinal shift. Compositional decomposition is planned for Phase 2.

## Data layout

The dashboard reads consolidated Parquet files produced by the ETL pipeline. Each file is one stratum level, covering all months. The authoritative spec is [`tracker/README.md`](https://github.com/).
