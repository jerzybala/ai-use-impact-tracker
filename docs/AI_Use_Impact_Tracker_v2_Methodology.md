**AI Use Impact Tracker**

**v2 — Weighted Impact Index**

Data Preparation, Computation Rules, and Implementation Status

**Date:** May 2026 | **Authors:** Tara Thiagarajan, Jerzy Bala |
**Status: Live on Railway**

1\. Overview

The AI Use Impact Tracker measures how AI use frequency relates to
self-reported work impact across countries, gender, and age groups. It
is built on survey data from the Global Mind Project (GMP) by Sapien
Labs.

The v2 dashboard introduces the **Weighted Impact Index (WII)** as the
primary outcome metric, replacing the simpler Net Impact Index (NII)
from v1. The WII assigns severity weights to each impact flag,
recognizing that job loss (−1.0) is more consequential than mild quality
improvement (+0.5).

2\. Data Source

**Source:** Global Mind Project (GMP), Sapien Labs. Monthly CSV extract
of survey responses.

**Current dataset:** 266,589 rows (filtered to respondents with
AI-related data) covering June 2025 – April 2026.

**Data cleaning:** Standard GMP cleaning criteria applied. Rows without
ai\_freq data are excluded. Pre-2025 months with near-zero adoption
rates (\< 5%) are dropped as they predate the AI questions.

**Note:** *Per Tara’s spec, the final version should use only Google
Display and Meta traffic data, excluding Google Search and
down-weighting organic traffic to 10%. This filtering is not yet
implemented.*

3\. Key Variables

3.1 Exposure: ai\_freq

A 7-level ordinal scale measuring how often a respondent uses AI
assistants:

  - 0 = Never

  - 1 = Rarely

  - 2 = Monthly (a few times a month)

  - 3 = Weekly (several days a week)

  - 4 = Daily (several times a day)

  - 5 = Constantly

  - 6 = Always (all of the time)

3.2 Outcome: ai\_impact\_work

A multi-select, pipe-delimited field. Each respondent can select
multiple impacts. The field is parsed into nine binary flags, each
carrying a signed severity weight:

|                                                      |            |              |
| ---------------------------------------------------- | ---------- | ------------ |
| **Impact Flag (ai\_impact\_work)**                   | **Weight** | **Category** |
| Created new job or income opportunities              | **+1.00**  | Positive     |
| Improved my work quality or output                   | **+0.50**  | Positive     |
| No impact                                            | **0.00**   | Neutral      |
| Not sure                                             | **0.00**   | Neutral      |
| Another impact not listed here                       | **0.00**   | Neutral      |
| Made me worry about the future of my job or industry | **−0.25**  | Negative     |
| Increased pressure to adapt or work faster           | **−0.50**  | Negative     |
| Reduced my income or made it harder to find work     | **−0.75**  | Negative     |
| Caused me to lose my job                             | **−1.00**  | Negative     |

4\. Weighted Impact Index (WII)

4.1 Per-Respondent Score

For each respondent in the impact denominator, the per-respondent score
is the dot product of their binary flag vector against the weight
vector:

**sᵢ = ∑ wₑ ⋅ 𝟙\[ flagₑ,ᵢ \]**

*f ∈ ℱ*

where wₑ is the weight for flag f from the IMPACT\_WEIGHTS table,
𝟙\[flagₑ,ᵢ\] is the indicator function (1 if respondent i selected
flag f, 0 otherwise), and ℱ is the set of eight weighted impact flags.

**Example — per-respondent scores:**

|                |                                       |                           |
| -------------- | ------------------------------------- | ------------------------- |
| **Respondent** | **Flags selected**                    | **Score**                 |
| Respondent A   | Improved quality, Adaptation pressure | (+0.50) + (−0.50) = 0.00  |
| Respondent B   | New job opportunities                 | **+1.00**                 |
| Respondent C   | Job loss                              | **−1.00**                 |
| Respondent D   | Improved quality, New opportunities   | (+0.50) + (+1.00) = +1.50 |
| Respondent E   | Job anxiety, Reduced income           | (−0.25) + (−0.75) = −1.00 |

4.2 Stratum-Level Index

The WII for a stratum (e.g., a country-month) is the arithmetic mean of
per-respondent scores across the impact denominator:

**WII = (1 / Nᵈ) ⋅ ∑ sᵢ**

