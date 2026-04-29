"""
Bake a self-contained, single-page AI Use Impact Tracker dashboard.

Layout:
  - Top filter row (month, color-by metric, gender, age band, frequency)
  - 4 KPI cards (weighted impact index, respondents, adoption, impact denom)
  - World choropleth (Observable Plot + topojson, CDN)
  - Country detail card on click

Data layers embedded:
  - global
  - country
  - country_gender
  - country_age_band
  - country_gender_age_band

Filter logic picks the appropriate stratum so every metric shown is the
exact precomputed value (no JS-side aggregation). Frequency filter
overrides color-by to net_impact_index at the chosen ai_freq level via
the dose_response column.

Run AFTER main.py:
    python3 make_dashboard.py

Output: ../dashboard/preview.html
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


HERE = Path(__file__).parent
TRACKER_OUT = HERE / "output" / "v1" / "metrics"
DASHBOARD_DIR = HERE.parent / "dashboard"
OUT_HTML = DASHBOARD_DIR / "preview.html"


KEEP_COLS_BASE = [
    "year", "month",
    "n_respondents", "n_impact_denominator",
    "adoption_rate", "freq_mean",
    "weighted_impact_index", "net_impact_index",
    "positive_impact_share", "negative_impact_share",
    "impact_share_improved_quality", "impact_share_new_opportunities",
    "impact_share_adaptation_pressure", "impact_share_job_anxiety",
    "impact_share_job_loss", "impact_share_reduced_income",
    "impact_share_none", "impact_share_other", "impact_share_not_sure",
    "dose_response",
]

LEVEL_KEYS = {
    "global":                  [],
    "country":                 ["country_clean"],
    "country_gender":          ["country_clean", "gender_clean"],
    "country_age_band":        ["country_clean", "age_band"],
    "country_gender_age_band": ["country_clean", "gender_clean", "age_band"],
}


def load_level(level: str, key_cols: list[str], tracker_out: Path) -> list[dict]:
    files = sorted(tracker_out.glob(f"stratum_level={level}/**/part-0.parquet"))
    if not files:
        print(f"  warning: no files found for level={level}")
        return []
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

    if "suppressed" in df.columns:
        df = df[~df["suppressed"].astype(bool)]

    cols = key_cols + KEEP_COLS_BASE
    df = df[[c for c in cols if c in df.columns]].copy()

    if "dose_response" in df.columns:
        df["dose_response"] = df["dose_response"].apply(
            lambda v: json.loads(v) if isinstance(v, str) else v
        )

    df = df.replace({float("nan"): None})

    records = []
    for r in df.to_dict(orient="records"):
        rec = {}
        for k, v in r.items():
            if v is None:
                rec[k] = None
            elif isinstance(v, float):
                rec[k] = None if math.isnan(v) else v
            elif hasattr(v, "item"):
                rec[k] = v.item()
            else:
                rec[k] = v
        records.append(rec)
    return records


def build_payload(tracker_out: Path) -> str:
    data = {level: load_level(level, keys, tracker_out)
            for level, keys in LEVEL_KEYS.items()}
    for k, v in data.items():
        print(f"  {k:30} rows={len(v):,}")
    return json.dumps(data, separators=(",", ":"))


def main():
    if not TRACKER_OUT.exists():
        raise SystemExit(
            f"No ETL output at {TRACKER_OUT}. Run:\n"
            f"  python3 main.py --source csv --path <your.csv> --out ./output"
        )
    print("Loading Parquet outputs…")
    payload = build_payload(TRACKER_OUT)
    print(f"Embedded JSON size: {len(payload)/1024:.1f} KB")

    html = HTML_TEMPLATE.replace("__DATA_JSON__", payload)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print("Open by double-clicking the file — no server needed.")


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AI Use Impact Tracker</title>
<style>
  :root {
    --ink:#1a1a1a; --muted:#6b7280; --accent:#1F3A5F; --accent2:#2E5C8A;
    --pos:#1a7f4e; --neg:#b3261e; --rule:#e5e7eb; --chip:#E8EEF4;
    --hero:#6366f1;
  }
  * { box-sizing: border-box; }
  html, body { margin:0; background:#f6f7f9; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color:var(--ink); }
  .shell { max-width:1280px; margin:0 auto; padding:28px 36px 60px; }
  header { padding-bottom:18px; border-bottom:1px solid var(--rule); margin-bottom:20px; }
  h1 { color:var(--accent); margin:0 0 4px; font-size:26px; }
  header p { color:var(--muted); margin:0; max-width:780px; font-size:14px; }

  .controls { background:#fff; padding:14px 18px; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); margin-bottom:18px; display:flex; flex-wrap:wrap; gap:18px; align-items:flex-end; }
  .controls .group { display:flex; flex-direction:column; gap:4px; }
  .controls label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; font-weight:600; }
  .controls select, .controls button { padding:6px 10px; border:1px solid var(--rule); border-radius:6px; font-size:14px; background:#fff; color:var(--ink); }
  .controls select { cursor:pointer; min-width:120px; }
  .controls button.icon { padding:6px 10px; line-height:1; cursor:pointer; }
  .controls button.icon:hover { background:var(--chip); }
  .controls .month-row { display:flex; gap:4px; align-items:center; }
  .controls .reset { margin-left:auto; background:transparent; border:none; color:var(--accent2); cursor:pointer; font-size:13px; padding:6px 8px; }
  .controls .reset:hover { text-decoration:underline; }

  .kpi-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-bottom:18px; }
  @media (max-width:900px) { .kpi-grid { grid-template-columns:repeat(2, 1fr); } }
  .card { background:#fff; padding:14px 18px; border-radius:10px; box-shadow:0 1px 2px rgba(0,0,0,0.06); }
  .card .label { font-size:11px; color:var(--muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; }
  .card .value { font-size:28px; font-weight:600; color:var(--accent); line-height:1.1; }
  .card .sub { font-size:12px; color:var(--muted); margin-top:4px; }
  .card.hero { border:2px solid var(--hero); }
  .card.hero .value { color:var(--hero); font-size:32px; }
  .pos { color:var(--pos) !important; } .neg { color:var(--neg) !important; }

  .map-panel { background:#fff; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); padding:18px 18px 14px; }
  .map-header { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px; gap:16px; flex-wrap:wrap; }
  .map-header h3 { margin:0; font-size:15px; color:#333; font-weight:600; }
  .map-meta { font-size:12px; color:var(--muted); }
  #map-container { width:100%; }
  #map-container svg { width:100%; height:auto; max-height:600px; display:block; }
  .legend { display:flex; align-items:center; gap:10px; margin-top:8px; font-size:12px; color:var(--muted); }
  .legend .swatch { width:220px; height:12px; border-radius:3px; border:1px solid var(--rule); }
  .legend .note { margin-left:auto; }

  .country-detail { background:#fff; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); padding:18px; margin-top:18px; display:none; }
  .country-detail.active { display:block; }
  .country-detail h3 { margin:0 0 12px; color:var(--accent); font-size:18px; }
  .country-detail .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; }
  .country-detail .stat .lbl { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; }
  .country-detail .stat .v { font-size:18px; font-weight:600; color:var(--accent); }
  .country-detail .close { float:right; cursor:pointer; color:var(--muted); border:none; background:transparent; font-size:18px; }

  .empty { color:var(--muted); font-style:italic; padding:14px; text-align:center; }
</style>
</head>
<body>
<div class="shell">
  <header>
    <h1>AI Use Impact Tracker</h1>
    <p>Self-reported impact of AI use on work, by country and demographic. Built on the Global Mind Project by Sapien Labs. Cells with fewer than 50 respondents are suppressed.</p>
  </header>

  <div class="controls">
    <div class="group">
      <label>Month</label>
      <div class="month-row">
        <button class="icon" id="prev-month" title="Previous month">◀</button>
        <select id="month-select"></select>
        <button class="icon" id="next-month" title="Next month">▶</button>
      </div>
    </div>
    <div class="group">
      <label>Color map by</label>
      <select id="metric-select">
        <option value="weighted_impact_index">Weighted Impact Index</option>
        <option value="net_impact_index">Net Impact Index</option>
        <option value="adoption_rate">AI Adoption Rate</option>
        <option value="freq_mean">Frequency Mean (0–6)</option>
        <option value="impact_share_improved_quality">Improved Quality (share)</option>
        <option value="impact_share_new_opportunities">New Opportunities (share)</option>
        <option value="impact_share_adaptation_pressure">Adaptation Pressure (share)</option>
        <option value="impact_share_job_anxiety">Job Anxiety (share)</option>
        <option value="impact_share_job_loss">Job Loss (share)</option>
        <option value="impact_share_reduced_income">Reduced Income (share)</option>
      </select>
    </div>
    <div class="group">
      <label>Gender</label>
      <select id="gender-select">
        <option value="">All</option>
        <option>Female</option><option>Male</option><option>Non-binary</option>
        <option>Other/Intersex</option><option>Prefer not to say</option>
      </select>
    </div>
    <div class="group">
      <label>Age band</label>
      <select id="age-select">
        <option value="">All</option>
        <option>18-20</option><option>21-24</option><option>25-34</option>
        <option>35-44</option><option>45-54</option><option>55-64</option>
        <option>65-74</option><option>75-84</option><option>85+</option>
      </select>
    </div>
    <div class="group">
      <label>Frequency</label>
      <select id="freq-select" title="When set, the map switches to net impact index at this AI-use frequency">
        <option value="">All</option>
        <option value="1">Rarely</option>
        <option value="2">Monthly</option>
        <option value="3">Weekly</option>
        <option value="4">Daily</option>
        <option value="5">Constantly</option>
        <option value="6">Always</option>
      </select>
    </div>
    <button class="reset" id="reset-btn">Reset filters</button>
  </div>

  <div class="kpi-grid">
    <div class="card hero">
      <div class="label">Weighted Impact Index</div>
      <div class="value" id="kpi-wii">—</div>
      <div class="sub" id="kpi-wii-sub"></div>
    </div>
    <div class="card">
      <div class="label">Respondents</div>
      <div class="value" id="kpi-n">—</div>
      <div class="sub" id="kpi-n-sub"></div>
    </div>
    <div class="card">
      <div class="label">AI Adoption Rate</div>
      <div class="value" id="kpi-adopt">—</div>
      <div class="sub">share using AI at all</div>
    </div>
    <div class="card">
      <div class="label">Impact Denominator</div>
      <div class="value" id="kpi-denom">—</div>
      <div class="sub">AI users with impact response</div>
    </div>
  </div>

  <div class="map-panel">
    <div class="map-header">
      <h3 id="map-title">World map — Weighted Impact Index</h3>
      <div class="map-meta" id="map-meta"></div>
    </div>
    <div id="map-container"><div class="empty">Loading map…</div></div>
    <div class="legend">
      <span id="legend-min">−1</span>
      <span class="swatch" id="legend-swatch"></span>
      <span id="legend-max">+1</span>
      <span class="note" id="legend-note"></span>
    </div>
  </div>

  <div class="country-detail" id="country-detail">
    <button class="close" id="cd-close" title="Close">×</button>
    <h3 id="cd-name"></h3>
    <div id="cd-body"></div>
  </div>
</div>

<script>const DATA = __DATA_JSON__;</script>
<script type="module">
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import {feature} from "https://cdn.jsdelivr.net/npm/topojson-client@3/+esm";
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

// GMP country name → world-atlas properties.name
const NAME_ALIASES = {
  "United States": "United States of America",
  "USA": "United States of America",
  "U.S.A.": "United States of America",
  "UK": "United Kingdom",
  "Czech Republic": "Czechia",
  "Ivory Coast": "Côte d'Ivoire",
  "Congo (DRC)": "Dem. Rep. Congo",
  "Congo (Kinshasa)": "Dem. Rep. Congo",
  "Bosnia and Herzegovina": "Bosnia and Herz.",
  "Dominican Republic": "Dominican Rep.",
  "Central African Republic": "Central African Rep.",
  "South Sudan": "S. Sudan",
};
const atlasName = n => NAME_ALIASES[n] ?? n;

const METRIC_META = {
  weighted_impact_index: { label:"Weighted Impact Index", domain:[-1,1], scheme:"PiYG", isShare:false, signed:true },
  net_impact_index:      { label:"Net Impact Index",      domain:[-1,1], scheme:"PiYG", isShare:false, signed:true },
  adoption_rate:         { label:"AI Adoption Rate",      domain:[0,1],  scheme:"Blues", isShare:true,  signed:false },
  freq_mean:             { label:"Frequency Mean",        domain:[0,6],  scheme:"Blues", isShare:false, signed:false },
  impact_share_improved_quality:    { label:"Improved Quality (share)",    domain:[0,1], scheme:"Greens", isShare:true, signed:false },
  impact_share_new_opportunities:   { label:"New Opportunities (share)",   domain:[0,1], scheme:"Greens", isShare:true, signed:false },
  impact_share_adaptation_pressure: { label:"Adaptation Pressure (share)", domain:[0,1], scheme:"Reds",   isShare:true, signed:false },
  impact_share_job_anxiety:         { label:"Job Anxiety (share)",         domain:[0,1], scheme:"Reds",   isShare:true, signed:false },
  impact_share_job_loss:            { label:"Job Loss (share)",            domain:[0,1], scheme:"Reds",   isShare:true, signed:false },
  impact_share_reduced_income:      { label:"Reduced Income (share)",      domain:[0,1], scheme:"Reds",   isShare:true, signed:false },
};

const $ = id => document.getElementById(id);
const monthSel = $("month-select"), metricSel = $("metric-select");
const genderSel = $("gender-select"), ageSel = $("age-select"), freqSel = $("freq-select");
const prevBtn = $("prev-month"), nextBtn = $("next-month"), resetBtn = $("reset-btn");

// Months
const months = [...new Set(DATA.global.map(r => `${r.year}-${String(r.month).padStart(2,"0")}`))].sort();
months.forEach(m => {
  const [y, mo] = m.split("-");
  const opt = document.createElement("option");
  opt.value = m;
  opt.textContent = new Date(+y, +mo - 1, 1).toLocaleDateString("en", {month:"short", year:"2-digit"});
  monthSel.appendChild(opt);
});
monthSel.value = months[months.length - 1];

prevBtn.addEventListener("click", () => {
  const i = months.indexOf(monthSel.value);
  if (i > 0) { monthSel.value = months[i-1]; render(); }
});
nextBtn.addEventListener("click", () => {
  const i = months.indexOf(monthSel.value);
  if (i < months.length - 1) { monthSel.value = months[i+1]; render(); }
});
resetBtn.addEventListener("click", () => {
  metricSel.value = "weighted_impact_index";
  genderSel.value = ""; ageSel.value = ""; freqSel.value = "";
  hideDetail(); render();
});

// World atlas
let countriesGeo;
try {
  const world = await d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json");
  countriesGeo = feature(world, world.objects.countries);
} catch (e) {
  $("map-container").innerHTML = '<div class="empty">Could not load world map atlas. Check internet connection.</div>';
}

// Pick the right precomputed stratum based on filters
function pickStratum() {
  const g = genderSel.value, a = ageSel.value;
  if (g && a) return { rows: DATA.country_gender_age_band, gender: g, age: a };
  if (g)      return { rows: DATA.country_gender,          gender: g, age: null };
  if (a)      return { rows: DATA.country_age_band,        gender: null, age: a };
  return { rows: DATA.country, gender: null, age: null };
}

function currentRows() {
  const [y, m] = monthSel.value.split("-").map(Number);
  const { rows, gender, age } = pickStratum();
  return rows.filter(r => {
    if (r.year !== y || r.month !== m) return false;
    if (gender && r.gender_clean !== gender) return false;
    if (age && r.age_band !== age) return false;
    return true;
  });
}

function activeMetricMeta() {
  if (freqSel.value !== "") {
    return { label:`Net Impact at "${freqSel.options[freqSel.selectedIndex].textContent}" use`, domain:[-1,1], scheme:"PiYG", isShare:false, signed:true, freqMode:true };
  }
  return METRIC_META[metricSel.value];
}

function metricForRow(r) {
  const f = freqSel.value;
  if (f !== "") return r.dose_response ? (r.dose_response[f] ?? null) : null;
  return r[metricSel.value] ?? null;
}

// Filter summary string
function filterSummary() {
  const parts = [monthSel.options[monthSel.selectedIndex].textContent];
  if (genderSel.value) parts.push(genderSel.value);
  if (ageSel.value) parts.push("Age " + ageSel.value);
  if (freqSel.value !== "") parts.push("Freq: " + freqSel.options[freqSel.selectedIndex].textContent);
  return parts.join(" · ");
}

const fmtSigned = v => v == null ? "—" : (v >= 0 ? "+" : "") + v.toFixed(3);
const fmtPct = v => v == null ? "—" : (v * 100).toFixed(1) + "%";
const fmtNum = v => v == null ? "—" : v.toLocaleString();
const fmtMetric = (v, meta) => v == null ? "—" : meta.isShare ? fmtPct(v) : meta.signed ? fmtSigned(v) : v.toFixed(2);

// KPIs
function renderKPIs() {
  const rows = currentRows();
  const totalN = rows.reduce((s, r) => s + (r.n_respondents || 0), 0);
  const totalDenom = rows.reduce((s, r) => s + (r.n_impact_denominator || 0), 0);
  const wmean = (field, weightField) => {
    let num = 0, den = 0;
    for (const r of rows) {
      const v = r[field], w = r[weightField] || 0;
      if (v != null && w > 0) { num += v * w; den += w; }
    }
    return den > 0 ? num / den : null;
  };
  const wii = wmean("weighted_impact_index", "n_impact_denominator");
  const adopt = wmean("adoption_rate", "n_respondents");

  const wiiEl = $("kpi-wii");
  wiiEl.textContent = fmtSigned(wii);
  wiiEl.classList.remove("pos", "neg");
  if (wii != null && wii > 0) wiiEl.classList.add("pos");
  if (wii != null && wii < 0) wiiEl.classList.add("neg");

  $("kpi-wii-sub").textContent = filterSummary();
  $("kpi-n").textContent = fmtNum(totalN);
  $("kpi-n-sub").textContent = filterSummary();
  $("kpi-adopt").textContent = fmtPct(adopt);
  $("kpi-denom").textContent = fmtNum(totalDenom);
}

// Domain fit: stretch the color scale to the actual visible range so the
// map doesn't wash out when values cluster near zero. Use a small floor
// so single-country views or tight clusters still show some contrast.
function fitDomain(values, meta) {
  const finite = values.filter(v => Number.isFinite(v));
  if (finite.length === 0) return meta.domain;
  // Use 2nd/98th percentiles to ignore lone outliers.
  const sorted = finite.slice().sort((a, b) => a - b);
  const q = p => sorted[Math.min(sorted.length - 1, Math.max(0, Math.floor(p * (sorted.length - 1))))];
  const lo = q(0.02), hi = q(0.98);
  if (meta.signed) {
    const a = Math.max(Math.abs(lo), Math.abs(hi), 0.05);
    return [-a, a];
  }
  if (meta.isShare) {
    return [Math.max(0, lo - 0.02), Math.max(hi, lo + 0.05, 0.1)];
  }
  // Unsigned numeric (freq_mean)
  const pad = Math.max((hi - lo) * 0.1, 0.1);
  return [Math.max(meta.domain[0], lo - pad), Math.min(meta.domain[1], hi + pad)];
}

// Map
function renderMap() {
  if (!countriesGeo) return;
  const rows = currentRows();
  const meta = activeMetricMeta();

  const valueByName = {};
  const rowByName = {};
  for (const r of rows) {
    if (!r.country_clean) continue;
    const v = metricForRow(r);
    if (v == null) continue;
    const key = atlasName(r.country_clean);
    valueByName[key] = v;
    rowByName[key] = r;
  }

  const fitted = fitDomain(Object.values(valueByName), meta);
  const fmt = v => fmtMetric(v, meta);

  const plot = Plot.plot({
    projection: "equal-earth",
    width: 1200,
    height: 540,
    margin: 0,
    color: { type: "linear", scheme: meta.scheme, domain: fitted, clamp: true, unknown: "#e5e7eb" },
    marks: [
      Plot.geo(countriesGeo, {
        fill: d => valueByName[d.properties.name],
        stroke: "#ffffff",
        strokeWidth: 0.4,
        title: d => {
          const v = valueByName[d.properties.name];
          if (v == null) return `${d.properties.name}\n(no data / suppressed)`;
          const r = rowByName[d.properties.name];
          return `${d.properties.name}\n${meta.label}: ${fmt(v)}\nn=${(r?.n_respondents ?? "?").toLocaleString?.() ?? r?.n_respondents}`;
        },
        tip: true,
      }),
    ],
  });

  // Click handler on country paths
  plot.querySelectorAll("path").forEach((p, i) => {
    p.style.cursor = "pointer";
    p.addEventListener("click", () => {
      const f = countriesGeo.features[i];
      if (!f) return;
      const name = f.properties.name;
      showDetail(name, rowByName[name]);
    });
  });

  const c = $("map-container");
  c.innerHTML = "";
  c.appendChild(plot);

  $("map-title").textContent = "World map — " + meta.label;
  $("map-meta").textContent = `${rows.length.toLocaleString()} country rows · cells under n=50 are suppressed`;

  // Legend — labels reflect the fitted domain
  const fmtBound = v => meta.isShare ? (v * 100).toFixed(0) + "%" : meta.signed ? (v >= 0 ? "+" : "") + v.toFixed(2) : v.toFixed(2);
  $("legend-min").textContent = fmtBound(fitted[0]);
  $("legend-max").textContent = fmtBound(fitted[1]);
  const interp = d3[`interpolate${meta.scheme}`];
  if (interp) {
    const stops = Array.from({length: 11}, (_, i) => interp(i / 10));
    $("legend-swatch").style.background = `linear-gradient(to right, ${stops.join(",")})`;
  }
  $("legend-note").textContent = `${Object.keys(valueByName).length} countries shown · ${filterSummary()}`;
}

// Country detail
function hideDetail() {
  $("country-detail").classList.remove("active");
}
$("cd-close").addEventListener("click", hideDetail);

function showDetail(name, row) {
  const el = $("country-detail");
  $("cd-name").textContent = name;
  if (!row) {
    $("cd-body").innerHTML = '<div class="empty">No data for this country under the current filters.</div>';
    el.classList.add("active");
    el.scrollIntoView({behavior: "smooth", block: "nearest"});
    return;
  }
  const stats = [
    ["Respondents", fmtNum(row.n_respondents)],
    ["Impact denom", fmtNum(row.n_impact_denominator)],
    ["Adoption rate", fmtPct(row.adoption_rate)],
    ["Frequency mean", row.freq_mean == null ? "—" : row.freq_mean.toFixed(2)],
    ["Weighted impact", fmtSigned(row.weighted_impact_index)],
    ["Net impact", fmtSigned(row.net_impact_index)],
    ["Improved quality", fmtPct(row.impact_share_improved_quality)],
    ["New opportunities", fmtPct(row.impact_share_new_opportunities)],
    ["Adaptation pressure", fmtPct(row.impact_share_adaptation_pressure)],
    ["Job anxiety", fmtPct(row.impact_share_job_anxiety)],
    ["Job loss", fmtPct(row.impact_share_job_loss)],
    ["Reduced income", fmtPct(row.impact_share_reduced_income)],
  ];
  let html = '<div class="grid">';
  for (const [lbl, v] of stats) html += `<div class="stat"><div class="lbl">${lbl}</div><div class="v">${v}</div></div>`;
  html += '</div>';

  if (row.dose_response) {
    const dr = row.dose_response;
    const labels = {1:"Rarely",2:"Monthly",3:"Weekly",4:"Daily",5:"Constantly",6:"Always"};
    const items = [];
    for (const k of [1,2,3,4,5,6]) {
      const v = dr[k];
      if (v != null) items.push(`<span style="display:inline-block;margin-right:14px;font-size:13px;color:var(--muted)">${labels[k]}: <strong style="color:${v>0?"var(--pos)":v<0?"var(--neg)":"var(--accent)"}">${fmtSigned(v)}</strong></span>`);
    }
    if (items.length) html += `<div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--rule)"><div class="lbl" style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">Dose-response (net impact by AI-use frequency)</div>${items.join("")}</div>`;
  }
  $("cd-body").innerHTML = html;
  el.classList.add("active");
  el.scrollIntoView({behavior: "smooth", block: "nearest"});
}

function render() {
  renderKPIs();
  renderMap();
}

[metricSel, genderSel, ageSel, freqSel, monthSel].forEach(el => el.addEventListener("change", render));
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
