**AI Use Impact Tracker**

*Technical Reference & Metric Computation Guide*

**Sapien Labs | May 2026**

This technical reference details every metric the AI Use Impact Tracker
publishes, including formulas, denominators, suppression rules,
confidence-interval methods, stratification logic, and how the
dashboard’s Period filter pools months.

**1. Core Analytical Building Blocks**

All metrics are calculated from one row per respondent per month. Three
primary derived fields drive almost everything else.

**1.1 AI-Use Frequency Scale**

Mapped from the raw ai\_freq text answer to a 0–6 ordinal scale:

| **Integer** | **Label**  | **Raw text mapped**                                    |
| ----------- | ---------- | ------------------------------------------------------ |
| 0           | Never      | “I have never used an AI assistant”                    |
| 1           | Rarely     | “Rarely”                                               |
| 2           | Monthly    | “A few times a month”                                  |
| 3           | Weekly     | “Several days a week”                                  |
| 4           | Daily      | “Several times a day”                                  |
| 5           | Constantly | “Constantly”, “Constamment”, “Constantly (when awake)” |
| 6           | Always     | “All of the time”                                      |
| —           | null       | “N/A” or anything not recognised                       |

**1.2 User Status**

A boolean identifying whether the respondent uses AI at all:

\[\text{is}_{\text{user}}\mathbb{\  = \ 1}\left\lbrack {ai\_ freq}_{\text{int}}\  \geq \ 1 \right\rbrack\]

A respondent at level 0 (“Never”) is not an AI user.

**1.3 Impact Flags (from ai\_impact\_work)**

The pipe-delimited ai\_impact\_work answer is split into nine boolean
columns; each respondent can have multiple flags set true.

<table>
<thead>
<tr class="header">
<th><strong>Flag</strong></th>
<th><strong>Triggered by answer</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><ol type="1">
<li><p>“Improved my work quality or output”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="even">
<td><ol start="2" type="1">
<li><p>“Created new job or income opportunities”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="odd">
<td><ol start="3" type="1">
<li><p>“Increased pressure to adapt or work faster”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="even">
<td><ol start="4" type="1">
<li><p>“Made me worry about the future of my job or industry”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="odd">
<td><ol start="5" type="1">
<li><p>“Caused me to lose my job”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="even">
<td><ol start="6" type="1">
<li><p>“Reduced my income or made it harder to find work”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="odd">
<td><ol start="7" type="1">
<li><p>“No impact”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="even">
<td><ol start="8" type="1">
<li><p>“Another impact not listed here” (plus any unknown raw option)</p></li>
</ol></td>
<td></td>
</tr>
<tr class="odd">
<td><ol start="9" type="1">
<li><p>“Not sure”</p></li>
</ol></td>
<td></td>
</tr>
<tr class="even">
<td><ol start="10" type="1">
<li><p>Raw value was null / N/A / blank</p></li>
</ol></td>
<td></td>
</tr>
</tbody>
</table>

Two derived boolean columns roll the flags into directional vectors:

  - **Positive:** impact\_improved\_quality OR
    impact\_new\_opportunities

  - **Negative:** impact\_adaptation\_pressure OR impact\_job\_anxiety
    OR impact\_job\_loss OR impact\_reduced\_income

impact\_none, impact\_other, impact\_not\_sure, and impact\_na are
treated as neither positive nor negative.

**2. Core Population Indicators**

These base descriptive metrics are calculated independently for every
demographic stratum and month block.

**2.1 Total Respondent Count (N)**

The absolute headcount of all individuals who completed the survey
inside a designated stratum × month cell. This is also the denominator
for adoption\_rate.

\[N\  = \ |\{\ i\ :\ i\  \in \ stratum\  \times \ month\ \}|\]

**2.2 Adoption Rate**

The proportion of the surveyed population that actively employs AI
tools:

\[\text{adoption}_{\text{rate}}\  = \ \frac{1}{N}\sum_{i = 1}^{N}{\mathbb{1\lbrack}is\_ userᵢ\rbrack}\]

Range \[0, 1\]. Includes respondents at every ai\_freq level from
“Rarely” upward.

**2.3 Frequency Distribution (freq\_share₀ … freq\_share₆)**

