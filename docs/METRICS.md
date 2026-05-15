# How the Metrics Are Computed

This is a detailed walk-through of every metric the AI Impact Tracker
publishes, including the exact formulas, denominators, suppression
rules, and how the dashboard's Period filter pools months together.

It is a companion to [`COLUMNS.md`](COLUMNS.md) (which documents the
source-side survey columns) and [`TRACKER.md`](TRACKER.md) (the
spec/contract for the metric layer). All formulas here match the
implementation in `tracker/src/pipeline/metrics.py` and
`tracker/src/pipeline/normalize.py`.

---

## Contents

- [1. Building blocks](#1-building-blocks)
- [2. Core indicators](#2-core-indicators)
- [3. The impact denominator](#3-the-impact-denominator)
- [4. Impact share metrics](#4-impact-share-metrics)
- [5. Positive / negative / net impact](#5-positive--negative--net-impact)
- [6. Weighted Impact Index](#6-weighted-impact-index)
- [7. Dose-response](#7-dose-response)
- [8. Confidence intervals](#8-confidence-intervals)
- [9. Minimum-N suppression](#9-minimum-n-suppression)
- [10. Stratification (country × gender × age)](#10-stratification-country--gender--age)
- [11. Rolling-window pooling (Period filter)](#11-rolling-window-pooling-period-filter)
- [12. Summary card (dashboard)](#12-summary-card-dashboard)
- [13. Known limitations](#13-known-limitations)

---

## 1. Building blocks

Every metric is computed from one row per **respondent per month**.
Three derived fields drive almost everything else:

### `ai_freq_int` — AI-use frequency on a 0–6 ordinal scale

Mapped from the raw `ai_freq` text answer:

| Integer | Label | Raw text mapped |
|---:|---|---|
| 0 | Never | "I have never used an AI assistant" |
| 1 | Rarely | "Rarely" |
| 2 | Monthly | "A few times a month" |
| 3 | Weekly | "Several days a week" |
| 4 | Daily | "Several times a day" |
| 5 | Constantly | "Constantly", "Constamment", "Constantly (when awake)" |
| 6 | Always | "All of the time" |
| — | null | "N/A" or anything not recognised |

### `is_user` — does this respondent use AI at all?

```
is_user = (ai_freq_int >= 1)
```

A respondent at level 0 ("Never") is **not** an AI user.

### Impact flags — one-hot from `ai_impact_work`

The pipe-delimited `ai_impact_work` answer is split into nine boolean
columns; each respondent can have multiple flags set true.

| Flag | Triggered by answer |
|---|---|
| `impact_improved_quality` | "Improved my work quality or output" |
| `impact_new_opportunities` | "Created new job or income opportunities" |
| `impact_adaptation_pressure` | "Increased pressure to adapt or work faster" |
| `impact_job_anxiety` | "Made me worry about the future of my job or industry" |
| `impact_job_loss` | "Caused me to lose my job" |
| `impact_reduced_income` | "Reduced my income or made it harder to find work" |
| `impact_none` | "No impact" |
| `impact_other` | "Another impact not listed here" (plus any unknown raw option) |
| `impact_not_sure` | "Not sure" |
| `impact_na` | Raw value was null / "N/A" / blank |

Two derived boolean columns roll the flags into a positive / negative
direction:

```
is_positive = impact_improved_quality OR impact_new_opportunities
is_negative = impact_adaptation_pressure
            OR impact_job_anxiety
            OR impact_job_loss
            OR impact_reduced_income
```

`impact_none`, `impact_other`, `impact_not_sure`, and `impact_na` are
treated as neither positive nor negative.

---

## 2. Core indicators

These are reported for **every stratum × month**.

### `n_respondents`

Plain count of respondents in the cell.

```
n_respondents = COUNT(rows in stratum × month)
```

This is also the denominator for `adoption_rate` and `freq_mean`.

### `adoption_rate` — share who use AI at all

```
adoption_rate = COUNT(is_user = true) / n_respondents
```

Range `[0, 1]`. Includes respondents at every `ai_freq` level from
"Rarely" upward.

### `freq_mean` — mean AI-use frequency on the 0–6 scale

```
freq_mean = MEAN(ai_freq_int)
```

over the rows in the cell that have a non-null `ai_freq_int`. Range
`[0, 6]`. A `freq_mean` of `2.08` means roughly "monthly use" on
average; `4.0` means "daily" on average.

> Note: `freq_mean` is computed and stored, but no longer surfaced as a
> selectable map metric on the redesigned dashboard.

### `freq_share_0` … `freq_share_6` — distribution

For each ordinal level `k = 0…6`:

```
freq_share_k = COUNT(ai_freq_int = k) / COUNT(ai_freq_int is not null)
```

The seven shares sum to `1`.

---

## 3. The impact denominator

The impact metrics in §4–§6 do **not** use `n_respondents` as their
denominator. They use a stricter base population, the
**impact denominator**:

```
in_impact_denom = is_user AND has_impact_response
```

where `has_impact_response` means at least one of the eight real
impact flags is true (all flags except `impact_na`):

```
has_impact_response = impact_improved_quality
                   OR impact_new_opportunities
                   OR impact_adaptation_pressure
                   OR impact_job_anxiety
                   OR impact_job_loss
                   OR impact_reduced_income
                   OR impact_none
                   OR impact_other
                   OR impact_not_sure
```

So the impact denominator is reported as `n_impact_denominator` and
equals the count of respondents who:

1. use AI at all (`ai_freq_int >= 1`), **and**
2. answered the impact question (gave at least one option, including
   "No impact" or "Not sure").

Respondents who never use AI, or whose impact answer was blank/N/A,
are excluded.

The dashboard tooltip describes this base as "AI users with impact
response".

---

## 4. Impact share metrics

For each impact flag listed in §1, the share is computed against the
impact denominator:

```
impact_share_{flag} = COUNT(flag = true AND in_impact_denom)
                    / n_impact_denominator
```

The metrics published are:

| Metric | Numerator flag |
|---|---|
| `impact_share_improved_quality` | `impact_improved_quality` |
| `impact_share_new_opportunities` | `impact_new_opportunities` |
| `impact_share_adaptation_pressure` | `impact_adaptation_pressure` |
| `impact_share_job_anxiety` | `impact_job_anxiety` |
| `impact_share_job_loss` | `impact_job_loss` |
| `impact_share_reduced_income` | `impact_reduced_income` |
| `impact_share_none` | `impact_none` |
| `impact_share_other` | `impact_other` |
| `impact_share_not_sure` | `impact_not_sure` |

Each is a value in `[0, 1]`.

**The shares do not have to sum to 1.** Respondents can select more
than one impact, so a given respondent can contribute to multiple
shares. A respondent who picked "Improved my work quality" *and*
"Created new opportunities" counts toward both
`impact_share_improved_quality` and `impact_share_new_opportunities`.

---

## 5. Positive / negative / net impact

Two rolled-up shares are computed on the same impact denominator:

```
positive_impact_share = COUNT(is_positive AND in_impact_denom)
                      / n_impact_denominator

negative_impact_share = COUNT(is_negative AND in_impact_denom)
                      / n_impact_denominator
```

`is_positive` and `is_negative` are defined in §1.

The **Net Impact Index** is the difference:

```
net_impact_index = positive_impact_share − negative_impact_share
```

Range `[−1, +1]`:

- `+1` means every respondent in the cell picked **only** positive
  impacts and **no** negative ones.
- `−1` means every respondent picked **only** negative impacts.
- `0` means equal positive and negative shares (this can happen by
  cancellation *or* because everyone answered "No impact" / "Not sure").

A respondent who picks one positive *and* one negative contributes
`+1` to both shares, so the net for that respondent's contribution is
`0`. The index is a population-level summary, not a per-respondent
score.

> Note: `net_impact_index` is computed and stored, but no longer
> surfaced as a selectable map metric on the redesigned dashboard. It
> still drives the dose-response panel (§7).

---

## 6. Weighted Impact Index

Tara's **Weighted Impact Index** (`weighted_impact_index`) is the
dashboard's headline metric. Unlike the simple net index in §5, it
assigns each impact flag a signed weight reflecting how positive or
negative that outcome is, then averages a per-respondent score across
the impact denominator.

### Weights

| Flag | Weight |
|---|---:|
| `impact_new_opportunities` | **+1.00** |
| `impact_improved_quality` | **+0.50** |
| `impact_job_anxiety` | **−0.25** |
| `impact_adaptation_pressure` | **−0.50** |
| `impact_reduced_income` | **−0.75** |
| `impact_job_loss` | **−1.00** |
| `impact_none`, `impact_other`, `impact_not_sure` | 0 |

These are editorial values set by the Sapien Labs team; they reflect
judgment about relative severity, not an empirical calibration.

### Per-respondent score

For each respondent in the impact denominator, sum the weights of
every flag they selected:

```
score(respondent) = Σ over flags f { IMPACT_WEIGHTS[f]  if flag f is true }
```

Examples:

- A respondent who selected only "Improved my work quality" scores
  `+0.5`.
- A respondent who selected "Improved my work quality" *and*
  "Adaptation pressure" scores `+0.5 + (−0.5) = 0`.
- A respondent who selected "Job loss" *and* "Reduced income" scores
  `−1.0 + (−0.75) = −1.75`.
- A respondent who selected "No impact" scores `0`.

A single respondent's score can exceed `±1` if they selected several
weighted flags in the same direction.

### Cell value

The published `weighted_impact_index` is the simple mean of these
per-respondent scores over the impact denominator:

```
weighted_impact_index = MEAN over impact denominator of score(respondent)
```

Range is roughly `[−1, +1]` in practice but is **not symmetric**: a
respondent would need to select multiple negative flags simultaneously
to drive a cell well below `−1`.

A positive cell value means the average AI user in that stratum had a
net-positive experience; a negative value means the average user had
a net-negative experience.

---

## 7. Dose-response

The dashboard's "Dose-response" row shows the **Net Impact Index by
AI-use frequency level**. For each stratum × month, and for each
ordinal `ai_freq` level `k = 1…6`:

```
dose_response[k] = MEAN(is_positive | ai_freq_int = k)
                 − MEAN(is_negative | ai_freq_int = k)
```

The denominator is respondents in the impact denominator (§3) at that
specific frequency level. If that level has fewer than `MIN_N`
respondents (§9), the entry is `null` (rendered as `n/a` in the
dashboard).

Level 0 ("Never") is not part of the impact denominator and is not
reported.

Interpretation: a dose-response that climbs from `+0.10` at "Rarely"
to `+0.40` at "Daily" suggests the net impact is more positive among
heavier users — a hint of dose-dependence, not a causal claim.

---

## 8. Confidence intervals

### Share metrics — Wilson 95% score interval

All share metrics (`adoption_rate`, every `impact_share_*`,
`positive_impact_share`, `negative_impact_share`) get a Wilson score
95% CI. Given `k` successes out of `n` trials and `z = 1.96`:

```
p      = k / n
denom  = 1 + z² / n
center = (p + z² / (2n)) / denom
half   = z · √( (p·(1−p) + z² / (4n)) / n ) / denom
ci_low  = clip(center − half, 0, 1)
ci_high = clip(center + half, 0, 1)
```

Wilson is preferred over the normal-approximation Wald interval
because it stays inside `[0, 1]` even at extreme `p` and small `n`.

### `freq_mean` — standard-error 95% CI

```
sem = stdev(ai_freq_int) / √n   (with ddof = 1)
ci  = freq_mean ± 1.96 · sem
```

### `weighted_impact_index` — standard-error 95% CI

The per-respondent score (§6) is treated as a continuous variable:

```
sem = stdev(score) / √n_impact_denominator   (with ddof = 1)
ci  = weighted_impact_index ± 1.96 · sem
```

All CIs assume simple random sampling — they will be revised once
survey weights are introduced.

---

## 9. Minimum-N suppression

Any stratum × month cell with fewer than **`MIN_N` (default 50)**
respondents is flagged `suppressed = true` and its metric values are
written as `null`. The dashboard does not display suppressed cells.

The threshold applies at the **finest** stratum level. So if a
country × gender × age cell has 41 respondents, that cell is
suppressed, even if the corresponding country × gender (without age)
cell has 600.

`MIN_N` is configurable per run via the `--min-n` flag to `main.py` /
`tracker/main.py`. The active value is stored in `_meta.json` and
embedded in the rendered HTML as the suppression threshold shown in
the dashboard subtitle.

The dashboard also applies a separate UI threshold: the Gender and
Age band dropdowns only list categories that have at least one
non-suppressed cell in `country_gender` / `country_age_band` — so
options with no usable data anywhere are hidden.

---

## 10. Stratification (country × gender × age)

Every metric is computed independently for each of these eight
stratum levels:

| Level | Group-by columns (in addition to year, month) |
|---|---|
| `global` | — |
| `country` | `country_clean` |
| `gender` | `gender_clean` |
| `age_band` | `age_band` |
| `country_gender` | `country_clean`, `gender_clean` |
| `country_age_band` | `country_clean`, `age_band` |
| `gender_age_band` | `gender_clean`, `age_band` |
| `country_gender_age_band` | `country_clean`, `gender_clean`, `age_band` |

The dashboard picks the finest level needed for the current filter
combination so every displayed number is a **precomputed cell value**,
not a JS-side aggregation:

| Filters | Level used |
|---|---|
| no demographic filter | `country` |
| gender only | `country_gender` |
| age only | `country_age_band` |
| gender + age | `country_gender_age_band` |

This is also why removing a demographic filter doesn't just average
the cells back together — the dashboard re-loads the coarser stratum.

---

## 11. Rolling-window pooling (Period filter)

The dashboard's **Period** selector — Single month / Last 3 / Last 6 /
Last 12 — pools the precomputed monthly cells into a rolling window.
Pooling is done in the browser on the embedded JSON and does not
change the published Parquet output.

For each (country × gender × age) cell across the window of months,
fields are pooled with the following rules:

| Field | Aggregation | Weight |
|---|---|---|
| `n_respondents`, `n_impact_denominator` | sum | — |
| `adoption_rate`, `freq_mean` | weighted mean | `n_respondents` |
| `weighted_impact_index`, `net_impact_index`, all `impact_share_*`, `positive_impact_share`, `negative_impact_share` | weighted mean | `n_impact_denominator` |
| `dose_response[k]` (for k = 1…6) | weighted mean | `n_impact_denominator` |

**This is approximate.** The exact pooled value would require
re-running the metric layer on the pooled respondent-level data. The
dashboard's weighted-mean of monthly aggregates is correct in
expectation but ignores within-month variance and does not produce
new confidence intervals.

Cells suppressed in a given month (originally below `MIN_N`) are
dropped before pooling, so a country can appear in the rolling window
even if some of its constituent months were individually suppressed.

---

## 12. Summary card (dashboard)

The top-right summary card on the dashboard is a fixed reference and
is **not** affected by Month, Period, Country, Gender, or Age filters.

It always shows:

1. The global weighted average of the currently-selected metric over
   the trailing 3 **full** months.
2. The total respondents over those 3 months.
3. The total respondents across the entire dataset to date.

"Full" means non-partial. The dashboard detects the latest partial
month by comparing each month's total respondents against the median
of prior months — any month with respondents below `60% × median` is
considered still in-flight and excluded from the trailing-3 window.
This is the same rule used to mark the partial point in the trend
chart.

Only the **metric** dropdown updates this card; switching metric
swaps the displayed label and value but does not change the underlying
3-month window.

---

## 13. Known limitations

These are explicit Phase-1 scope boundaries — they apply to every
metric above.

- **No survey weights** are applied. All respondents are treated as an
  equal-weighted sample. The published values reflect the raw
  respondent mix in each cell, not a population-representative
  estimate.
- **Self-selection bias is not adjusted.** Associations between
  `ai_freq` and impact (including dose-response) are descriptive, not
  causal.
- **Composition effects are not decomposed.** Month-over-month
  changes can reflect a change in respondent mix rather than a
  genuine attitude shift.
- **CIs assume simple random sampling.** They will be revised once
  weighting is introduced.
- **`IMPACT_WEIGHTS` (§6) are editorial.** They encode Sapien Labs'
  judgment about relative severity of each outcome, not an empirical
  calibration. Changing the weights will shift every published
  `weighted_impact_index` value.

Phase 2 will add survey weighting and compositional adjustment.
