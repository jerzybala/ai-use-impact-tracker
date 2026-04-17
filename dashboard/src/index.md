---
title: AI Use Impact Tracker — Overview
---

# AI Use Impact Tracker

How frequency of AI use relates to self-reported impact on work — tracked monthly across countries, gender, and age. Built on the Global Mind Project by Sapien Labs.

```js
const global = FileAttachment("data/global.parquet").parquet();
const gender = FileAttachment("data/gender.parquet").parquet();
const ageBand = FileAttachment("data/age_band.parquet").parquet();
```

```js
// Latest month
const latest = global.toArray()
  .filter(d => !d.suppressed)
  .sort((a, b) => (b.year - a.year) || (b.month - a.month))[0];
```

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Respondents (latest month)</h2>
    <span class="big">${latest ? latest.n_respondents.toLocaleString() : "—"}</span>
    <small>${latest ? `${latest.year}-${String(latest.month).padStart(2,"0")}` : ""}</small>
  </div>
  <div class="card">
    <h2>AI adoption rate</h2>
    <span class="big">${latest ? (latest.adoption_rate * 100).toFixed(1) + "%" : "—"}</span>
    <small>share using AI at all</small>
  </div>
  <div class="card">
    <h2>Positive-impact share</h2>
    <span class="big">${latest ? (latest.positive_impact_share * 100).toFixed(1) + "%" : "—"}</span>
    <small>quality ↑ or new opportunities</small>
  </div>
  <div class="card">
    <h2>Net Impact Index</h2>
    <span class="big" style="color:${latest && latest.net_impact_index > 0 ? '#1a7f4e' : '#b3261e'}">
      ${latest ? (latest.net_impact_index >= 0 ? "+" : "") + latest.net_impact_index.toFixed(3) : "—"}
    </span>
    <small>positive − negative share, range [−1, 1]</small>
  </div>
</div>

## Net Impact Index over time — global

```js
Plot.plot({
  height: 320,
  marginLeft: 60,
  y: {label: "Net Impact Index", grid: true, domain: [-0.5, 0.5]},
  x: {type: "band", label: null},
  marks: [
    Plot.ruleY([0], {stroke: "#999"}),
    Plot.areaY(global.toArray().filter(d => !d.suppressed), {
      x: d => `${d.year}-${String(d.month).padStart(2,"0")}`,
      y1: "net_impact_index",
      y2: 0,
      fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
      fillOpacity: 0.18
    }),
    Plot.lineY(global.toArray().filter(d => !d.suppressed), {
      x: d => `${d.year}-${String(d.month).padStart(2,"0")}`,
      y: "net_impact_index",
      stroke: "#1F3A5F",
      strokeWidth: 2.5
    }),
    Plot.dot(global.toArray().filter(d => !d.suppressed), {
      x: d => `${d.year}-${String(d.month).padStart(2,"0")}`,
      y: "net_impact_index",
      fill: "#1F3A5F",
      r: 5
    })
  ]
})
```

<div class="grid grid-cols-2">
  <div>

## AI adoption rate — global

```js
Plot.plot({
  height: 260,
  y: {label: "% using AI at all", grid: true, tickFormat: d => (d*100).toFixed(0)+"%", domain: [0,1]},
  x: {type: "band", label: null},
  marks: [
    Plot.barY(global.toArray().filter(d => !d.suppressed), {
      x: d => `${d.year}-${String(d.month).padStart(2,"0")}`,
      y: "adoption_rate",
      fill: "#2E5C8A"
    })
  ]
})
```

  </div>
  <div>

## Impact share composition — latest month

```js
{
  const row = latest || {};
  const data = [
    {label: "Improved quality",    share: row.impact_share_improved_quality,    cat: "positive"},
    {label: "New opportunities",   share: row.impact_share_new_opportunities,   cat: "positive"},
    {label: "Adaptation pressure", share: row.impact_share_adaptation_pressure, cat: "negative"},
    {label: "Job anxiety",         share: row.impact_share_job_anxiety,         cat: "negative"},
    {label: "No impact",           share: row.impact_share_none,                cat: "neutral"},
    {label: "Other",               share: row.impact_share_other,               cat: "neutral"},
    {label: "Not sure",            share: row.impact_share_not_sure,            cat: "neutral"}
  ].filter(d => d.share != null);
  return Plot.plot({
    height: 260,
    marginLeft: 140,
    x: {grid: true, tickFormat: d => (d*100).toFixed(0)+"%", label: "% of AI users reporting"},
    marks: [
      Plot.barX(data, {
        y: "label",
        x: "share",
        fill: d => d.cat === "positive" ? "#1a7f4e" : d.cat === "negative" ? "#b3261e" : "#888",
        sort: {y: "x", reverse: true}
      }),
      Plot.text(data, {y: "label", x: "share",
        text: d => (d.share*100).toFixed(1)+"%",
        textAnchor: "start", dx: 4})
    ]
  });
}
```

  </div>
</div>

## Net Impact Index by gender and age band — latest month

<div class="grid grid-cols-2">
  <div>

```js
{
  const rows = gender.toArray().filter(d => !d.suppressed
    && d.year === latest?.year && d.month === latest?.month);
  return Plot.plot({
    height: 260,
    marginLeft: 100,
    x: {grid: true, label: "Net Impact Index", domain: [-0.5, 0.5]},
    marks: [
      Plot.ruleX([0], {stroke: "#999"}),
      Plot.barX(rows, {
        y: "gender_clean",
        x: "net_impact_index",
        fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
        sort: {y: "x"}
      })
    ]
  });
}
```

  </div>
  <div>

```js
{
  const order = ["18-20","21-24","25-34","35-44","45-54","55-64","65-74","75-84","85+"];
  const rows = ageBand.toArray().filter(d => !d.suppressed
    && d.year === latest?.year && d.month === latest?.month);
  return Plot.plot({
    height: 260,
    marginLeft: 60,
    x: {grid: true, label: "Net Impact Index", domain: [-0.5, 0.5]},
    y: {domain: order},
    marks: [
      Plot.ruleX([0], {stroke: "#999"}),
      Plot.barX(rows, {
        y: "age_band",
        x: "net_impact_index",
        fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e"
      })
    ]
  });
}
```

  </div>
</div>

<style>
.big { font-size: 2.2em; font-weight: 600; display: block; margin: 6px 0 2px; }
.card small { color: #777; }
.card h2 { font-size: 14px; color: #555; margin: 0 0 4px; font-weight: 500; }
</style>