*i ∈ 𝒟*

**Example:** Using the five respondents above:

**WII = (0.00 + 1.00 + (−1.00) + 1.50 + (−1.00)) / 5 = +0.10**

In practice, with tens of thousands of respondents per month, global WII
values land around +0.14 to +0.18 — net positive, meaning the weighted
benefit of AI on work slightly outweighs the weighted harm.

4.3 Impact Denominator

The denominator includes only respondents who: (a) use AI at any
frequency (ai\_freq \>= 1), and (b) have at least one non-null impact
response. Respondents who selected only N/A or left the field blank are
excluded.

4.4 Confidence Intervals

Two different confidence interval methods are used depending on the
metric type:

**Wald confidence interval (WII).** The Weighted Impact Index is a mean
of continuous per-respondent scores (ranging roughly from −1 to +1.5).
Its 95% CI is computed via the standard error of the mean (SEM):

**CI = WII ± 1.96 × σₛ / √Nᵈ**

*σₛ = std dev of per-respondent scores*

where SD is the standard deviation of the per-respondent scores and N is
the impact denominator size. The constant 1.96 is the z-score from the
standard normal distribution corresponding to 95% confidence (2.5% in
each tail). This is justified by the Central Limit Theorem: with tens of
thousands of respondents per month, the sampling distribution of the
mean is approximately normal regardless of the underlying score
distribution.

**Example:** For March 2026 with WII = +0.147 and \~25,000 respondents:

**CI = 0.147 ± 1.96 × σₛ / √25,000 = \[0.140, 0.153\]**

The interval is tight (±0.007) because N is large. The entire interval
is above zero, meaning the positive weighted impact is statistically
significant.

**Wilson score interval (share metrics).** Share-based metrics —
adoption rate, individual impact flag shares, positive/negative impact
shares — are proportions bounded between 0 and 1. For these, we use the
Wilson score 95% confidence interval, which performs better than the
Wald interval when proportions are near 0 or 1 or when sample sizes are
smaller. This is the same method used in the v1 dashboard.

**Why two methods?** The WII is a continuous mean, not a proportion, so
the Wald/SEM approach is appropriate. The share metrics are bounded
proportions where Wilson score intervals provide better coverage,
especially at the extremes. Both use the 95% confidence level (z =
1.96).

4.5 Asymmetry by Design

The weight scheme is deliberately asymmetric: the most severe negative
outcome (job loss, −1.0) carries the same absolute weight as the
strongest positive (new opportunities, +1.0), but the cumulative
negative weight across all four negative flags (−2.5) exceeds the
cumulative positive weight (+1.5). This reflects the stakeholder
judgment that **severe harms deserve disproportionate weight** compared
to moderate benefits.

4.6 Comparison with v1 Net Impact Index

The v1 NII is a simpler binary measure: NII = positive\_share −
negative\_share. A respondent counts as positive if they selected any
positive flag and negative if they selected any negative flag. NII
treats all impacts equally; WII differentiates by severity.

In practice, global WII values (\~0.14–0.18) run lower than NII values
(\~0.20–0.26) because the negative weights are heavier.

4.7 Rolling-Window Pooling

When the dashboard is set to a rolling window (e.g., "Last 3 months"),
it computes a weighted average of the pre-computed monthly metrics,
using each month’s respondent count as the weight:

**WII\_pooled = ∑ (Nₘ ⋅ WIIₘ) / ∑ Nₘ**

*m = 1 … w (months in window)*

**Example — Last 3 months pooled WII:**

|            |                   |            |             |
| ---------- | ----------------- | ---------- | ----------- |
| **Month**  | **N respondents** | **WII**    | **N × WII** |
| Feb 2026   | 20,000            | \+0.161    | 3,220       |
| Mar 2026   | 25,000            | \+0.147    | 3,675       |
| Apr 2026   | 15,000            | \+0.141    | 2,115       |
| **Pooled** | **60,000**        | **+0.150** | **9,010**   |

**WII\_pooled = 9,010 / 60,000 = +0.150**

March contributes more because it has the most respondents (25K). This
is more accurate than a simple average of the three monthly values,
which would treat all months equally regardless of sample size.

***Approximation note:** The impact metrics (WII, positive/negative
shares) technically have a different denominator — the impact
denominator (AI users who answered the impact question), not total N. We
use total N as a proxy because the two track closely within a short
window, keeping the approximation within \~1 percentage point of exact.*

