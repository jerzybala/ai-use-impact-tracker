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
  .legend { display:flex; align-items:flex-start; gap:10px; margin-top:8px; font-size:12px; color:var(--muted); }
  .legend .bar-wrap { display:flex; flex-direction:column; gap:2px; }
  .legend .swatch { width:380px; height:12px; border-radius:3px; border:1px solid var(--rule); }
  .legend .ticks { display:flex; justify-content:space-between; width:380px; padding:0 1px; font-size:10px; color:var(--muted); white-space:nowrap; }
  .legend .ticks span { transform:translateX(-50%); }
  .legend .ticks span:first-child { transform:none; }
  .legend .ticks span:last-child { transform:translateX(-100%); }
  .legend .note { margin-left:auto; align-self:center; }

  .ts-panel { background:#fff; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); padding:18px; margin-top:18px; display:none; }
  .ts-panel.active { display:block; }
  .ts-panel h3 { margin:0 0 10px; font-size:15px; color:#333; font-weight:600; }
  .ts-panel .ts-meta { font-size:12px; color:var(--muted); margin-bottom:8px; }
  .ts-chart svg { width:100%; height:auto; max-height:260px; display:block; }
  .ts-chart-detail svg { width:100%; height:auto; max-height:200px; display:block; }
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
      <label>Period</label>
      <select id="window-select" title="Pool the selected month with prior months (weighted by respondent count)">
        <option value="1">Single month</option>
        <option value="6">Last 6 months</option>
        <option value="12">Last 12 months</option>
      </select>
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
      <div class="bar-wrap">
        <span class="swatch" id="legend-swatch"></span>
        <div class="ticks" id="legend-ticks"></div>
      </div>
      <span id="legend-max">+1</span>
      <span class="note" id="legend-note"></span>
    </div>
  </div>

  <div class="ts-panel" id="ts-panel">
    <h3 id="ts-title">Trend over time</h3>
    <div class="ts-meta" id="ts-meta"></div>
    <div class="ts-chart" id="ts-chart"></div>
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

// GMP country name → world-atlas properties.name (Natural Earth 110m).
// The atlas uses abbreviated forms ("Dem. Rep. Congo", "Bosnia and Herz.")
// and a few non-obvious renderings ("Czechia", "eSwatini", "Türkiye").
const NAME_ALIASES = {
  // Anglo / common Latin variants
  "United States": "United States of America",
  "USA": "United States of America",
  "U.S.A.": "United States of America",
  "U.S.": "United States of America",
  "US": "United States of America",
  "UK": "United Kingdom",
  "U.K.": "United Kingdom",
  "Great Britain": "United Kingdom",
  "Britain": "United Kingdom",
  "Russian Federation": "Russia",
  "Republic of Korea": "South Korea",
  "Korea, South": "South Korea",
  "Korea (South)": "South Korea",
  "Korea, Republic of": "South Korea",
  "Democratic People's Republic of Korea": "North Korea",
  "Korea, North": "North Korea",
  "DPRK": "North Korea",
  "Iran, Islamic Republic of": "Iran",
  "Iran (Islamic Republic of)": "Iran",
  "Syrian Arab Republic": "Syria",
  "Lao People's Democratic Republic": "Laos",
  "Lao PDR": "Laos",
  "Viet Nam": "Vietnam",
  "Burma": "Myanmar",
  "Myanmar (Burma)": "Myanmar",
  "Brunei Darussalam": "Brunei",
  "Republic of Moldova": "Moldova",
  "Moldova, Republic of": "Moldova",
  "Bolivia (Plurinational State of)": "Bolivia",
  "Venezuela, Bolivarian Republic of": "Venezuela",
  "Venezuela (Bolivarian Republic of)": "Venezuela",
  "Tanzania, United Republic of": "Tanzania",
  "United Republic of Tanzania": "Tanzania",
  "Palestinian Territory": "Palestine",
  "Palestine, State of": "Palestine",
  "Hong Kong SAR": "Hong Kong",
  "Hong Kong, China": "Hong Kong",
  "Macao SAR": "Macao",
  "Taiwan, Province of China": "Taiwan",

  // Atlas uses abbreviated forms
  "Czech Republic": "Czechia",
  "Czechoslovakia": "Czechia",
  "Macedonia": "North Macedonia",
  "Republic of Macedonia": "North Macedonia",
  "Macedonia, Republic of": "North Macedonia",
  "FYR Macedonia": "North Macedonia",
  "Swaziland": "eSwatini",
  "Eswatini": "eSwatini",
  "Cape Verde": "Cabo Verde",
  "East Timor": "Timor-Leste",
  "Timor": "Timor-Leste",
  "Turkey": "Türkiye",
  "Turkiye": "Türkiye",
  "Ivory Coast": "Côte d'Ivoire",
  "Cote d'Ivoire": "Côte d'Ivoire",
  "Congo, Democratic Republic of the": "Dem. Rep. Congo",
  "Democratic Republic of the Congo": "Dem. Rep. Congo",
  "DR Congo": "Dem. Rep. Congo",
  "DRC": "Dem. Rep. Congo",
  "Congo (DRC)": "Dem. Rep. Congo",
  "Congo (Kinshasa)": "Dem. Rep. Congo",
  "Congo, Republic of the": "Republic of the Congo",
  "Congo (Brazzaville)": "Republic of the Congo",
  "Congo": "Republic of the Congo",
  "Bosnia and Herzegovina": "Bosnia and Herz.",
  "Dominican Republic": "Dominican Rep.",
  "Central African Republic": "Central African Rep.",
  "South Sudan": "S. Sudan",
  "Equatorial Guinea": "Eq. Guinea",
  "Solomon Islands": "Solomon Is.",
  "Falkland Islands": "Falkland Is.",
  "Western Sahara": "W. Sahara",
  "Saint Kitts and Nevis": "St. Kitts and Nevis",
  "Saint Vincent and the Grenadines": "St. Vin. and Gren.",
  "Saint Lucia": "Saint Lucia",
  "Antigua and Barbuda": "Antigua and Barb.",
  "Sao Tome and Principe": "São Tomé and Principe",
  "São Tomé and Príncipe": "São Tomé and Principe",
};
const atlasName = n => NAME_ALIASES[n] ?? n;

// Domains chosen so the visible color spread reflects realistic between-country
// variation; outliers are clamped (color.clamp:true) instead of stretching the
// scale. The static [-1,1] / [0,1] bounds left almost everything washed out.
const METRIC_META = {
  weighted_impact_index: { label:"Weighted Impact Index", domain:[-0.3, 0.3], scheme:"PiYG",   isShare:false, signed:true  },
  net_impact_index:      { label:"Net Impact Index",      domain:[-0.5, 0.5], scheme:"PiYG",   isShare:false, signed:true  },
  adoption_rate:         { label:"AI Adoption Rate",      domain:[0, 1],      scheme:"Blues",  isShare:true,  signed:false },
  freq_mean:             { label:"Frequency Mean",        domain:[0, 6],      scheme:"Blues",  isShare:false, signed:false, freqOrdinal:true },
  impact_share_improved_quality:    { label:"Improved Quality (share)",    domain:[0, 0.6],  scheme:"Greens", isShare:true, signed:false },
  impact_share_new_opportunities:   { label:"New Opportunities (share)",   domain:[0, 0.4],  scheme:"Greens", isShare:true, signed:false },
  impact_share_adaptation_pressure: { label:"Adaptation Pressure (share)", domain:[0, 0.6],  scheme:"Reds",   isShare:true, signed:false },
  impact_share_job_anxiety:         { label:"Job Anxiety (share)",         domain:[0, 0.6],  scheme:"Reds",   isShare:true, signed:false },
  impact_share_job_loss:            { label:"Job Loss (share)",            domain:[0, 0.15], scheme:"Reds",   isShare:true, signed:false },
  impact_share_reduced_income:      { label:"Reduced Income (share)",      domain:[0, 0.2],  scheme:"Reds",   isShare:true, signed:false },
};

const $ = id => document.getElementById(id);
const monthSel = $("month-select"), metricSel = $("metric-select");
const genderSel = $("gender-select"), ageSel = $("age-select"), freqSel = $("freq-select");
const winSel = $("window-select");
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
  if (i > 0) { monthSel.value = months[i-1]; hideDetail(); render(); }
});
nextBtn.addEventListener("click", () => {
  const i = months.indexOf(monthSel.value);
  if (i < months.length - 1) { monthSel.value = months[i+1]; hideDetail(); render(); }
});
resetBtn.addEventListener("click", () => {
  metricSel.value = "weighted_impact_index";
  genderSel.value = ""; ageSel.value = ""; freqSel.value = "";
  winSel.value = "1";
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

// The set of (year-month) keys covered by the current Period selection.
function selectedMonths() {
  const w = +winSel.value || 1;
  const i = months.indexOf(monthSel.value);
  if (i < 0) return new Set([monthSel.value]);
  const start = Math.max(0, i - w + 1);
  return new Set(months.slice(start, i + 1));
}

// Pool rows by (country, gender, age) using respondent-count weights.
// adoption_rate and freq_mean weight by n_respondents; impact metrics
// (and dose_response levels) weight by n_impact_denominator.
const POOL_FIELDS = {
  adoption_rate: "n_respondents",
  freq_mean: "n_respondents",
  weighted_impact_index: "n_impact_denominator",
  net_impact_index: "n_impact_denominator",
  positive_impact_share: "n_impact_denominator",
  negative_impact_share: "n_impact_denominator",
  impact_share_improved_quality: "n_impact_denominator",
  impact_share_new_opportunities: "n_impact_denominator",
  impact_share_adaptation_pressure: "n_impact_denominator",
  impact_share_job_anxiety: "n_impact_denominator",
  impact_share_job_loss: "n_impact_denominator",
  impact_share_reduced_income: "n_impact_denominator",
  impact_share_none: "n_impact_denominator",
  impact_share_other: "n_impact_denominator",
  impact_share_not_sure: "n_impact_denominator",
};

function poolByCountry(rs) {
  const groups = new Map();
  for (const r of rs) {
    const key = `${r.country_clean ?? ""}|${r.gender_clean ?? ""}|${r.age_band ?? ""}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }
  const out = [];
  for (const [, rows] of groups) {
    const head = rows[0];
    const o = {
      country_clean: head.country_clean,
      gender_clean: head.gender_clean,
      age_band: head.age_band,
      n_respondents: rows.reduce((s, r) => s + (r.n_respondents || 0), 0),
      n_impact_denominator: rows.reduce((s, r) => s + (r.n_impact_denominator || 0), 0),
    };
    for (const [f, wf] of Object.entries(POOL_FIELDS)) {
      let num = 0, den = 0;
      for (const r of rows) {
        const v = r[f], wt = r[wf] || 0;
        if (v != null && wt > 0) { num += v * wt; den += wt; }
      }
      o[f] = den > 0 ? num / den : null;
    }
    o.dose_response = {};
    for (const lvl of [1,2,3,4,5,6]) {
      let num = 0, den = 0;
      for (const r of rows) {
        const v = r.dose_response?.[lvl];
        const wt = r.n_impact_denominator || 0;
        if (v != null && wt > 0) { num += v * wt; den += wt; }
      }
      o.dose_response[lvl] = den > 0 ? num / den : null;
    }
    out.push(o);
  }
  return out;
}

function currentRows() {
  const sel = selectedMonths();
  const { rows, gender, age } = pickStratum();
  const filtered = rows.filter(r => {
    const ym = `${r.year}-${String(r.month).padStart(2,"0")}`;
    if (!sel.has(ym)) return false;
    if (gender && r.gender_clean !== gender) return false;
    if (age && r.age_band !== age) return false;
    return true;
  });
  return sel.size > 1 ? poolByCountry(filtered) : filtered;
}

// Same selection as currentRows() but never pooled — used for time series.
function windowRowsRaw() {
  const sel = selectedMonths();
  const { rows, gender, age } = pickStratum();
  return rows.filter(r => {
    const ym = `${r.year}-${String(r.month).padStart(2,"0")}`;
    if (!sel.has(ym)) return false;
    if (gender && r.gender_clean !== gender) return false;
    if (age && r.age_band !== age) return false;
    return true;
  });
}

function ymKey(r) { return `${r.year}-${String(r.month).padStart(2,"0")}`; }
function ymToDate(ym) { const [y, m] = ym.split("-").map(Number); return new Date(y, m - 1, 1); }

// Per-month weighted aggregate of the active metric across the given rows.
function monthlySeries(rows) {
  const isVolume = !freqSel.value && (metricSel.value === "adoption_rate" || metricSel.value === "freq_mean");
  const weightField = isVolume ? "n_respondents" : "n_impact_denominator";
  const byMonth = new Map();
  for (const r of rows) {
    const k = ymKey(r);
    if (!byMonth.has(k)) byMonth.set(k, []);
    byMonth.get(k).push(r);
  }
  const out = [];
  for (const [ym, rs] of byMonth) {
    let num = 0, den = 0;
    for (const r of rs) {
      const v = metricForRow(r);
      const w = r[weightField] || 0;
      if (v != null && w > 0) { num += v * w; den += w; }
    }
    if (den > 0) out.push({ ym, date: ymToDate(ym), value: num / den });
  }
  out.sort((a, b) => a.date - b.date);
  return out;
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
function periodLabel() {
  const sel = [...selectedMonths()].sort();
  if (sel.length <= 1) return monthSel.options[monthSel.selectedIndex].textContent;
  const fmt = ym => {
    const [y, m] = ym.split("-").map(Number);
    return new Date(y, m - 1, 1).toLocaleDateString("en", {month: "short", year: "2-digit"});
  };
  return `${fmt(sel[0])} – ${fmt(sel[sel.length - 1])}`;
}
function filterSummary() {
  const parts = [periodLabel()];
  if (genderSel.value) parts.push(genderSel.value);
  if (ageSel.value) parts.push("Age " + ageSel.value);
  if (freqSel.value !== "") parts.push("Freq: " + freqSel.options[freqSel.selectedIndex].textContent);
  return parts.join(" · ");
}

const FREQ_LABELS = ["Never", "Rarely", "Monthly", "Weekly", "Daily", "Constantly", "Always"];
const freqOrdinal = v => v == null ? null : FREQ_LABELS[Math.max(0, Math.min(6, Math.round(v)))];

const fmtSigned = v => v == null ? "—" : (v >= 0 ? "+" : "") + v.toFixed(3);
const fmtPct = v => v == null ? "—" : (v * 100).toFixed(1) + "%";
const fmtNum = v => v == null ? "—" : v.toLocaleString();
const fmtFreqMean = v => v == null ? "—" : `${v.toFixed(2)} (${freqOrdinal(v)})`;
const fmtMetric = (v, meta) => {
  if (v == null) return "—";
  if (meta.isShare) return fmtPct(v);
  if (meta.signed) return fmtSigned(v);
  if (meta.freqOrdinal) return fmtFreqMean(v);
  return v.toFixed(2);
};

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

// Build an intensified interpolator: skip the near-white tail of the
// scheme so even the lowest data values render as a recognisable color
// (instead of blending with the gray "no data" fill).
function makeInterp(meta) {
  const base = d3[`interpolate${meta.scheme}`];
  if (!base) return null;
  if (meta.signed) {
    // Diverging: pull both ends toward saturated; middle stays light but not pure white.
    return t => base(t <= 0.5
      ? 0.04 + (0.5 - 0.04) * (t / 0.5)
      : 0.5 + (0.96 - 0.5) * ((t - 0.5) / 0.5));
  }
  // Sequential: start at 22% of the scheme so low values aren't white.
  return t => base(0.22 + 0.74 * t);
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

  const fmt = v => fmtMetric(v, meta);
  const interp = makeInterp(meta);
  const colorOpts = interp
    ? { type: "linear", interpolate: interp, domain: meta.domain, clamp: true, unknown: "#cbd5e1" }
    : { type: "linear", scheme: meta.scheme, domain: meta.domain, clamp: true, unknown: "#cbd5e1" };

  const plot = Plot.plot({
    projection: "equal-earth",
    width: 1200,
    height: 540,
    margin: 0,
    color: colorOpts,
    marks: [
      // Sphere outline so the globe is visible even when most countries lack data.
      Plot.sphere({ stroke: "#94a3b8", strokeWidth: 0.5, fill: "#ffffff" }),
      Plot.geo(countriesGeo, {
        fill: d => valueByName[d.properties.name],
        stroke: "#64748b",
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

  // Click handler on country paths.
  // Plot.geo creates a <g> containing one <path> per feature; Plot.sphere
  // creates a separate <g> with a single path. We need to attach clicks
  // only to the country paths and map each one to the correct feature.
  // Plot 0.6 binds the integer index (not the feature object) to each
  // path's __data__, so we identify the country group as the <g> with
  // the most direct <path> children, then iterate its paths in order
  // — which matches countriesGeo.features 1-to-1.
  const allGroups = [...plot.querySelectorAll("g")];
  let countryGroup = null, maxPaths = 0;
  for (const g of allGroups) {
    const n = g.querySelectorAll(":scope > path").length;
    if (n > maxPaths) { maxPaths = n; countryGroup = g; }
  }
  if (countryGroup) {
    countryGroup.querySelectorAll(":scope > path").forEach((p, i) => {
      const f = countriesGeo.features[i];
      if (!f || !f.properties || !f.properties.name) return;
      p.style.cursor = "pointer";
      p.addEventListener("click", () => {
        const name = f.properties.name;
        showDetail(name, rowByName[name]);
      });
    });
  }

  const c = $("map-container");
  c.innerHTML = "";
  c.appendChild(plot);

  $("map-title").textContent = "World map — " + meta.label;
  $("map-meta").textContent = `${rows.length.toLocaleString()} country rows · cells under n=50 are suppressed`;

  // Legend — labels reflect the active domain (with clamp).
  // For Frequency Mean, show all 7 ordinal labels under the swatch and
  // hide the min/max numeric labels. For other metrics show min/max.
  const fmtBound = v => meta.isShare ? (v * 100).toFixed(0) + "%" : meta.signed ? (v >= 0 ? "+" : "") + v.toFixed(2) : v.toFixed(1);
  const ticksEl = $("legend-ticks");
  ticksEl.innerHTML = "";
  if (meta.freqOrdinal) {
    $("legend-min").style.visibility = "hidden";
    $("legend-max").style.visibility = "hidden";
    for (const lbl of FREQ_LABELS) {
      const s = document.createElement("span");
      s.textContent = lbl;
      ticksEl.appendChild(s);
    }
  } else {
    $("legend-min").style.visibility = "visible";
    $("legend-max").style.visibility = "visible";
    $("legend-min").textContent = fmtBound(meta.domain[0]);
    $("legend-max").textContent = fmtBound(meta.domain[1]);
  }
  if (interp) {
    const stops = Array.from({length: 11}, (_, i) => interp(i / 10));
    $("legend-swatch").style.background = `linear-gradient(to right, ${stops.join(",")})`;
  }
  $("legend-note").textContent = `${Object.keys(valueByName).length} countries shown · ${filterSummary()}`;
}

// Country detail
function hideDetail() {
  $("country-detail").classList.remove("active");
  // Restore the global time-series panel if a multi-month window is active.
  if (winSel.value !== "1") $("ts-panel").classList.add("active");
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
    ["Frequency mean", fmtFreqMean(row.freq_mean)],
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
    let hasAny = false;
    for (const k of [1,2,3,4,5,6]) {
      const v = dr[k];
      if (v != null) {
        hasAny = true;
        items.push(`<span style="display:inline-block;margin-right:16px;font-size:13px;color:var(--muted)">${labels[k]}: <strong style="color:${v>0?"var(--pos)":v<0?"var(--neg)":"var(--accent)"}">${fmtSigned(v)}</strong></span>`);
      } else {
        items.push(`<span style="display:inline-block;margin-right:16px;font-size:13px;color:var(--muted);opacity:0.45">${labels[k]}: <em>n/a</em></span>`);
      }
    }
    if (hasAny) html += `<div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--rule)"><div class="lbl" style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">Dose-response (net impact by AI-use frequency · n/a means &lt;50 respondents at that level)</div>${items.join("")}</div>`;
  }
  $("cd-body").innerHTML = html;

  // Country-specific time series (only when a multi-month window is active).
  if (winSel.value !== "1") {
    const meta = activeMetricMeta();
    const countryRows = windowRowsRaw().filter(r => atlasName(r.country_clean) === name);
    const series = countryRows.map(r => {
      const v = metricForRow(r);
      const ym = ymKey(r);
      return v != null ? { ym, date: ymToDate(ym), value: v } : null;
    }).filter(Boolean).sort((a, b) => a.date - b.date);

    const tsBlock = document.createElement("div");
    tsBlock.style.marginTop = "16px";
    tsBlock.style.paddingTop = "12px";
    tsBlock.style.borderTop = "1px solid var(--rule)";
    tsBlock.innerHTML = `<div class="lbl" style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">${meta.label} over time — ${name}</div><div class="ts-chart-detail"></div>`;
    $("cd-body").appendChild(tsBlock);
    renderTimeseriesInto(tsBlock.querySelector(".ts-chart-detail"), series, meta, 200);
  }

  el.classList.add("active");
  // Hide the global time-series while looking at a single country.
  $("ts-panel").classList.remove("active");
  el.scrollIntoView({behavior: "smooth", block: "nearest"});
}

function renderTimeseriesInto(container, data, meta, height) {
  if (!data || data.length === 0) {
    container.innerHTML = '<div class="empty">Not enough data to plot a trend.</div>';
    return;
  }
  const fmtVal = v => fmtMetric(v, meta);
  const yAxis = { domain: meta.domain, label: null, grid: true, nice: false };
  if (meta.isShare) yAxis.tickFormat = "%";
  const marks = [];
  if (meta.signed) marks.push(Plot.ruleY([0], { stroke: "#cbd5e1" }));
  marks.push(Plot.lineY(data, { x: "date", y: "value", stroke: "#1F3A5F", strokeWidth: 2, curve: "monotone-x" }));
  marks.push(Plot.dot(data, {
    x: "date", y: "value",
    fill: d => d.value,
    stroke: "#1F3A5F", strokeWidth: 1,
    r: 5,
    title: d => `${d.date.toLocaleDateString("en", {month:"short", year:"2-digit"})}: ${fmtVal(d.value)}`,
    tip: true,
  }));
  const interp = makeInterp(meta);
  const colorOpts = interp
    ? { type: "linear", interpolate: interp, domain: meta.domain, clamp: true, legend: false }
    : { type: "linear", scheme: meta.scheme, domain: meta.domain, clamp: true, legend: false };
  const plot = Plot.plot({
    width: 880,
    height: height || 220,
    marginTop: 16,
    marginRight: 20,
    marginBottom: 30,
    marginLeft: 56,
    x: { type: "time", label: null, tickFormat: d => d.toLocaleDateString("en", {month:"short", year:"2-digit"}) },
    y: yAxis,
    color: colorOpts,
    marks,
  });
  container.innerHTML = "";
  container.appendChild(plot);
}

function renderTimeseries() {
  const panel = $("ts-panel");
  if (winSel.value === "1") {
    panel.classList.remove("active");
    return;
  }
  panel.classList.add("active");
  const meta = activeMetricMeta();
  const data = monthlySeries(windowRowsRaw());
  $("ts-title").textContent = `${meta.label} over time`;
  $("ts-meta").textContent = `${data.length} of ${selectedMonths().size} months · weighted across visible countries · ${filterSummary()}`;
  renderTimeseriesInto($("ts-chart"), data, meta, 240);
}

function render() {
  renderKPIs();
  renderMap();
  renderTimeseries();
}

[metricSel, genderSel, ageSel, freqSel, monthSel, winSel].forEach(el => el.addEventListener("change", () => { hideDetail(); render(); }));
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
