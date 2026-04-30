---
title: Frequency & impact
---

# Frequency of AI use vs. impact on work

The *dose-response* view: how Net Impact Index varies with how often people use AI. A clean upward slope suggests heavier users report more net-positive impact.

```js
const global  = FileAttachment("data/global.parquet").parquet();
const gender  = FileAttachment("data/gender.parquet").parquet();
const ageBand = FileAttachment("data/age_band.parquet").parquet();
```

```js
// Ordinal frequency labels per tracker/README.md §4.1
const FREQ_LABELS = ["Never", "Rarely", "Monthly", "Weekly", "Daily", "Constantly", "Always"];

// Build long-format dose-response rows from a stratum parquet
function unpackDose(rows, groupKey) {
  const out = [];
  for (const r of rows) {
    if (r.suppressed) continue;
    const dose = typeof r.dose_response === "string"
      ? JSON.parse(r.dose_response)
      : r.dose_response;
    if (!dose) continue;
    for (const [lvl, val] of Object.entries(dose)) {
      if (val == null) continue;
      out.push({
        group: groupKey ? r[groupKey] : "Global",
        year: r.year,
        month: r.month,
        freq_level: Number(lvl),
        freq_label: FREQ_LABELS[Number(lvl)],
        net_impact: val
      });
    }
  }
  return out;
}
```

```js
const months = Array.from(new Set(global.toArray().map(d => `${d.year}-${String(d.month).padStart(2,"0")}`))).sort();
const latestMonth = months[months.length - 1];
```

## Global dose-response — ${latestMonth}

```js
{
  const rows = global.toArray().filter(d =>
    `${d.year}-${String(d.month).padStart(2,"0")}` === latestMonth
  );
  const dose = unpackDose(rows);
  return Plot.plot({
    height: 320,
    marginLeft: 60,
    x: {domain: FREQ_LABELS, label: "AI frequency"},
    y: {grid: true, label: "Net Impact Index", domain: [-0.3, 0.6]},
    marks: [
      Plot.ruleY([0], {stroke: "#999"}),
      Plot.lineY(dose, {x: "freq_label", y: "net_impact", stroke: "#1F3A5F", strokeWidth: 2.5}),
      Plot.dot(dose, {x: "freq_label", y: "net_impact", fill: "#1F3A5F", r: 6}),
      Plot.text(dose, {x: "freq_label", y: "net_impact",
        text: d => (d.net_impact >= 0 ? "+" : "") + d.net_impact.toFixed(2),
        dy: -12, fontSize: 11})
    ]
  });
}
```

<div class="grid grid-cols-2">
<div>

## Dose-response by gender — ${latestMonth}

```js
{
  const rows = gender.toArray().filter(d =>
    `${d.year}-${String(d.month).padStart(2,"0")}` === latestMonth
  );
  const dose = unpackDose(rows, "gender_clean");
  return Plot.plot({
    height: 320,
    marginLeft: 60,
    x: {domain: FREQ_LABELS, label: "AI frequency"},
    y: {grid: true, label: "Net Impact Index"},
    color: {legend: true},
    marks: [
      Plot.ruleY([0], {stroke: "#bbb"}),
      Plot.lineY(dose, {x: "freq_label", y: "net_impact", stroke: "group", strokeWidth: 2}),
      Plot.dot(dose, {x: "freq_label", y: "net_impact", fill: "group", r: 4})
    ]
  });
}
```

</div>
<div>

## Dose-response by age band — ${latestMonth}

```js
{
  const order = ["18-20","21-24","25-34","35-44","45-54","55-64","65-74","75-84","85+"];
  const rows = ageBand.toArray().filter(d =>
    `${d.year}-${String(d.month).padStart(2,"0")}` === latestMonth
  );
  const dose = unpackDose(rows, "age_band");
  return Plot.plot({
    height: 320,
    marginLeft: 60,
    x: {domain: FREQ_LABELS, label: "AI frequency"},
    y: {grid: true, label: "Net Impact Index"},
    color: {legend: true, domain: order},
    marks: [
      Plot.ruleY([0], {stroke: "#bbb"}),
      Plot.lineY(dose, {x: "freq_label", y: "net_impact", stroke: "group", strokeWidth: 2}),
      Plot.dot(dose, {x: "freq_label", y: "net_impact", fill: "group", r: 4})
    ]
  });
}
```

</div>
</div>

## Frequency distribution over time — global

```js
{
  const rows = global.toArray().filter(d => !d.suppressed);
  const long = [];
  for (const r of rows) {
    for (let lvl = 0; lvl <= 6; lvl++) {
      const share = r[`freq_share_${lvl}`];
      if (share == null) continue;
      long.push({
        month: `${r.year}-${String(r.month).padStart(2,"0")}`,
        label: FREQ_LABELS[lvl],
        lvl,
        share
      });
    }
  }
  return Plot.plot({
    height: 320,
    marginLeft: 60,
    y: {grid: true, label: "Share of respondents", tickFormat: d => (d*100).toFixed(0)+"%"},
    x: {type: "band", label: null},
    color: {legend: true, domain: FREQ_LABELS, scheme: "Blues"},
    marks: [
      Plot.barY(long, {
        x: "month",
        y: "share",
        fill: "label",
        order: d => d.lvl,
        tip: true
      })
    ]
  });
}
```