5\. Suppression Rule

Strata with fewer than **N = 50** respondents are suppressed. This
prevents noisy estimates from small cells.

6\. Stratification

Metrics are computed at eight stratum levels:

  - Global (all respondents in a month)

  - Country

  - Gender

  - Age band (9 bands: 18–20 through 85+)

  - Country × Gender

  - Country × Age band

  - Gender × Age band

  - Country × Gender × Age band

7\. v2 Dashboard Features

7.1 Overview Tab

  - Hero KPI card: Weighted Impact Index with 95% CI

  - Supporting KPIs: respondent count, adoption rate, impact denominator

  - WII time-series (monthly, global) with selection indicator

  - Adoption rate bar chart (monthly, global)

  - Impact composition chart with flag weights annotated + survey
    wording toggle

  - WII by gender and age band (horizontal bar charts)

7.2 Countries Tab

  - Top 12 countries ranked by WII

  - Adoption rate × WII scatter plot with min-N slider (50–500)

  - Full country-month table, sortable by any column

7.3 Frequency & Impact Tab

  - Dose-response: NII by AI frequency level (global, by gender, by age)

  - Frequency distribution stacked bar chart over time

7.4 Interactive Controls

  - Month selector with prev/next navigation

  - Rolling-window options: Last 3 months, Last 6 months (pooled)

  - Min-N slider on scatter chart

  - Short labels / survey wording toggle on composition chart

8\. Technical Architecture

8.1 Pipeline

  - CSV ingest → normalization (normalize.py) → metric aggregation
    (metrics.py) → Parquet output → HTML dashboard bake

  - Pure-function pipeline: normalization and metric layers have no I/O
    side effects

  - ETL runs in \~17 seconds on 266K rows across 8 stratum levels

8.2 Deployment

  - Flask web app on Railway with Docker (python:3.12-slim)

  - GitHub auto-deploy on push to main

  - CSV upload triggers threaded ETL + dual dashboard bake (v1 and v2)

  - Routes: /dashboard-v1/\<id\>, /dashboard-v2/\<id\>, /latest-v1,
    /latest-v2

  - Static HTML works offline from file:// (Observable Plot + d3 from
    CDN)

9\. Implementation Status

|                                                       |                 |
| ----------------------------------------------------- | --------------- |
| **Feature**                                           | **Status**      |
| Weighted Impact Index (per-flag weights)              | **Implemented** |
| KPI dashboard with hero WII card + 95% CI             | **Implemented** |
| WII time-series (monthly, global)                     | **Implemented** |
| WII breakdowns by gender, age, country                | **Implemented** |
| Impact composition chart with weight annotations      | **Implemented** |
| Country ranking by WII (top 12 bar chart)             | **Implemented** |
| Adoption x WII scatter plot with min-N slider         | **Implemented** |
| Sortable country table with WII column                | **Implemented** |
| Dose-response (NII by frequency level)                | **Implemented** |
| Rolling-window views (3-month, 6-month pooling)       | **Implemented** |
| Separate v1/v2 dashboard routes on Railway            | **Implemented** |
| Demographic-weighted averaging (UN age distributions) | **Planned**     |
| Quarterly aggregation                                 | **Planned**     |
| Regional groupings and averages                       | **Planned**     |
| Map views (choropleth)                                | **Planned**     |
| Data source filtering (Google Display, Meta only)     | **Planned**     |

10\. Limitations

10.1 No Survey Weights (Non-Probability Sample)

The GMP respondent pool is a convenience sample recruited via online ads
(Google Display, Meta, and organic search). It is not a probability
sample and carries no post-stratification or design weights.
Consequently:

  - Demographic proportions in the data do not match national population
    proportions. Countries, age groups, and genders are represented
    according to who encounters and completes the survey, not according
    to census benchmarks.

  - All metrics — WII, adoption rate, impact shares — are descriptive
    statistics of the responding population, not population-level
    estimates. We cannot claim, for example, that 42% of adults in a
    country use AI; we can only say that 42% of GMP respondents in that
    country reported using AI.

  - Associations between AI frequency and impact outcomes are
    correlational. Higher-frequency AI users who report better outcomes
    may differ systematically from lower-frequency users in education,
    occupation, digital literacy, or other unmeasured confounders. No
    causal claims are supported.

