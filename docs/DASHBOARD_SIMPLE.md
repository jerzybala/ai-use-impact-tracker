# AI Use Impact Tracker — Dashboard Guide

A plain-English walkthrough of what the dashboard shows and how it works.
For the full technical specification, see [DASHBOARD.md](DASHBOARD.md).

---

## Contents

- [1. What this dashboard shows](#1-what-this-dashboard-shows)
- [2. How it works](#2-how-it-works)
- [3. What data is behind it](#3-what-data-is-behind-it)
- [4. The page in detail](#4-the-page-in-detail)
- [5. How filters work together](#5-how-filters-work-together)
- [6. How the numbers are calculated](#6-how-the-numbers-are-calculated)
- [7. What the colors and numbers mean](#7-what-the-colors-and-numbers-mean)
- [8. Metric reference](#8-metric-reference)

---

## 1. What this dashboard shows

The dashboard visualises how people around the world report AI is affecting
their work — based on responses to the Global Mind Project survey by
Sapien Labs.

In one view, you see:

- Four **headline numbers** at the top
- A **world map** colored by the metric you choose
- A **trend chart** (when looking at more than one month)
- A **detailed card** for any country you click

You can filter the view by month, period, gender, age band, and how often
respondents use AI.

## 2. How it works

The dashboard is a single web page. Once it loads, everything runs in your
browser — no server is doing any calculation. All the numbers needed are
built into the page itself when it is "baked" from the survey data.

- The numbers come from a precomputed dataset.
- The map shapes come from a public world map dataset (Natural Earth).
- The dashboard re-draws the three views every time you change a filter.

You need an internet connection on first load to fetch the chart library and
the world map shapes. Once loaded, you can change filters freely without any
more network traffic.

## 3. What data is behind it

The dashboard works with **monthly summaries**. For each combination of
country, gender, age band, and month, it has one row of pre-calculated
numbers.

A few things to know about the data:

- **Suppression for small samples.** If fewer than 50 people are in a
  particular slice (for example, women aged 18–20 in a specific country for
  one month), that slice is **dropped** — it does not appear on the map and
  is not in the totals. This protects against numbers that would be too
  noisy to be meaningful.
- **Monthly grain.** Every row is for one month. When you select "Last 6
  months", the dashboard combines six monthly rows into a single value (see
  [§6](#6-how-the-numbers-are-calculated) for how).
- **No raw survey responses.** The dashboard never works with individual
  respondents — only with the precomputed monthly summaries.

## 4. The page in detail

### Filter bar (top)

Five dropdowns plus a reset button:

- **Month** — pick a specific month, or use the arrows to step forward or
  backward one month at a time.
- **Period** — Single month, Last 6 months, or Last 12 months. The
  multi-month options combine recent months into a rolling summary.
- **Color map by** — picks which measure to use to color the world map. Ten
  options, including AI Adoption Rate, Improved Quality, Job Anxiety, etc.
- **Gender** — All, or one specific group.
- **Age band** — All, or one specific age range.
- **Frequency** — All, or only respondents who use AI at a chosen intensity
  (e.g. Daily, Constantly). When set, the map switches to show **net
  impact** specifically at that frequency.

### Headline numbers (KPI cards)

Four cards at the top:

- **Weighted Impact Index** — a single number summarising how positive
  (green) or negative (red) the overall AI impact is. It combines all
  reported effects with weights that give more importance to severe ones
  (for example, job loss counts more than mild adaptation pressure).
- **Respondents** — total number of people in the current view.
- **AI Adoption Rate** — share of respondents who say they use AI at all.
- **Impact Denominator** — number of AI users who reported at least one
  impact effect. This is the base used for the impact percentages.

### World map (center)

Every country is filled with a color showing its value for the chosen
metric. The shading is consistent: stronger color = stronger value.
Countries shown in light gray have either no data or too few respondents
under the current filters.

- **Hover** any country to see a tooltip with its value and respondent count.
- **Click** a country to open its detail card.

### Trend chart (below map, when shown)

Appears when the **Period** is set to Last 6 or Last 12 months. Shows the
chosen metric over time as a single line for all currently visible
countries combined.

### Country detail card (after clicking a country)

Shows every metric for that country under the current filters, plus a
**dose-response** strip — how net impact changes across different AI-use
frequencies (Rarely, Monthly, Weekly, Daily, Constantly, Always). When you
are looking at a multi-month period, it also shows the country's own trend
line.

Close the card with the × in the top right.

## 5. How filters work together

All filters apply at the same time. The view shows only the data that
matches every filter.

The **Frequency** filter is the one exception. Instead of hiding data, it
**changes what the map measures**. When a frequency is selected, the map
shows the net positive-vs-negative impact specifically among people who use
AI at that frequency.

Behind the scenes, the dashboard always picks the most specific
pre-summarised slice of the data that matches your filter combination. If
you filter by Women + age 25–34, the dashboard goes straight to the
precomputed table for that exact combination — it does not average across
other groups. This means every number you see is exact, not approximated.

## 6. How the numbers are calculated

### Combining countries (KPIs and trend chart)

When the dashboard needs a single number across many countries (for the KPI
cards or the trend line), it does not take a simple average. It uses a
**weighted average** — each country contributes in proportion to its
number of respondents. A country with 10,000 respondents counts ten times
more than one with 1,000.

- For **impact metrics**, the weight is the number of AI users who reported
  impacts (the "impact denominator").
- For **overall metrics** like adoption rate, the weight is the total
  respondent count.

### Combining months (Last 6 / Last 12 periods)

When you select a multi-month period, the dashboard combines the monthly
numbers for each country into one rolling value. This is also a weighted
average — months with more respondents count more.

This is an **approximation**. The most rigorous approach would be to
recalculate everything from the raw survey responses pooled across months,
but that is not practical inside the dashboard. The weighted average of
monthly summaries gives the right value on average, but loses some
information about month-to-month variability.

### Frequency-based view

When you set the Frequency filter, the map switches to a measure called
**net impact** — the share of people reporting positive effects minus the
share reporting negative effects — calculated only among respondents at
that frequency level. So you can ask: "Among Daily AI users in each
country, what is the balance of positive vs negative experiences?"

### Adaptive trend lines

The trend chart automatically zooms its vertical axis to fit the data, with
a small amount of padding. This makes small month-to-month changes easier
to see than if the chart always used the same scale as the map.

## 7. What the colors and numbers mean

### Color schemes

The dashboard uses different color schemes for different types of metric:

| Type of metric | Colors | Meaning |
|---|---|---|
| Signed indices (Weighted Impact, Net Impact) | Pink → light → green | Pink = more negative · green = more positive · light yellow middle = roughly balanced |
| Volume measures (Adoption Rate, Frequency Mean) | Light → dark blue | Darker = more AI use |
| Positive-effect shares (Improved Quality, New Opportunities) | Light → dark green | Darker = more people reporting this positive effect |
| Negative-effect shares (Adaptation Pressure, Job Anxiety, Job Loss, Reduced Income) | Light → dark red | Darker = more people reporting this negative effect |

### Color ranges

Each metric has a sensible range chosen for readability. For example, the
Weighted Impact Index map runs from −0.30 to +0.30 (not the full
mathematical −1 to +1), because realistic country values mostly sit in the
inner range. Countries with values outside the visible range still get
colored, but stay at the endpoint color rather than stretching the whole
scale.

### Number formats

- **Percentages** — shown to one decimal place (e.g. `12.3%`)
- **Signed indices** — shown to three decimals with a sign (e.g. `+0.142`,
  `−0.073`)
- **Frequency mean** — shown as a decimal with the closest named level
  (e.g. `3.42 (Weekly)`)
- **Counts** — formatted with thousands separators (e.g. `12,456`)
- **Missing values** — shown as an em-dash `—`

## 8. Metric reference

The dashboard surfaces twelve metrics across the KPI cards, the map, and the
country detail card. Each row below explains what one measures, how the
dashboard arrives at the number, and why it is worth paying attention to.

| Metric | What it measures | How it is computed | Why it matters |
|---|---|---|---|
| **Weighted Impact Index** *(headline KPI + map)* | A single signed score of AI's overall effect on work, with severe outcomes weighted more heavily than mild ones. | For each AI user with any impact response, sum signed weights: job loss `−1.0`, reduced income `−0.75`, adaptation pressure `−0.5`, job anxiety `−0.25`, improved quality `+0.5`, new opportunities `+1.0`. Then average across those users. | The headline number — does AI help or hurt overall, with severity baked in (a job loss outweighs mild stress). |
| **Net Impact Index** *(map)* | The simple balance of positive vs negative experiences, unweighted. | (Share reporting any positive effect) minus (share reporting any negative effect). Range −1 to +1. | A simpler alternative to the Weighted Impact Index. Tells you how many people had good vs bad experiences, without judging severity. |
| **AI Adoption Rate** *(KPI + map)* | Share of respondents who use AI at all. | Number whose AI-use frequency is anything other than "Never", divided by total respondents. | Measures penetration — how widely AI use has spread in a population. |
| **Frequency Mean (0–6)** *(map)* | Average AI-use intensity on a 0–6 scale. | Map each respondent's frequency to a number (Never 0 · Rarely 1 · Monthly 2 · Weekly 3 · Daily 4 · Constantly 5 · Always 6), then average across respondents who answered. | Distinguishes "many people use AI rarely" from "fewer people use it constantly" — depth of use, not just breadth. |
| **Respondents** *(KPI)* | Number of people in the current filtered view. | A straight count after applying the active month, gender, age, and frequency filters. | Tells you how much data is behind the numbers shown. Trust is low when this is small. |
| **Impact Denominator** *(KPI)* | Number of AI users who reported at least one specific impact (positive, negative, or neutral). | Count of respondents who use AI **and** selected any non-blank answer to the impact question. | The base for every impact percentage below. If this is much smaller than Respondents, most people in the slice don't use AI or didn't answer the impact question. |
| **Improved Quality** *(share, map)* | Share of AI users who say AI improved the quality or output of their work. | Number who selected "Improved my work quality or output" divided by the Impact Denominator. | The most common positive outcome — a sign AI is acting as a productivity aid. |
| **New Opportunities** *(share, map)* | Share of AI users who say AI created new job or income opportunities for them. | Number who selected "Created new job or income opportunities" divided by the Impact Denominator. | The strongest positive signal — AI helping people expand earnings or enter new work, not just polish existing tasks. |
| **Adaptation Pressure** *(share, map)* | Share of AI users who feel pressure to adapt or work faster because of AI. | Number who selected "Increased pressure to adapt or work faster" divided by the Impact Denominator. | A mild negative — captures stress and pace-of-change concerns even when jobs themselves aren't threatened. |
| **Job Anxiety** *(share, map)* | Share of AI users who worry about the future of their job or industry. | Number who selected "Made me worry about the future of my job or industry" divided by the Impact Denominator. | A forward-looking negative — anxiety about future replacement or industry disruption, regardless of current impact. |
| **Job Loss** *(share, map)* | Share of AI users who say AI caused them to lose their job. | Number who selected "Caused me to lose my job" divided by the Impact Denominator. | The most serious negative outcome. Even small percentages are significant because of severity. |
| **Reduced Income** *(share, map)* | Share of AI users who say AI reduced their income or made it harder to find work. | Number who selected "Reduced my income or made it harder to find work" divided by the Impact Denominator. | A serious financial negative — captures harm short of outright job loss, including freelancers losing clients or hours. |
| **Dose-response** *(country detail card)* | Net impact broken out by AI-use frequency level. | For each frequency level separately (Rarely → Always), compute the Net Impact Index using only respondents at that level. | Reveals whether intensive AI users have systematically different experiences from light users — does more AI make work better or worse? |

**Notes on reading the shares**

- The impact shares can **sum to more than 100%**. Respondents could pick
  several impact options at once — for example, a single person could
  report both Improved Quality and Job Anxiety.
- All impact shares use the **same denominator** (the Impact Denominator),
  so they are directly comparable to each other.
- The Adoption Rate uses the **total respondent count** as its denominator
  instead, since people who don't use AI still count toward the population.
