# AI Impact Tracker — Dashboard Guide

A plain-English walkthrough of what the dashboard shows and how it works.
For the formulas behind every number, see [METRICS.md](METRICS.md). For
the source-side survey columns, see [COLUMNS.md](COLUMNS.md).

---

## Contents

- [1. What this dashboard shows](#1-what-this-dashboard-shows)
- [2. How it works](#2-how-it-works)
- [3. What data is behind it](#3-what-data-is-behind-it)
- [4. The page in detail](#4-the-page-in-detail)
- [5. How filters work together](#5-how-filters-work-together)
- [6. How the numbers are calculated](#6-how-the-numbers-are-calculated)
- [7. Colors and number formats](#7-colors-and-number-formats)
- [8. Quick metric reference](#8-quick-metric-reference)

---

## 1. What this dashboard shows

The AI Impact Tracker visualises how people around the world report AI is
affecting their work — based on responses to the Global Mind Project
survey by Sapien Labs.

In one view, you see:

- A fixed **summary card** at the top right with the trailing-3-month
  global average for the selected metric.
- A **detail panel** for the currently-selected country (or for the
  Global aggregate when no country is selected).
- A **world map** colored by the metric you choose.
- A **trend chart** showing the selected metric over the last 12 months,
  for the selected country (or globally).

You can filter the map and detail/trend views by month, period, country,
gender, and age band. The summary card at the top is intentionally fixed
and is not affected by those filters — it's a stable reference number.

## 2. How it works

The dashboard is a single web page. Once it loads, every number you see
is computed in your browser from precomputed monthly summaries embedded
in the page — no server is doing any calculation. Changing filters
re-draws the views instantly with no further network traffic.

You need an internet connection on first load to fetch the chart library
and the world-map shapes (Natural Earth, via CDN). After that, everything
is local.

## 3. What data is behind it

The dashboard works with **monthly summaries**, not raw survey responses.
For each combination of country × gender × age band × month, one row of
pre-calculated numbers is baked into the page.

A few things to know:

- **Suppression for small samples.** Any month × stratum cell with fewer
  than 50 respondents is dropped — it does not appear on the map and is
  not in any total. This protects against numbers too noisy to trust.
- **Monthly grain.** Every row is for one month. When you select "Last 3
  months" or "Last 6 months", the dashboard combines the monthly rows
  into a weighted rolling summary (see §6).
- **Below-threshold demographics are hidden.** The Gender and Age band
  dropdowns only list categories that have at least one non-suppressed
  cell, so you can't pick options that would show "no data" everywhere.

## 4. The page in detail

### Header

- **Title** — "AI Impact Tracker: **Impact of AI on Work**". The topic is
  rendered as a dropdown; today it only has one option, but future
  releases will offer other AI-impact lenses.
- **Summary card (top-right)** — a fixed reference: the global weighted
  average of the selected metric over the **trailing 3 full months**,
  plus respondents in that window and total respondents to date. This
  card does *not* respond to filter changes; only switching metrics
  updates its label and value.
- **Help menu** — links to this guide, the methodology doc, and the data
  column reference.

### Filter bar

- **Month** — pick a specific month, or use the arrows to step forward
  and back one month at a time.
- **Period** — Single month · Last 3 months · Last 6 months · Last 12
  months. The multi-month options pool months into a rolling summary.
  Default is **Last 3 months**.
- **Select Work Impact Factor** — which metric colors the map and drives
  the summary card / trend chart. Eight options (see §8).
- **Gender** — All, or one specific category (filtered to those with
  data available).
- **Age band** — All, or one specific range (filtered to those with
  data available).
- **Country** — Global (default), or one specific country. Drives the
  detail panel and the trend chart. Map clicks update this too.
- **Reset filters** — restores defaults: latest month, Last 3 months,
  Weighted Impact Index, no demographic filter, Global.

### Detail panel

Always visible. Shows metric values for the selected country (or for
the Global aggregate when no country is selected) under the active
month / period / demographic filters. Includes a **dose-response** strip
showing the Net Impact Index broken out by AI-use frequency level
(Rarely → Always).

When viewing a **single month**, the Weighted Impact Index stat also
displays a **95% confidence interval** badge — a blue pill showing the
interval bounds and the ± margin. This interval is a Wald CI computed
from the standard error of the weighted mean (mean ± 1.96 × SE). The
badge is only shown for single-month views because multi-month
(rolling) summaries are weighted averages of pre-aggregated monthly
cells, which do not preserve the within-month variance needed to
compute a valid interval.

### World map

Each country is filled with a color showing its value for the chosen
metric. Light gray means no data or too few respondents under the
current filters.

- **Hover** for a tooltip with the value and respondent count.
- **Click** to select that country — the detail panel and trend chart
  update, and the Country dropdown follows along.

### Trend chart

Sits to the right of the map. Always shows the trailing 12 months of
the selected metric for the selected country (or for the global
weighted average if no country is chosen). It is **independent of the
Period filter** so trends stay readable when Period is set to a short
window.

The chart marks the latest month as "partial" with an outlined dot
when its total respondents are well below the median of prior months
— a signal that the month is still in-flight. The line stops at the
last complete month and the partial point sits unconnected to its
right.

If the selected country has fewer than 3 months of data, the chart
shows "Insufficient data to show a trend." instead.

## 5. How filters work together

Every filter applies at the same time. Behind the scenes, the dashboard
picks the **most specific precomputed slice** that matches your filter
combination — so every displayed number is exact, not approximated.

| Filters | Slice used |
|---|---|
| no demographic filter | per-country |
| gender only | per-country × gender |
| age only | per-country × age |
| gender + age | per-country × gender × age |

When you remove a demographic filter, the dashboard does not re-average
visible cells — it loads the coarser precomputed slice. This is why
"All women across all ages" is *not* a simple mean of the age-band
buckets.

## 6. How the numbers are calculated

The short version is below. For the full formulas — including the
Wilson confidence intervals, the impact severity weights table, and how
multi-month pooling weights months — see [METRICS.md](METRICS.md).

### Combining countries

When the dashboard needs a single number across many countries (for the
summary card or the trend chart), it does **not** take a simple average.
It uses a **weighted average** — each country contributes in proportion
to its respondent count. A country with 10,000 respondents counts ten
times more than one with 1,000.

- **Impact metrics** weight by the impact denominator (AI users who
  reported any impact).
- **Adoption rate** weights by the total respondent count.

### Combining months (Last 3 / 6 / 12 periods)

Each (country × gender × age) cell across the window is pooled with a
weighted mean — months with more respondents count more. This is an
**approximation**: the most rigorous approach would be to recompute
everything from the pooled raw responses, but that's not practical
inside a browser. The weighted average of monthly cells is correct in
expectation but loses some within-month variance.

### Dynamic map colors

The map's color scale is rebuilt from the **actual data** every time
you change a filter — the darkest color always lands on the highest
observed value, so subtle differences between countries stay visible.
Weighted Impact and the other diverging-by-nature metrics get a
symmetric scale around 0 so the neutral midpoint stays at the lightest
color.

## 7. Colors and number formats

### Color schemes

Every metric uses a **single-hue** ramp from light to dark.

| Metric | Color | Reads as |
|---|---|---|
| Weighted Impact Index | Light → dark green | Darker = stronger positive impact (negative values show light green). |
| AI Adoption Rate | Light → dark blue | Darker = more AI use. |
| Improved Quality, New Opportunities (positive shares) | Light → dark green | Darker = more people reporting this positive effect. |
| Adaptation Pressure, Job Anxiety, Job Loss, Reduced Income (negative shares) | Light → dark red | Darker = more people reporting this negative effect. |

The range shown in the legend reflects the **actual data range** of
the current view, not a fixed bound.

### Number formats

- **Percentages** — one decimal place (e.g. `12.3%`)
- **Weighted Impact Index** — two decimals, with `-` for negatives
  (e.g. `0.17`, `-0.04`)
- **Counts** — thousands separators (e.g. `12,456`)
- **Missing values** — em-dash `—`

## 8. Quick metric reference

The "Select Work Impact Factor" dropdown surfaces eight metrics. Each
also appears in the detail panel along with a dose-response strip.

| Metric | What it measures |
|---|---|
| **Weighted Impact Index** | A single signed score of AI's overall effect on work, with severe outcomes weighted more heavily than mild ones. Headline metric. |
| **AI Adoption Rate** | Share of respondents who use AI at all (any frequency above "Never"). |
| **Improved Quality** | Share of AI users who say AI improved their work quality or output. |
| **New Opportunities** | Share of AI users who say AI created new job or income opportunities. |
| **Adaptation Pressure** | Share of AI users who feel pressure to adapt or work faster because of AI. |
| **Job Anxiety** | Share of AI users worried about the future of their job or industry. |
| **Job Loss** | Share of AI users who say AI caused them to lose their job. |
| **Reduced Income** | Share of AI users who say AI reduced their income or made it harder to find work. |

For the underlying definitions (impact denominator, impact severity weights,
dose-response), see [METRICS.md](METRICS.md).

**Reading the shares:**

- They can **sum to more than 100%** — respondents can pick multiple
  impact options at once.
- All impact shares use the **same denominator** (the impact
  denominator), so they are directly comparable.
- Adoption Rate uses the **total respondent count** as its denominator,
  since people who don't use AI still count toward the population.