**Planned mitigation:** *Demographic-weighted averaging using UN World
Population Prospects age–sex distributions is on the roadmap. This would
rebalance age and gender composition within each country to approximate
national demographics, reducing one source of composition bias. It would
not, however, address self-selection into the survey or unmeasured
confounders.*

10.2 Composition Effects in Time-Series

Month-over-month changes in WII or other metrics may reflect shifts in
who is responding rather than genuine attitudinal change. For example:

  - If a recruitment campaign increases responses from a younger
    demographic in one month, and younger respondents tend to report
    more positive AI impacts, the global WII will rise — even if no
    individual changed their view.

  - Country mix changes: if a high-WII country (e.g., one with strong AI
    adoption) is over-represented in one month relative to another, the
    global metric shifts accordingly.

  - Seasonal patterns in survey completion (e.g., lower response rates
    during holidays) can alter the demographic mix.

The stratified breakdowns (by country, gender, age) partially mitigate
this by holding one dimension constant, but cross-dimensional
composition effects remain. The rolling-window views help smooth
short-term fluctuations.

10.3 Weight Selection

The nine impact weights (+1.0, +0.5, 0, −0.25, −0.50, −0.75, −1.0) were
chosen by stakeholder judgment, not derived from empirical data.
Different weight schemes would produce different index values and could
alter relative country rankings. Sensitivity analysis (varying weights
within a plausible range) has not yet been conducted. The asymmetric
design — total negative weight (−2.5) exceeding total positive weight
(+1.5) — is intentional but should be disclosed when comparing WII
values across studies.

10.4 Rolling-Window Approximation

Rolling-window pooling (3-month, 6-month) computes a weighted average of
pre-aggregated monthly metrics using each month’s total respondent count
as the weight. The exact calculation would re-aggregate from
individual-level data within the pooled window. The approximation
introduces minor error (±1 percentage point within 3–6 month windows)
because the impact denominator differs slightly from total N. This
trade-off is accepted for client-side performance: the dashboard runs
entirely in the browser and cannot re-query raw data.

10.5 Dose-Response Uses NII, Not WII

The Frequency & Impact tab shows dose-response curves (impact by AI
frequency level) using the simpler Net Impact Index, not the Weighted
Impact Index. This is because the current ETL computes NII stratified by
frequency level but does not yet compute WII per frequency level. Adding
weighted dose-response is a planned enhancement.

10.6 Data Source Filtering Not Yet Implemented

Per Tara’s specification, the production version should restrict the
respondent pool to Google Display and Meta traffic sources and
down-weight organic/search traffic to 10%. This filtering is not yet
implemented in the ETL pipeline. The current dashboard processes *all*
traffic sources equally, which may include respondents with different
characteristics (e.g., Google Search respondents may have higher digital
literacy). Once implemented, historical metrics may shift as the
composition of the respondent pool changes.

10.7 Multi-Select Interaction Effects

Respondents can select multiple impact flags simultaneously. The WII
treats each flag independently — a respondent selecting both “improved
quality” (+0.5) and “job anxiety” (−0.25) receives the sum (+0.25). This
additive model does not capture potential interactions: for instance,
the experience of simultaneous benefit and anxiety may not be
well-described by simply adding the weights. More complex models (e.g.,
interaction terms, latent factor analysis) could address this but are
beyond the current scope.

10.8 Suppression and Small-Cell Noise

Strata with fewer than 50 respondents are suppressed entirely. This
threshold is a pragmatic choice; it prevents the noisiest estimates from
appearing but does not guarantee statistical reliability. For strata
just above the threshold (e.g., N = 55), confidence intervals are wide
and point estimates can shift substantially with small data changes.
Users should exercise caution when interpreting metrics from low-N
strata, even when displayed.

10.9 Confidence Intervals Assume Simple Random Sampling

All confidence intervals — both Wald (for WII and frequency mean) and
Wilson score (for share metrics) — assume simple random sampling. The
GMP respondent pool is a convenience sample, so these CIs may understate
the true uncertainty. They will be revised once survey weights are
introduced.

11\. Access

**Web app:** https://ai-use-impact-tracker-demo.up.railway.app/

**v1 dashboard:** /latest-v1 (Net Impact Index)

**v2 dashboard:** /latest-v2 (Weighted Impact Index)

**GitHub:** https://github.com/jerzybala/ai-use-impact-tracker