For each ordinal level k = 0, …, 6:

\[{freq\_ share}_{k}\  = \ \frac{1}{N'}\sum_{}^{}{\mathbb{1\lbrack}ai\_ freq\_ intᵢ\  = \ k\rbrack}\]

The seven shares sum to 1.

**3. The Impact Denominator Framework**

To isolate real trends, workspace impact metrics do not use the full
population headcount (N) as their base. Instead, they rely on a stricter
verified sub-population called the Impact Denominator (Nᵈ).

\[in\_ impact\_ denomᵢ\  = \ {is\_ user}_{i}\  \land \ {has\_ impact\_ response}_{i}\]

where has\_impact\_response means at least one of the eight real impact
flags is true (all flags except impact\_na) — i.e. the disjunction over
impact\_improved\_quality, impact\_new\_opportunities,
impact\_adaptation\_pressure, impact\_job\_anxiety, impact\_job\_loss,
impact\_reduced\_income, impact\_none, impact\_other, and
impact\_not\_sure.

To be included in the impact denominator, a respondent must fulfill two
rules simultaneously:

1.  **Active Engagement:** They must be a confirmed AI user
    (ai\_freq\_int ≥ 1).

2.  **Valid Response:** They must have provided an explicit answer to
    the impact question, including choosing baseline answers like “No
    impact” or “Not sure.”

> *Methodological Purpose: Non-users are removed from impact
> calculations because a participant with zero regular interaction
> cannot report direct workspace shifts. This step ensures that the
> resulting percentages accurately reflect the experiences of the user
> base without downward dilution.*

**4. Impact Share Metrics**

For each impact flag listed in §1, the share is computed against the
impact denominator. Let Nᵈ denote n\_impact\_denominator:

\[{impact\_ share}_{f}\  = \ \frac{1}{Nᵈ}\sum_{}^{}{\mathbb{1\lbrack}flag(f,\ i)\rbrack}\]

| **Metric**                   | **Numerator flag** |
| ---------------------------- | ------------------ |
| impact\_improved\_quality    |                    |
| impact\_new\_opportunities   |                    |
| impact\_adaptation\_pressure |                    |
| impact\_job\_anxiety         |                    |
| impact\_job\_loss            |                    |
| impact\_reduced\_income      |                    |
| impact\_none                 |                    |
| impact\_other                |                    |
| impact\_not\_sure            |                    |

Each is a value in \[0, 1\].

**The shares do not have to sum to 1.** Respondents can select more than
one impact, so a given respondent can contribute to multiple shares.

**5. Positive / Negative / Net Impact**

Two rolled-up shares are computed on the same impact denominator:

\[{positive\_ impact}_{\text{share}}\  = \ \frac{1}{Nᵈ}\sum_{}^{}{\mathbb{1\lbrack}is\_ positiveᵢ\rbrack}\]

\[{negative\_ impact}_{\text{share}}\  = \ \frac{1}{Nᵈ}\sum_{}^{}{\mathbb{1\lbrack}is\_ negativeᵢ\rbrack}\]

These two shares serve as building blocks for the dose-response panel
(§7), which displays their difference (positive − negative) at each
AI-use frequency level.

**6. Weighted Impact Index (WII)**

The **Weighted Impact Index** (weighted\_impact\_index) is the
dashboard’s headline metric. Unlike the simple net index in §5, it
assigns each impact flag a signed weight reflecting how positive or
negative that outcome is, then averages a per-respondent score across
the impact denominator.

**6.1 Weight Table**

These are editorial values set by the Sapien Labs team; they reflect
judgment about relative severity, not an empirical calibration.

| **Workplace Impact Choice Flag**                     | **Assigned Severity Weight** |
| ---------------------------------------------------- | ---------------------------- |
| Created new job or income opportunities              | **+1.00**                    |
| Improved my work quality or output                   | **+0.50**                    |
| Made me worry about the future of my job or industry | **−0.25**                    |
| Increased pressure to adapt or work faster           | **−0.50**                    |
| Reduced my income or made it harder to find work     | **−0.75**                    |
| Caused me to lose my job                             | **−1.00**                    |
| No impact / Another impact / Not sure                | **0.00**                     |

**6.2 Per-Respondent Score**

For each respondent i in the impact denominator, sum the weights of
every flag they selected:

\[s_{i}\  = \ \sum_{f\mathcal{\  \in \ F}}^{}{wₑ\  \cdot \ \mathbb{1\lbrack}flag(f,\ i)\rbrack}\]

where wₑ = IMPACT\_WEIGHTS\[f\] and ℱ is the set of eight weighted flags
(excluding impact\_na).

**Examples:**

  - A respondent who selected only “Improved my work quality” scores
    +0.5.

  - A respondent who selected “Improved my work quality” and “Adaptation
    pressure” scores +0.5 + (−0.5) = 0.

  - A respondent who selected “Job loss” and “Reduced income” scores
    −1.0 + (−0.75) = −1.75.

  - A respondent who selected “No impact” scores 0.

A single respondent’s score can exceed ±1 if they selected several
weighted flags in the same direction.

**6.3 Cell Value**

The published weighted\_impact\_index is the arithmetic mean of
per-respondent scores over the impact denominator:

\[WII\  = \ \frac{1}{Nᵈ}\sum_{}^{}{sᵢ}\]

Range is roughly \[−1, +1\] in practice but is not symmetric: a
respondent would need to select multiple negative flags simultaneously
to drive a cell well below −1.

A positive cell value means the average AI user in that stratum had a
net-positive experience; a negative value means the average user had a
net-negative experience.

**6.4 Asymmetry by Design**

The weight scheme is deliberately asymmetric: the most severe negative
outcome (job loss, −1.0) carries the same absolute weight as the
strongest positive (new opportunities, +1.0), but the cumulative
negative weight across all four negative flags (−2.5) exceeds the
cumulative positive weight (+1.5). This reflects the stakeholder
judgment that severe harms deserve disproportionate weight compared to
moderate benefits.

**6.5 Comparison with the v1 Net Impact Index**

The v1 dashboard used a simpler binary measure (NII = positive\_share −
negative\_share) that treated all impacts equally. The WII replaced it
as the headline metric because it differentiates by severity. In
practice, global WII values (\~0.14–0.18) run lower than NII values
(\~0.20–0.26) because the negative weights are heavier. The NII is still
computed internally and drives the dose-response panel (§7).

**7. Dose-Response**

The dashboard’s “Dose-response” row shows the difference between
positive and negative impact shares (positive\_impact\_share −
negative\_impact\_share) at each AI-use frequency level. For each
stratum × month, and for each ordinal ai\_freq level k = 1, …, 6:

\[dose\_ response\left\lbrack k \right\rbrack\  = \ {pos\_ share}_{k}\  - \ {neg\_ share}_{k}\]

where the denominator is respondents in the impact denominator (§3) at
that specific frequency level. If that level has fewer than MIN\_N
respondents (§9), the entry is null (rendered as n/a in the dashboard).

Level 0 (“Never”) is not part of the impact denominator and is not
reported.

**Interpretation:** a dose-response that climbs from +0.10 at “Rarely”
to +0.40 at “Daily” suggests the net impact is more positive among
heavier users — a hint of dose-dependence, not a causal claim.

**8. Confidence Intervals**

**8.1 Share Metrics — Wilson 95% Score Interval**

All share metrics (adoption\_rate, every impact\_share\_\*,
positive\_impact\_share, negative\_impact\_share) get a Wilson score 95%
CI. Given k successes out of n trials and z = 1.96:

\[p\hat{}\  = \ \frac{k}{n}\]

\[p\tilde{}\  = \ \frac{p\hat{}\  + \ z²/2n}{1\  + \ z²/n}\]

\[CI\  = \ p\tilde{}\  \pm \ \frac{z\  \cdot \ \sqrt{}\lbrack\ p\hat{}(1 - p\hat{})/n\  + \ z²/4n²\ \rbrack}{1\  + \ z²/n}\]

\[\text{ci}_{\text{low}}\  = \ max(0,\ CIₗₒᵂ),\ \ \text{ci}_{\text{high}}\  = \ min(1,\ CIₕᵢₙₕ)\]

Wilson is preferred over the normal-approximation Wald interval because
it stays inside \[0, 1\] even at extreme proportions and small n.

**8.2 Weighted Impact Index — Wald 95% CI**

The per-respondent score sᵢ (§6) is treated as a continuous variable:

\[SE\  = \ \frac{\sigma ₛ}{\sqrt{}Nᵈ}\ \ \ \ (ddof\  = \ 1)\]

\[CI\  = \ WII\  \pm \ 1.96\  \times \ SE\]

where σₛ is the sample standard deviation of the per-respondent scores
and Nᵈ is the impact denominator size.

> *All CIs assume simple random sampling — they will be revised once
> survey weights are introduced.*

**9. Minimum-N Suppression**

Any stratum × month cell with fewer than **MIN\_N (default 50)**
respondents is flagged suppressed = true and its metric values are
written as null. The dashboard does not display suppressed cells.

The threshold applies at the finest stratum level. So if a country ×
gender × age cell has 41 respondents, that cell is suppressed, even if
the corresponding country × gender (without age) cell has 600.

MIN\_N is configurable per run via the --min-n flag to main.py. The
active value is stored in \_meta.json and embedded in the rendered HTML
as the suppression threshold shown in the dashboard subtitle.

The dashboard also applies a separate UI threshold: the Gender and Age
band dropdowns only list categories that have at least one
non-suppressed cell — so options with no usable data anywhere are
hidden.

**10. Stratification (Country × Gender × Age)**

Every metric is computed independently for each of these eight stratum
levels:

| **Level**                  | **Group-by columns (+ year, month)**     |
| -------------------------- | ---------------------------------------- |
| global                     | —                                        |
| country                    | country\_clean                           |
| gender                     | gender\_clean                            |
| age\_band                  | age\_band                                |
| country\_gender            | country\_clean, gender\_clean            |
| country\_age\_band         | country\_clean, age\_band                |
| gender\_age\_band          | gender\_clean, age\_band                 |
| country\_gender\_age\_band | country\_clean, gender\_clean, age\_band |

The dashboard picks the finest level needed for the current filter
combination so every displayed number is a precomputed cell value, not a
JS-side aggregation:

| **Filters**           | **Level used**             |
| --------------------- | -------------------------- |
| no demographic filter | country                    |
| gender only           | country\_gender            |
| age only              | country\_age\_band         |
| gender + age          | country\_gender\_age\_band |

This is also why removing a demographic filter doesn’t just average the
cells back together — the dashboard re-loads the coarser stratum.

**11. Rolling-Window Pooling (Period Filter)**

The dashboard’s Period selector — Single month / Last 3 / Last 6 / Last
12 — pools the precomputed monthly cells into a rolling window~~.
Pooling is done in the browser on the embedded JSON and does not change
the published Parquet output.~~

<table>
<thead>
<tr class="header">
<th><strong>Field</strong></th>
<th><strong>Aggregation</strong></th>
<th><strong>Weight</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>n_respondents, n_impact_denominator</td>
<td>sum</td>
<td>—</td>
</tr>
<tr class="even">
<td>adoption_rate</td>
<td>weighted mean</td>
<td>n_respondents</td>
</tr>
<tr class="odd">
<td>weighted_impact_index, net_impact_index,<br />
all impact_share_*, positive/negative share</td>
<td>weighted mean</td>
<td>n_impact_denominator</td>
</tr>
<tr class="even">
<td>dose_response[k] (k = 1…6)</td>
<td>weighted mean</td>
<td>n_impact_denominator</td>
</tr>
</tbody>
</table>

**This is approximate.** The exact pooled value would require re-running
the metric layer on the pooled respondent-level data. The dashboard’s
weighted-mean of monthly aggregates is correct in expectation but
ignores within-month variance and does not produce new confidence
intervals.

Cells suppressed in a given month (originally below MIN\_N) are dropped
before pooling, so a country can appear in the rolling window even if
some of its constituent months were individually suppressed.

**11.1 Pooling Formula**

\[x_{\text{pooled}}\  = \ \frac{\sum\ nₘ\  \cdot \ xₘ}{\sum\ nₘ}\]

where m indexes months in the window and nₘ is the appropriate weight
column for the metric class.

**12. Summary Card (Dashboard)**

The top-right summary card on the dashboard is a fixed reference and is
not affected by Month, Period, Country, Gender, or Age filters. It
always shows:

3.  The global weighted average of the currently-selected metric over
    the trailing 3 full months.

4.  The total respondents over those 3 months.

5.  The total respondents across the entire dataset to date.

**“Full” means non-partial.** The dashboard detects the latest partial
month by comparing each month’s total respondents against the median of
prior months — any month with respondents below 60% × median is
considered still in-flight and excluded from the trailing-3 window. This
is the same rule used to mark the partial point in the trend chart.

Only the metric dropdown updates this card; switching metric swaps the
displayed label and value but does not change the underlying 3-month
window.

**13. Known Limitations**

These limitations apply to every metric above.

**13.1 No Survey Weights (Non-Probability Sample)**

The GMP respondent pool is a convenience sample recruited via online ads
(Google Display, Meta, and organic search). It carries no
post-stratification or design weights. Demographic proportions in the
data do not match national population proportions — countries, age
groups, and genders are represented according to who encounters and
completes the survey, not according to census benchmarks.

All metrics are descriptive statistics of the responding population, not
population-level estimates. Associations between ai\_freq and impact
outcomes are correlational; higher-frequency AI users who report better
outcomes may differ systematically from lower-frequency users in
education, occupation, digital literacy, or other unmeasured
confounders. No causal claims are supported.

> *Planned mitigation: Demographic-weighted averaging using UN World
> Population Prospects age–sex distributions is on the roadmap. This
> would rebalance age and gender composition within each country but
> would not address self-selection or unmeasured confounders.*

**13.2 Composition Effects in Time-Series**

Month-over-month changes may reflect shifts in who is responding rather
than genuine attitudinal change. If a recruitment campaign increases
responses from a younger demographic in one month, and younger
respondents tend to report more positive AI impacts, the global WII will
rise even if no individual changed their view. Country mix changes and
seasonal patterns in survey completion can similarly shift metrics.

The stratified breakdowns (by country, gender, age) partially mitigate
this by holding one dimension constant, but cross-dimensional
composition effects remain. Rolling-window views help smooth short-term
fluctuations.

**13.3 Weight Selection**

The nine IMPACT\_WEIGHTS (§6) were chosen by stakeholder judgment, not
derived from empirical data. Different weight schemes would produce
different index values and could alter relative country rankings.
Sensitivity analysis (varying weights within a plausible range) has not
yet been conducted. The asymmetric design — total negative weight (−2.5)
exceeding total positive weight (+1.5) — is intentional but should be
disclosed when comparing WII values across studies.

**13.4 Rolling-Window Approximation**

Rolling-window pooling (§11) uses total n\_respondents as approximate
weights. The exact calculation would re-aggregate from individual-level
data within the pooled window. The approximation introduces minor error
(±1 percentage point within 3–6 month windows) because the impact
denominator differs slightly from total N. This trade-off is accepted
for client-side performance.

**13.5 Data Source Filtering Not Yet Implemented**

Per Tara’s specification, the production version should restrict the
respondent pool to Google Display and Meta traffic sources and
down-weight organic/search traffic to 10%. This is not yet implemented;
the current pipeline processes all traffic sources equally.

**13.6 Multi-Select Interaction Effects**

The WII treats each flag independently — a respondent selecting both
“improved quality” (+0.5) and “job anxiety” (−0.25) receives the sum
(+0.25). This additive model does not capture potential interactions
between simultaneous positive and negative experiences.

**13.7 Suppression and Small-Cell Noise**

Strata with fewer than 50 respondents (MIN\_N) are suppressed entirely.
For strata just above the threshold (e.g., N = 55), confidence intervals
are wide and point estimates can shift substantially with small data
changes.

**13.8 CIs Assume Simple Random Sampling**

All confidence intervals are computed under a simple-random-sampling
assumption. The GMP is a non-probability convenience sample, so the
intervals represent variability due to finite sample size but do not
account for design effects, clustering, or non-response bias. Confidence
intervals will be revised once survey weights are introduced.
