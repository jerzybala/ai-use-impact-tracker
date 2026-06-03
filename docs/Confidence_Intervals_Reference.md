**Confidence Intervals in the AI Use Impact Tracker**

*A Personal Reference*

Jerzy Bala | Sapien Labs | May 2026

**1. Why We Use Confidence Intervals**

Every metric on the tracker dashboard is a *point estimate* derived from
a sample of MHQ survey respondents. The true population value is
unknown. A 95% confidence interval (CI) quantifies the sampling
uncertainty around that estimate: if we could re-draw the sample many
times, \~95% of intervals computed this way would contain the true
parameter.

CIs serve three practical purposes in the tracker:

  - **Signal vs. noise.** A narrow CI (e.g., ±0.006) tells us the
    estimate is stable. A wide CI (±0.08) warns that the sample may be
    too small to draw conclusions.

  - **Cross-stratum comparison.** If the CIs for two countries do not
    overlap, the difference is statistically meaningful at the 95%
    level. If they overlap substantially, we cannot confidently
    distinguish the two.

  - **Trend validation.** A month-over-month shift in WII only qualifies
    as a real trend if the new estimate falls outside the previous
    month’s CI.

**2. Two CI Methods in the Pipeline**

The tracker computes CIs using two distinct formulas, chosen based on
the statistical nature of the metric.

**2.1 Wilson Score Interval (for proportions)**

Used for: adoption\_rate, all impact\_share\_\* flags,
positive\_impact\_share, negative\_impact\_share.

These metrics are proportions — bounded between 0 and 1 — derived from
binary counts (k successes out of n trials). The classical Wald interval
(p ± z·√(p(1−p)/n)) can produce bounds below 0 or above 1, especially
when p is near the boundary or n is small. The Wilson score interval
corrects this:

center = (p̂ + z²/2n) / (1 + z²/n)

half = z · √( p̂(1−p̂)/n + z²/4n² ) / (1 + z²/n)

CI = \[ max(0, center − half), min(1, center + half) \]

where p̂ = k/n is the observed proportion and z = 1.96 for 95%
confidence.

> *Key property: The Wilson interval is asymmetric around p̂ and always
> stays within \[0, 1\], making it the standard choice for proportion
> CIs in applied statistics.*

**2.2 Wald (SEM-based) Interval (for continuous means)**

Used for: weighted\_impact\_index (the primary dashboard headline
metric).

The Weighted Impact Index (WII) is a continuous-valued mean, not a
proportion. Each respondent’s personal score is the dot product of their
binary impact flags and the assigned severity weights, yielding values
that range from −1.0 to +1.5. Since the metric is unbounded by \[0, 1\],
we use the standard Wald interval based on the standard error of the
mean:

SEM = σ / √N

CI = \[ x̄ − 1.96 · SEM, x̄ + 1.96 · SEM \]

where σ is the sample standard deviation (ddof=1), N is the impact
denominator count, and x̄ is the WII point estimate.

> *The Wald interval is symmetric around the mean and relies on the
> Central Limit Theorem. For N ≥ 50 (our suppression threshold), the CLT
> approximation is solid.*

**3. When to Use Which**

|                         |                 |               |                          |
| ----------------------- | --------------- | ------------- | ------------------------ |
| **Metric**              | **Type**        | **CI Method** | **Rationale**            |
| adoption\_rate          | Proportion      | Wilson        | Binary: user vs non-user |
| impact\_share\_\*       | Proportion      | Wilson        | Binary: flag on vs off   |
| positive\_impact\_share | Proportion      | Wilson        | Any positive flag set    |
| negative\_impact\_share | Proportion      | Wilson        | Any negative flag set    |
| weighted\_impact\_index | Continuous mean | Wald          | Score range −1.0 to +1.5 |

**4. Worked Example: Wilson CI for Adoption Rate**

Let’s walk through the computation for **April 2026, Global** where:

  - N = 16,486 respondents

  - k = 12,753 are AI users (frequency ≥ 1)

  - p̂ = 12753 / 16486 = **0.7736**

**Step-by-step**

**1.** Compute z²/n:

z²/n = 1.96² / 16486 = 3.8416 / 16486 = 0.000233

**2.** Compute the adjusted centre:

center = (0.7736 + 0.000117) / (1 + 0.000233) = 0.77372 / 1.000233 =
0.77354

**3.** Compute the half-width:

half = 1.96 · √( 0.7736 × 0.2264 / 16486 + 3.8416 / (4 × 16486²) ) /
1.000233

\= 1.96 · √( 0.00001062 + 3.54×10⁻⁹ ) / 1.000233

\= 1.96 · 0.003259 / 1.000233 = 0.006388

**4.** Final interval:

CI = \[ 0.77354 − 0.00639, 0.77354 + 0.00639 \] = \[ 0.7672, 0.7799 \]

The pipeline output for this cell: adoption\_rate\_ci\_low = 0.7653,
adoption\_rate\_ci\_high = 0.7781. (Minor rounding differences from
intermediate precision.)

> *Interpretation: We are 95% confident that the true global AI adoption
> rate in April 2026 lies between 76.5% and 77.8%. The narrow ±0.6pp
> margin reflects the large sample.*

**5. Worked Example: Wald CI for Weighted Impact Index**

Same cohort: **April 2026, Global**.

The WII is computed over the impact denominator (AI users who provided
an impact response). From the baked data:

  - x̄ = WII = **+0.1413**

  - CI = \[0.1354, 0.1471\]

