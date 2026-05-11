# AI Use Impact Tracker — Dashboard Specification

**Version:** 0.2 · **Scope:** the single-page world-map dashboard (`preview.html`)

This document describes the dashboard as a product: what it shows, how filters
compose, and the algorithms that run at view time. It is intentionally
independent of the implementation files. For the metric layer definitions and
the ETL contract, see [`TRACKER.md`](TRACKER.md).

---

## Contents

- [1. Overview](#1-overview)
- [2. Architecture](#2-architecture)
- [3. Data layer](#3-data-layer)
- [4. UI components](#4-ui-components)
- [5. Filter model](#5-filter-model)
- [6. Algorithms](#6-algorithms)
- [7. Visual encoding](#7-visual-encoding)
- [8. Country-name reconciliation](#8-country-name-reconciliation)
- [9. Suppression and missingness](#9-suppression-and-missingness)
- [10. External dependencies](#10-external-dependencies)
- [11. Known limitations](#11-known-limitations)

---

## 1. Overview

The dashboard is a single self-contained HTML file that visualises self-reported
impact of AI use on work, by country and demographic, from the Global Mind
Project (GMP) survey. It is produced by a one-shot bake step over the Parquet
metric layer; once baked, it runs entirely in the browser with no server-side
computation.

Each interaction recomputes three coordinated views from the same precomputed
data and the current filter state:

1. A row of four **KPI cards** (Weighted Impact Index, respondents, adoption
   rate, impact denominator).
2. A **world choropleth** colored by the active metric.
3. A **time-series** chart (only when the period selector is set to a
   multi-month window) and a per-country detail card on click.

The dashboard never aggregates respondent-level data. All values displayed are
derived from the precomputed stratified aggregates in the embedded data layer.
The only client-side aggregation is the rolling-window pooling for multi-month
periods (§6.2) and weighted means across countries for the KPIs and the global
time series.

## 2. Architecture

```
                     ┌────────────────────────────────────┐
                     │           preview.html             │
                     │  ┌──────────────────────────────┐  │
                     │  │ Inline JSON (~5 stratum sets)│  │
                     │  └──────────────────────────────┘  │
                     │  ┌──────────────────────────────┐  │
                     │  │ ES module (d3, topojson,     │  │
                     │  │ Observable Plot via CDN)     │  │
                     │  └──────────────────────────────┘  │
                     └────────────────────────────────────┘
                                       ↑
                                       │  (one-time bake)
                                       │
                  ┌───────────────────────────────────────┐
                  │ tracker/output/v1/metrics/*.parquet   │
                  └───────────────────────────────────────┘
```

**Self-contained.** The HTML is a single file. All data is embedded as inline
JSON inside a `<script>` tag — there is no XHR for survey data. The only
runtime network traffic is:

- Three ES-module imports from jsDelivr: `d3@7`, `topojson-client@3`,
  `@observablehq/plot@0.6`.
- One JSON fetch for the world atlas: `world-atlas@2/countries-110m.json`
  (Natural Earth 110m).

**Pure client-side.** All filtering, pooling, weighted means, color
interpolation, and chart layout happens in the browser. The Flask app that
hosts the file serves it as a static asset; the dashboard does not call back
into the application.

**Reactive.** A single `render()` function is called on every filter change.
It rebuilds the KPIs, the map, and the time-series from scratch — there is no
incremental update path. With ~5 strata × a few thousand cells each, the
all-from-scratch redraw is cheap enough that this stays under one frame.

## 3. Data layer

The dashboard embeds five precomputed stratum tables, each a flat array of
records at monthly grain. Every record represents one (stratum × year × month)
cell.

| Stratum | Key columns | Used when |
|---|---|---|
| `global` | — | Building the master list of available months |
| `country` | `country_clean` | No gender or age filter active |
| `country_gender` | `country_clean`, `gender_clean` | Gender filter only |
| `country_age_band` | `country_clean`, `age_band` | Age filter only |
| `country_gender_age_band` | `country_clean`, `gender_clean`, `age_band` | Both gender and age filters active |

Each record carries the same fixed set of measurement columns (counts, mean
metrics, share metrics, and a nested `dose_response` object keyed by AI-use
frequency level 1–6). The dashboard never reads cells flagged as suppressed —
those are excluded at bake time.

The five-table design is the core performance contract: any combination of
demographic filters selects exactly one precomputed stratum, so the dashboard
never has to roll up over respondent groups at view time. Time-windowing is
the only on-the-fly aggregation, and it is performed per (country × gender ×
age) cell — never across them.

## 4. UI components

### 4.1 Filter bar

Five linked controls plus a reset button:

- **Month** — single dropdown plus prev/next buttons. Lists every (year,
  month) present in the `global` stratum.
- **Period** — Single month / Last 6 months / Last 12 months. Determines how
  many trailing months are pooled (§6.2).
- **Color map by** — selects which precomputed metric drives the choropleth.
  Ten options (see §7.1).
- **Gender** — All, or one of the five canonical labels.
- **Age band** — All, or one of nine bands from 18-20 to 85+.
- **Frequency** — All, or one of six AI-use intensity levels (Rarely …
  Always). When set, the map's color metric is **overridden** to show the
  net impact index at that frequency level (§6.5).

### 4.2 KPI cards

Four headline statistics. Each is recomputed from the rows visible under the
current filter:

| KPI | Computation |
|---|---|
| Weighted Impact Index | Weighted mean across visible (country) rows, weighted by `n_impact_denominator` |
| Respondents | Sum of `n_respondents` across visible rows |
| AI Adoption Rate | Weighted mean of `adoption_rate`, weighted by `n_respondents` |
| Impact Denominator | Sum of `n_impact_denominator` across visible rows |

The Weighted Impact Index card has a colored value:
- Positive values → green
- Negative values → red
- Zero or unknown → neutral

### 4.3 World map

Equal-Earth projection. One filled polygon per country drawn from the Natural
Earth 110m atlas. Countries without a matching row in the current view (no
data, or suppressed) are rendered in neutral gray (`#cbd5e1`).

A custom DOM tooltip follows the cursor when hovering a country:
- Country name (atlas form)
- Metric label and formatted value, **or** "No data / suppressed"
- Respondent count

Clicking a country opens the country detail card (§4.5). The map also draws a
sphere outline so the projection is visible even when most countries are
empty.

### 4.4 Time-series panel

Hidden when **Period = Single month**. Otherwise shows the active metric's
trend across every month in the window, aggregated across all visible
countries by a weighted mean (weight = `n_impact_denominator` for impact
metrics, `n_respondents` for adoption/frequency).

The y-axis is fit tightly to the data (§6.7) rather than using the map's full
visual domain — small month-over-month changes remain readable.

### 4.5 Country detail card

Opened by clicking a country on the map. Shows:

- A grid of every metric for that country under the current filters.
- The dose-response strip: net impact at each AI-use frequency level 1–6,
  with `n/a` shown for levels below the 50-respondent suppression threshold.
- (Multi-month windows only) A small per-country time series of the active
  metric.

When the detail card is open, the global time-series panel is hidden to avoid
visual collision. Closing the detail card restores the global series if the
period is multi-month.

## 5. Filter model

Filters compose as a single conjunction: the visible rows are those that
satisfy **all** of {month in window, gender match, age match}. The frequency
filter is special — it never changes which rows are visible, only how the map
is colored (see §6.5).

The mapping from filter combination to source stratum is fixed:

```
(gender = any,  age = any) → country
(gender = X,    age = any) → country_gender
(gender = any,  age = Y)   → country_age_band
(gender = X,    age = Y)   → country_gender_age_band
```

The dashboard always picks the **most specific** precomputed stratum that
covers the active filters, then narrows by exact-match on the stratifier
columns. This guarantees every cell displayed is an exact precomputed value —
the dashboard never averages across demographic groups.

## 6. Algorithms

### 6.1 Stratum selection

Inputs: the current gender and age-band filter values.

Output: a reference to one of the four country-level stratum arrays, plus the
active gender/age values for downstream exact-match filtering.

The selection is a deterministic 2×2 lookup. The selected array is then
filtered to the rows whose `gender_clean` and `age_band` match the active
values exactly.

### 6.2 Rolling-window pooling

Applied only when **Period > 1**. The window is the most recent `w` months
ending at the selected month, where `w ∈ {6, 12}`.

For each (country, gender, age) cell appearing in any month of the window,
the dashboard emits one pooled row. Aggregation rules per field:

| Field | Aggregation | Weight |
|---|---|---|
| `n_respondents`, `n_impact_denominator` | sum | — |
| `adoption_rate`, `freq_mean` | weighted mean | `n_respondents` |
| `weighted_impact_index`, `net_impact_index`, every `impact_share_*`, `positive_impact_share`, `negative_impact_share` | weighted mean | `n_impact_denominator` |
| `dose_response[k]` for k = 1…6 | weighted mean | `n_impact_denominator` |

Rows where the relevant weight is zero or the value is null are skipped in
the numerator and denominator of the weighted mean — they contribute nothing
to the pooled value.

**This is approximate.** The exact pooled value would require re-running the
metric layer on respondent-level data pooled across months. The dashboard's
weighted mean of monthly aggregates is correct in expectation but ignores
within-month variance. Months below the 50-respondent suppression threshold
were dropped at bake time, so a country may appear in the rolling window even
if some of its constituent months were individually suppressed.

### 6.3 KPI weighted means

For the four KPI cards, the dashboard computes a single weighted mean across
all visible (country) rows after stratum selection and (if applicable) rolling
pooling. The weight depends on the metric:

- `adoption_rate` → weighted by `n_respondents`
- everything else → weighted by `n_impact_denominator`

Sums (Respondents, Impact Denominator) are straight sums across the same row
set.

### 6.4 Choropleth coloring

For each visible country row, the dashboard computes `value = metric(row)`
(see §6.5 for the frequency override). Country names are mapped to atlas
names (§8), then values are joined to atlas features by name.

The color scale is a linear interpolator with:

- A fixed **domain per metric** (see §7.1) — values outside the domain are
  clamped to the endpoint color so a single outlier cannot wash out the rest
  of the map.
- A custom **intensified interpolator** — the dashboard skips the near-white
  tail of the underlying d3 color scheme so even small data values render as
  a recognisable color, distinct from the gray "no data" fill.
  - For diverging schemes (PiYG): the interpolator maps `[0, 1]` into
    `[0.04, 0.96]` of the underlying scheme, pulling both ends toward
    saturated while keeping the midpoint light but not pure white.
  - For sequential schemes (Blues, Greens, Reds): the interpolator maps
    `[0, 1]` into `[0.22, 0.96]`, starting at 22% so low values are visibly
    colored.

Countries with no matching row, or whose value is null, are rendered in
neutral gray (`#cbd5e1`).

### 6.5 Frequency override (dose-response substitution)

When the Frequency filter is set to a level `f ∈ {1, …, 6}`, the metric used
for the map and time-series is **substituted** with `dose_response[f]` — the
precomputed net impact index restricted to respondents who reported AI use at
that frequency level.

This override:
- Replaces the active metric for all map coloring, KPIs, the global time
  series, and the country detail's per-country time series.
- Forces the color scale to the diverging PiYG scheme over domain `[-1, 1]`.
- Does not affect respondent counts or the impact denominator KPIs (those
  remain the broad-population denominators).
- Sets `dose_response[f]` to `null` for cells where fewer than 50 respondents
  selected that frequency level, so under-sampled country-level cells drop
  out of the map.

### 6.6 Time-series aggregation (global)

For the global time-series panel, the dashboard groups visible rows by
year-month and computes a weighted mean of the active metric within each
month — the same weighting rules as §6.3. The resulting series has one point
per month present in the window for which at least one country contributed a
non-null weighted value.

Volume metrics (`adoption_rate`, `freq_mean`) weight by `n_respondents`; all
other metrics weight by `n_impact_denominator`. When the frequency override
is active, all weights revert to `n_impact_denominator`.

### 6.7 Adaptive y-domain (time series)

The map's per-metric domain is the right choice for cross-country comparison
but too wide for trend lines: a 1-percentage-point shift gets flattened
against a 60% domain. The time-series uses an adaptive domain instead:

1. Compute the min and max of the visible series values.
2. Pad both ends by `max(0.15 × (max − min), floor)`, where `floor` is a
   small per-metric-type constant (0.5% for shares, 1% for signed indices,
   5% for ordinals) so a flat series still has vertical breathing room.
3. For share metrics, clamp the lower bound to zero.

This applies independently to each chart instance (global panel and
per-country panel).

## 7. Visual encoding

### 7.1 Metric domains and schemes

The dashboard's color domain for the map is **not** the metric's
mathematical range — it is the visible range chosen to reflect realistic
between-country variation. Outliers saturate at the endpoint color.

| Metric | Map domain | Scheme | Format |
|---|---|---|---|
| Weighted Impact Index | [−0.30, +0.30] | PiYG (diverging) | signed, 3dp |
| Net Impact Index | [−0.50, +0.50] | PiYG (diverging) | signed, 3dp |
| AI Adoption Rate | [0, 100%] | Blues | percent, 1dp |
| Frequency Mean (0–6) | [0, 6] | Blues | ordinal label |
| Improved Quality | [0, 60%] | Greens | percent, 1dp |
| New Opportunities | [0, 40%] | Greens | percent, 1dp |
| Adaptation Pressure | [0, 60%] | Reds | percent, 1dp |
| Job Anxiety | [0, 60%] | Reds | percent, 1dp |
| Job Loss | [0, 15%] | Reds | percent, 1dp |
| Reduced Income | [0, 20%] | Reds | percent, 1dp |
| Net impact at chosen frequency (override) | [−1, +1] | PiYG | signed, 3dp |

**Why colors group this way:**
- PiYG (pink-yellow-green diverging) for signed indices where positive and
  negative both carry meaning.
- Blues for neutral volume measures (how much AI is being used).
- Greens for positive-sentiment shares (good outcomes).
- Reds for negative-sentiment shares (bad outcomes).

### 7.2 Legend

The legend shows the active color scale as a horizontal swatch with
endpoint labels and a count of visible countries. For Frequency Mean, the
endpoint labels are hidden and the seven ordinal labels (Never … Always) are
laid out beneath the swatch instead.

### 7.3 Number formatting

| Type | Format |
|---|---|
| Share / percent | `XX.X%` |
| Signed index | `+0.123` / `−0.123` |
| Ordinal mean (frequency) | `3.42 (Weekly)` — numeric mean plus nearest ordinal label |
| Counts | locale-formatted with thousands separators |
| Missing | em-dash `—` |

## 8. Country-name reconciliation

The GMP survey writes country names in their full English form (or, in some
cases, in a non-Latin script — those are canonicalised at the ETL layer).
The Natural Earth 110m atlas uses abbreviated forms ("Dem. Rep. Congo",
"Bosnia and Herz.", "S. Sudan") and some renderings that have changed over
time ("Czechia", "Türkiye", "eSwatini").

The dashboard ships with an alias table mapping ~60 GMP names to their atlas
equivalents. Categories of mapping:

- Anglo/Latin variants: `USA`, `U.S.`, `Great Britain`, `Britain` → atlas
  forms.
- ISO-3166 long-form: `Russian Federation` → `Russia`, `Lao People's
  Democratic Republic` → `Laos`, etc.
- SAR / annotated names: `Hong Kong SAR`, `Hong Kong, China` → `Hong Kong`.
- Recent renamings: `Turkey` → `Türkiye`, `Swaziland` → `eSwatini`.
- Atlas abbreviations: `Bosnia and Herzegovina` → `Bosnia and Herz.`,
  `Central African Republic` → `Central African Rep.`, etc.

A country in the GMP data with no atlas match falls through the table
unchanged. If the atlas has no matching feature for that name, the country's
value is silently dropped from the map (it will still appear in the country
detail if reached by some other path, but cannot be clicked from the map).

This table is the maintenance seam: as new country variants appear in GMP
data, they are added here without touching the metric layer.

## 9. Suppression and missingness

The dashboard applies suppression at three points:

1. **Cell-level**, at bake time. Any (stratum × month) cell with
   `n_respondents < 50` was flagged at the ETL stage and excluded from the
   embedded JSON. The dashboard never sees these cells.
2. **Frequency-level**, within `dose_response`. The nested object stores
   `null` for any AI-use frequency level (1–6) where fewer than 50
   respondents in that cell selected that level. The dashboard renders these
   as `n/a` in the dose-response strip and excludes them from the map under
   the frequency override.
3. **Atlas-level**. Countries with no matching atlas feature do not appear on
   the map regardless of data availability.

Countries shown as gray on the map fall into one of: no respondents in the
current filter combination, all relevant cells suppressed at bake time, or
the active metric is null in the (otherwise valid) cell.

The legend caption shows the count of countries that **do** have a value
under the current filters, alongside the filter summary.

## 10. External dependencies

The dashboard requires network access at view time for:

| Resource | Source | Purpose |
|---|---|---|
| `d3@7` | jsDelivr | Color interpolators, JSON fetch helper |
| `topojson-client@3` | jsDelivr | TopoJSON → GeoJSON conversion |
| `@observablehq/plot@0.6` | jsDelivr | All chart rendering (map + time series) |
| `world-atlas@2/countries-110m.json` | jsDelivr | Country geometries (Natural Earth 110m, ~110 KB) |

If any of these fail to load, the dashboard degrades gracefully:
- Plot/d3/topojson failures break the page (no fallback).
- A world-atlas fetch failure replaces the map area with a "Could not load
  world map atlas. Check internet connection." notice; KPIs and the
  time-series remain functional.

There is no offline mode. The dashboard requires an HTTP origin (not
`file://`) to run, because the CDN imports use ES module syntax.

## 11. Known limitations

- **Approximate rolling pooling.** The Last 6 / Last 12 window pools monthly
  aggregates by weighted mean; the exact value would require pooling
  respondent-level data first. This biases nothing in expectation but
  understates uncertainty.
- **No confidence intervals shown.** The ETL emits Wilson 95% CIs for every
  share metric and SE-based CIs for the mean metrics; the dashboard does not
  currently render them.
- **No survey weights.** The dashboard inherits the metric layer's choice to
  treat respondents as an equal-weighted sample. Cross-country comparisons
  should be read as descriptive, not population-representative.
- **No composition decomposition.** Month-over-month shifts in a country's
  weighted impact index may reflect a change in respondent mix rather than a
  change in attitude. The dashboard does not surface this.
- **Static color domains.** The per-metric color domains are chosen for a
  visually informative spread on the current data and are not adaptive. If
  the underlying distribution shifts substantially, the domains may need to
  be reconsidered.
- **Editorial weights.** The `IMPACT_WEIGHTS` baked into the Weighted Impact
  Index reflect editorial judgment about relative severity. They are not
  empirically calibrated. The dashboard takes them as given.
- **Network-dependent.** A failed CDN or atlas fetch breaks the
  visualization. There is no bundled fallback geometry.
