---
title: By country
---

# AI use impact by country

Countries are ordered by sample size (largest first). Only cells passing the n ≥ 50 minimum-N rule are shown.

```js
const country = FileAttachment("data/country.parquet").parquet();
```

```js
const rowsAll = country.toArray().filter(d => !d.suppressed);
const months = Array.from(new Set(rowsAll.map(d => `${d.year}-${String(d.month).padStart(2,"0")}`))).sort();
const latestMonth = months[months.length - 1];
```

```js
// Pick top-N countries by total respondents across all months
const totals = d3.rollups(rowsAll, v => d3.sum(v, d => d.n_respondents), d => d.country_clean)
  .sort((a,b) => b[1] - a[1]);
const topN = 12;
const topCountries = totals.slice(0, topN).map(d => d[0]);
```

## Top ${topN} countries — ranked by Net Impact Index (${latestMonth})

```js
{
  const latest = rowsAll.filter(d =>
    `${d.year}-${String(d.month).padStart(2,"0")}` === latestMonth
    && topCountries.includes(d.country_clean)
  );
  return Plot.plot({
    height: 340,
    marginLeft: 140,
    x: {grid: true, label: "Net Impact Index", domain: [-0.3, 0.7]},
    marks: [
      Plot.ruleX([0], {stroke: "#999"}),
      Plot.barX(latest, {
        y: "country_clean",
        x: "net_impact_index",
        fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
        sort: {y: "x", reverse: true}
      }),
      Plot.text(latest, {
        y: "country_clean",
        x: "net_impact_index",
        text: d => (d.net_impact_index >= 0 ? "+" : "") + d.net_impact_index.toFixed(2),
        dx: d => d.net_impact_index >= 0 ? 4 : -4,
        textAnchor: d => d.net_impact_index >= 0 ? "start" : "end"
      })
    ]
  });
}
```

## Adoption rate × Net Impact — latest month

Each dot is one of the top ${topN} countries; size encodes respondent count.

```js
{
  const latest = rowsAll.filter(d =>
    `${d.year}-${String(d.month).padStart(2,"0")}` === latestMonth
    && topCountries.includes(d.country_clean)
  );
  return Plot.plot({
    height: 380,
    marginLeft: 60,
    x: {grid: true, label: "AI adoption rate", tickFormat: d => (d*100).toFixed(0)+"%"},
    y: {grid: true, label: "Net Impact Index"},
    marks: [
      Plot.ruleY([0], {stroke: "#999"}),
      Plot.dot(latest, {
        x: "adoption_rate",
        y: "net_impact_index",
        r: d => Math.sqrt(d.n_respondents) / 2,
        fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
        fillOpacity: 0.7,
        stroke: "white"
      }),
      Plot.text(latest, {
        x: "adoption_rate",
        y: "net_impact_index",
        text: "country_clean",
        dy: -12,
        fontSize: 11
      })
    ]
  });
}
```

## Small multiples — Net Impact trend per country

```js
{
  const rows = rowsAll.filter(d => topCountries.includes(d.country_clean));
  return Plot.plot({
    height: 520,
    marginLeft: 40,
    fy: {label: null},
    x: {type: "band", label: null, tickRotate: -30},
    y: {grid: true, domain: [-0.3, 0.7], label: "Net Impact Index"},
    facet: {data: rows, y: "country_clean"},
    marks: [
      Plot.ruleY([0], {stroke: "#bbb"}),
      Plot.lineY(rows, {
        x: d => `${d.year}-${String(d.month).padStart(2,"0")}`,
        y: "net_impact_index",
        stroke: "#1F3A5F",
        strokeWidth: 2
      }),
      Plot.dot(rows, {
        x: d => `${d.year}-${String(d.month).padStart(2,"0")}`,
        y: "net_impact_index",
        fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
        r: 3
      })
    ]
  });
}
```

## All country-months (filterable table)

```js
const search = view(Inputs.search(rowsAll, {placeholder: "Filter countries…"}));
```

```js
Inputs.table(search, {
  columns: ["year", "month", "country_clean", "n_respondents",
            "adoption_rate", "positive_impact_share",
            "negative_impact_share", "net_impact_index"],
  header: {
    country_clean: "Country",
    n_respondents: "N",
    adoption_rate: "Adoption",
    positive_impact_share: "Positive",
    negative_impact_share: "Negative",
    net_impact_index: "Net Impact"
  },
  format: {
    adoption_rate: d => d == null ? "" : (d*100).toFixed(1) + "%",
    positive_impact_share: d => d == null ? "" : (d*100).toFixed(1) + "%",
    negative_impact_share: d => d == null ? "" : (d*100).toFixed(1) + "%",
    net_impact_index: d => d == null ? "" : (d >= 0 ? "+" : "") + d.toFixed(3)
  },
  sort: "net_impact_index",
  reverse: true
})
```