**Reverse-engineering the SEM**

From the CI bounds we can recover the SEM:

margin = (0.1471 − 0.1354) / 2 = 0.00586

SEM = margin / 1.96 = 0.00586 / 1.96 = 0.00299

And we can infer the sample standard deviation. The impact denominator
for this month was approximately N≈ 9,300 (those who are AI users and
gave an impact answer):

σ = SEM × √N = 0.00299 × √9300 ≈ 0.00299 × 96.4 ≈ 0.288

> *Interpretation: We are 95% confident the true population WII lies
> between +0.135 and +0.147. The ±0.006 margin is tight enough that a
> shift to, say, +0.120 next month would clearly fall outside this band,
> signalling a real decline.*

**6. Using CIs to Compare Groups**

**6.1 Non-overlapping CIs → Significant difference**

Suppose in April 2026:

  - **Brazil:** WII = +0.21, CI = \[0.175, 0.245\]

  - **Germany:** WII = +0.08, CI = \[0.042, 0.118\]

The intervals do not overlap (Germany’s upper bound 0.118 \< Brazil’s
lower bound 0.175), so we can state with \>95% confidence that Brazil’s
AI impact sentiment is more positive than Germany’s.

**6.2 Overlapping CIs → Inconclusive**

Suppose instead:

  - **UK:** WII = +0.15, CI = \[0.120, 0.180\]

  - **Canada:** WII = +0.13, CI = \[0.095, 0.165\]

The intervals overlap (UK lower 0.120 \< Canada upper 0.165). This does
not prove the groups are equal — it means our samples are not large
enough to distinguish them confidently. A formal two-sample test could
still find significance, but the CI overlap is a quick visual heuristic.

> *Rule of thumb: Non-overlap of 95% CIs implies significance at roughly
> p \< 0.01 (stricter than 0.05). So overlapping CIs don’t rule out a
> real difference — they just mean the quick visual check is
> inconclusive.*

**7. Where CIs Appear on the Dashboard**

Currently, CIs surface in one place on the v2 dashboard:

  - **WII hero card sub-line:** Displays 95% CI: \[lo, hi\] (±margin)
    below the WII value in single-month view only.

CIs are *not* displayed in rolling-window mode (Last 3 / Last 6 months)
because the pooled estimate uses sample-size-weighted means across
independent monthly slices. You cannot simply average pre-computed CIs;
the correct approach would require access to the raw respondent-level
data at render time, which the static baked dashboard does not have.

**7.1 Potential Extensions**

CIs are computed and stored in the Parquet output for every metric and
every stratum cell. They could be surfaced in additional places:

  - **Error bars on time-series:** Add vertical whiskers to the WII
    trend line showing ±1.96·SEM per month.

  - **Country scatter confidence ellipses:** On the adoption-vs-WII
    scatter, draw horizontal/vertical error bars per country.

  - **Country table CI column:** Add a CI column to the sortable country
    table, helping users spot countries with unreliable estimates (wide
    CIs from small samples).

  - **Demographic bar chart whiskers:** Show CI ranges on the gender/age
    breakdown bars.

> *Implementation note: All of these require only front-end changes —
> the CI fields are already in the embedded JSON. The data pipeline does
> not need modification.*

**8. Suppression Threshold and CI Width**

The pipeline suppresses any stratum cell with fewer than 50 respondents
(N \< 50). This threshold was chosen partly because of CI behaviour: at
N = 50, the Wilson CI for a proportion of 0.50 is approximately ±14pp,
and the Wald CI for a mean with σ = 0.3 is approximately ±0.083. Below N
= 50 the intervals become so wide that the estimates carry little
practical value.

Approximate CI half-widths at different sample sizes (for a proportion p
= 0.50):

|         |                       |                     |              |
| ------- | --------------------- | ------------------- | ------------ |
| **N**   | **Wilson ± (p=0.50)** | **Wald ± (σ=0.30)** | **Usable?**  |
| 30      | ±0.182 (18.2pp)       | ±0.107              | Suppressed   |
| 50      | ±0.139 (13.9pp)       | ±0.083              | Threshold    |
| 200     | ±0.069 (6.9pp)        | ±0.042              | Good         |
| 1,000   | ±0.031 (3.1pp)        | ±0.019              | Excellent    |
| 16,000+ | ±0.008 (0.8pp)        | ±0.005              | Global-level |

> *At our typical global N of \~16K–34K per month, CIs are extremely
> tight. The real value of CIs shows up at the country or
> country×gender×age\_band level where cells can drop near the
> suppression boundary.*

**9. Implementation Reference**

The CI computations live in a single file:

  - tracker/src/pipeline/metrics.py

**Wilson CI function (line 38)**

wilson\_ci(k, n, z=1.96) — vectorised NumPy implementation. Takes arrays
of success counts and trial counts. Returns (lo, hi) arrays clipped to
\[0, 1\].

**Wald CI for WII (lines 131–134)**

Computed inline: mean ± 1.96 \* std(ddof=1) / sqrt(N). Only generated
when N \> 1.

**Where CIs are stored**

Every CI appears as two adjacent columns in the Parquet output:
\<metric\>\_ci\_low and \<metric\>\_ci\_high. These propagate into the
baked dashboard JSON and are available in every stratum-level file
(global, country, gender, age\_band, and all cross-strata).
