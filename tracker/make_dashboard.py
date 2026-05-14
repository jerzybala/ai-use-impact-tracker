"""
Bake a self-contained, single-page AI Impact Tracker dashboard.

Layout:
  - Header with title and top-right "Global · last N months" summary card
  - Top filter row (month, period, work-impact factor, gender, age band, country)
  - Detail panel (Global by default; switches to a country when selected)
  - Side-by-side world choropleth + time-series chart

Data layers embedded:
  - global
  - country
  - country_gender
  - country_age_band
  - country_gender_age_band

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


def load_meta(tracker_out: Path) -> dict:
    """Read the _meta.json sidecar written by parquet_writer. Falls back to defaults."""
    p = tracker_out / "_meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"min_n": 50}


def bake_html(payload: str, meta: dict) -> str:
    """Apply both template substitutions in one place."""
    return (HTML_TEMPLATE
            .replace("__DATA_JSON__", payload)
            .replace("__MIN_N__", str(int(meta.get("min_n", 50)))))


def main():
    if not TRACKER_OUT.exists():
        raise SystemExit(
            f"No ETL output at {TRACKER_OUT}. Run:\n"
            f"  python3 main.py --source csv --path <your.csv> --out ./output"
        )
    print("Loading Parquet outputs…")
    meta = load_meta(TRACKER_OUT)
    payload = build_payload(TRACKER_OUT)
    print(f"Embedded JSON size: {len(payload)/1024:.1f} KB · min_n={meta.get('min_n', 50)}")

    html = bake_html(payload, meta)
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
<title>AI Impact Tracker — Impact of AI on Work</title>
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
  h1 .sub { color:var(--ink); font-weight:600; }
  header p { color:var(--muted); margin:0; max-width:780px; font-size:14px; }
  header p a { color:var(--accent2); text-decoration:none; border-bottom:1px solid currentColor; }
  header p a:hover { color:var(--accent); }

  .header-top { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; flex-wrap:wrap; }
  .title-block { flex:1 1 360px; min-width:0; }
  .help-menu { position:relative; flex-shrink:0; align-self:flex-start; }

  .summary-card { background:#fff; border:2px solid var(--hero); border-radius:10px; padding:12px 16px; box-shadow:0 1px 2px rgba(0,0,0,0.06); min-width:280px; }
  .summary-card .summary-head { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; font-weight:600; margin-bottom:6px; }
  .summary-card .summary-grid { display:flex; gap:22px; align-items:flex-end; }
  .summary-card .summary-grid > div { display:flex; flex-direction:column; gap:2px; }
  .summary-card .lbl { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; font-weight:600; }
  .summary-card .val { font-size:24px; font-weight:600; color:var(--hero); line-height:1.1; }
  .summary-card .val.ink { color:var(--accent); }
  .summary-card .summary-sub { font-size:11px; color:var(--muted); margin-top:6px; }
  .summary-card .summary-total { font-size:11px; color:var(--muted); margin-top:2px; }
  .summary-card .summary-total strong { color:var(--ink); font-weight:600; }

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

  .pos { color:var(--pos) !important; } .neg { color:var(--neg) !important; }

  .map-ts-grid { display:grid; grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr); gap:18px; }
  @media (max-width:980px) { .map-ts-grid { grid-template-columns: 1fr; } }

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

  .ts-panel { background:#fff; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); padding:18px; }
  .ts-panel h3 { margin:0 0 6px; font-size:15px; color:#333; font-weight:600; }
  .ts-panel .ts-meta { font-size:12px; color:var(--muted); margin-bottom:8px; }
  .ts-chart svg { width:100%; height:auto; max-height:500px; display:block; }

  .detail-panel { background:#fff; border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); padding:18px; margin-bottom:18px; }
  .detail-panel h3 { margin:0 0 12px; color:var(--accent); font-size:18px; }
  .detail-panel .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:14px; }
  .detail-panel .stat .lbl { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; }
  .detail-panel .stat .v { font-size:18px; font-weight:600; color:var(--accent); }
  .dose-block { margin-top:14px; padding-top:12px; border-top:1px solid var(--rule); }
  .dose-block .dose-label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }
  .dose-items { display:flex; flex-wrap:wrap; gap:6px 18px; line-height:1.5; }
  .dose-items > span { font-size:13px; color:var(--muted); white-space:nowrap; }

  .empty { color:var(--muted); font-style:italic; padding:14px; text-align:center; }

  .map-tip {
    position:fixed; pointer-events:none; z-index:1000;
    background:#fff; border:1px solid var(--rule); border-radius:6px;
    padding:8px 12px; box-shadow:0 4px 14px rgba(0,0,0,0.12);
    font-size:13px; color:var(--ink); line-height:1.45;
    max-width:280px; display:none;
  }
  .map-tip .name { color:var(--accent); font-weight:600; margin-bottom:3px; }
  .map-tip .row { color:var(--muted); font-size:12px; }
  .map-tip .row strong { color:var(--ink); font-weight:600; }
  .map-tip .row.muted { color:var(--muted); font-style:italic; }

  .help-btn { background:var(--chip); color:var(--accent); border:1px solid var(--rule);
    border-radius:6px; padding:6px 12px; font-size:13px; font-weight:600; cursor:pointer; }
  .help-btn:hover { background:#d8e2ec; }
  .help-dropdown { position:absolute; right:0; top:calc(100% + 6px); background:#fff;
    border:1px solid var(--rule); border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,0.10);
    min-width:200px; padding:6px; display:none; z-index:100; }
  .help-dropdown.open { display:block; }
  .help-dropdown a { display:block; padding:8px 12px; font-size:13px; color:var(--ink);
    text-decoration:none; border-radius:5px; }
  .help-dropdown a:hover { background:var(--chip); color:var(--accent); }
</style>
</head>
<body>
<div class="shell">
  <header>
    <div class="header-top">
      <div class="title-block">
        <h1>AI Impact Tracker: <span class="sub">Impact of AI on Work</span></h1>
        <p>Self-reported impact of AI use on work, by country and demographic. Built on the <a href="https://sapienlabs.org/global-mind-project/" target="_blank" rel="noopener">Global Mind Project</a> by Sapien Labs. Cells with fewer than __MIN_N__ respondents are suppressed.</p>
      </div>
      <div class="summary-card" id="summary-card">
        <div class="summary-head" id="summary-head">Global · last 3 months</div>
        <div class="summary-grid">
          <div>
            <div class="lbl" id="summary-metric-lbl">Weighted Impact Index</div>
            <div class="val" id="summary-metric-val">—</div>
          </div>
          <div>
            <div class="lbl">Respondents</div>
            <div class="val ink" id="summary-n">—</div>
          </div>
        </div>
        <div class="summary-sub" id="summary-period">—</div>
        <div class="summary-total">Total respondents to date: <strong id="summary-total-n">—</strong></div>
      </div>
      <div class="help-menu">
        <button type="button" class="help-btn" id="help-btn" aria-haspopup="true" aria-expanded="false">Help ▾</button>
        <div class="help-dropdown" id="help-dropdown" role="menu">
          <a href="/docs/DASHBOARD_SIMPLE.html" target="_blank" rel="noopener">User guide</a>
          <a href="/docs/DASHBOARD_SIMPLE.html#eight" target="_blank" rel="noopener">Metric reference</a>
          <a href="/docs/COLUMNS.html" target="_blank" rel="noopener">Data columns</a>
        </div>
      </div>
    </div>
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
        <option value="3">Last 3 months</option>
        <option value="6">Last 6 months</option>
        <option value="12">Last 12 months</option>
      </select>
    </div>
    <div class="group">
      <label>Select Work Impact Factor</label>
      <select id="metric-select">
        <option value="weighted_impact_index">Weighted Impact Index</option>
        <option value="adoption_rate">AI Adoption Rate</option>
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
      </select>
    </div>
    <div class="group">
      <label>Age band</label>
      <select id="age-select">
        <option value="">All</option>
      </select>
    </div>
    <div class="group">
      <label>Country</label>
      <select id="country-select" title="Show detail and trend for the selected country">
        <option value="">Global</option>
      </select>
    </div>
    <button class="reset" id="reset-btn">Reset filters</button>
  </div>

  <div class="detail-panel" id="detail-panel">
    <h3 id="cd-name">Global</h3>
    <div id="cd-body"></div>
  </div>

  <div class="map-ts-grid">
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
  </div>

  <div class="map-tip" id="map-tip"></div>
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

// Color scheme + value-type config per metric. Domain is now computed
// dynamically from the visible data (see computeDomain in renderMap), so
// the darkest color always lands on the actual max observed.
const METRIC_META = {
  weighted_impact_index:            { label:"Weighted Impact Index",       scheme:"Greens", isShare:false, signed:true  },
  adoption_rate:                    { label:"AI Adoption Rate",            scheme:"Blues",  isShare:true,  signed:false },
  impact_share_improved_quality:    { label:"Improved Quality (share)",    scheme:"Greens", isShare:true,  signed:false },
  impact_share_new_opportunities:   { label:"New Opportunities (share)",   scheme:"Greens", isShare:true,  signed:false },
  impact_share_adaptation_pressure: { label:"Adaptation Pressure (share)", scheme:"Reds",   isShare:true,  signed:false },
  impact_share_job_anxiety:         { label:"Job Anxiety (share)",         scheme:"Reds",   isShare:true,  signed:false },
  impact_share_job_loss:            { label:"Job Loss (share)",            scheme:"Reds",   isShare:true,  signed:false },
  impact_share_reduced_income:      { label:"Reduced Income (share)",      scheme:"Reds",   isShare:true,  signed:false },
};

const $ = id => document.getElementById(id);
const monthSel = $("month-select"), metricSel = $("metric-select");
const genderSel = $("gender-select"), ageSel = $("age-select");
const countrySel = $("country-select");
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

// Default Period to "Last 3 months"
winSel.value = "3";

// Build the country dropdown from country-level rows.
const allCountries = [...new Set(DATA.country.map(r => r.country_clean).filter(Boolean))].sort();
for (const c of allCountries) {
  const opt = document.createElement("option");
  opt.value = c;
  opt.textContent = c;
  countrySel.appendChild(opt);
}

// Build the gender dropdown from country_gender rows — only includes
// genders that have at least one non-suppressed cell anywhere (i.e. some
// country meets the min-N threshold). Below-threshold categories are
// hidden so users don't pick options that show "no data" everywhere.
const genderOrder = ["Female", "Male", "Non-binary", "Other/Intersex", "Prefer not to say"];
const availableGenders = new Set(DATA.country_gender.map(r => r.gender_clean).filter(Boolean));
for (const g of genderOrder) {
  if (!availableGenders.has(g)) continue;
  const opt = document.createElement("option");
  opt.value = g; opt.textContent = g;
  genderSel.appendChild(opt);
}
// Any extras outside the canonical order (defensive).
for (const g of [...availableGenders].sort()) {
  if (genderOrder.includes(g)) continue;
  const opt = document.createElement("option");
  opt.value = g; opt.textContent = g;
  genderSel.appendChild(opt);
}

// Same below-threshold filter for age bands — only ages with at least one
// non-suppressed cell appear in the dropdown.
const ageOrder = ["18-20", "21-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75-84", "85+"];
const availableAges = new Set(DATA.country_age_band.map(r => r.age_band).filter(Boolean));
for (const a of ageOrder) {
  if (!availableAges.has(a)) continue;
  const opt = document.createElement("option");
  opt.value = a; opt.textContent = a;
  ageSel.appendChild(opt);
}
for (const a of [...availableAges].sort()) {
  if (ageOrder.includes(a)) continue;
  const opt = document.createElement("option");
  opt.value = a; opt.textContent = a;
  ageSel.appendChild(opt);
}

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
  genderSel.value = ""; ageSel.value = ""; countrySel.value = "";
  winSel.value = "3";
  render();
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

// Aggregate country-level rows (already filtered by month/gender/age) into a
// single global pseudo-row that mirrors the country row shape. Used for the
// detail panel and the top summary card when Country = Global.
function aggregateGlobal(rows) {
  if (!rows.length) return null;
  const o = {
    country_clean: "Global",
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
  return o;
}

function ymKey(r) { return `${r.year}-${String(r.month).padStart(2,"0")}`; }
function ymToDate(ym) { const [y, m] = ym.split("-").map(Number); return new Date(y, m - 1, 1); }

// Per-month weighted aggregate of the active metric across the given rows.
// Also records `n` (sum of n_respondents across countries in that month) so
// markPartial() can detect the in-flight current month from its low sample.
function monthlySeries(rows) {
  const isVolume = metricSel.value === "adoption_rate";
  const weightField = isVolume ? "n_respondents" : "n_impact_denominator";
  const byMonth = new Map();
  for (const r of rows) {
    const k = ymKey(r);
    if (!byMonth.has(k)) byMonth.set(k, []);
    byMonth.get(k).push(r);
  }
  const out = [];
  for (const [ym, rs] of byMonth) {
    let num = 0, den = 0, totalN = 0;
    for (const r of rs) {
      const v = metricForRow(r);
      const w = r[weightField] || 0;
      if (v != null && w > 0) { num += v * w; den += w; }
      totalN += r.n_respondents || 0;
    }
    if (den > 0) out.push({ ym, date: ymToDate(ym), value: num / den, n: totalN });
  }
  out.sort((a, b) => a.date - b.date);
  return out;
}

// Tag the last point as `partial` when its respondent count is well below the
// median of prior months in the series — the signal that the current month is
// still in flight. Requires at least 3 prior months to compute a stable median.
function markPartial(data) {
  if (!data || data.length < 4) return data;
  const prior = data.slice(0, -1).map(d => d.n).filter(v => v != null && v > 0);
  if (prior.length < 3) return data;
  const sorted = [...prior].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const last = data[data.length - 1];
  if (last.n != null && median > 0 && last.n < 0.6 * median) {
    last.partial = true;
  }
  return data;
}

function activeMetricMeta() {
  return METRIC_META[metricSel.value];
}

function metricForRow(r) {
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
  return parts.join(" · ");
}

const fmtSigned = v => v == null ? "—" : (v >= 0 ? "+" : "") + v.toFixed(3);
const fmtPct = v => v == null ? "—" : (v * 100).toFixed(1) + "%";
const fmtNum = v => v == null ? "—" : v.toLocaleString();
const fmtMetric = (v, meta) => {
  if (v == null) return "—";
  if (meta.isShare) return fmtPct(v);
  if (meta.signed) return fmtSigned(v);
  return v.toFixed(2);
};

// Total respondents across the entire dataset (all months, global rows).
// Computed once at startup so the summary card can always show it.
const TOTAL_RESPONDENTS_TO_DATE = DATA.global.reduce(
  (s, r) => s + (r.n_respondents || 0), 0);

// Top-right summary card — global weighted average of the active metric over
// the selected period, plus respondents in period and total respondents to date.
function renderSummary() {
  const rows = currentRows();
  const meta = activeMetricMeta();
  const totalN = rows.reduce((s, r) => s + (r.n_respondents || 0), 0);
  const weightField = meta.isShare ? "n_impact_denominator"
                                   : (metricSel.value === "adoption_rate" ? "n_respondents"
                                                                          : "n_impact_denominator");
  let num = 0, den = 0;
  for (const r of rows) {
    const v = r[metricSel.value], w = r[weightField] || 0;
    if (v != null && w > 0) { num += v * w; den += w; }
  }
  const avg = den > 0 ? num / den : null;

  const head = `Global · ${periodLabel()}`;
  $("summary-head").textContent = head;

  $("summary-metric-lbl").textContent = meta.label;
  const valEl = $("summary-metric-val");
  valEl.textContent = fmtMetric(avg, meta);
  valEl.classList.remove("pos", "neg");
  if (meta.signed && avg != null && avg > 0) valEl.classList.add("pos");
  if (meta.signed && avg != null && avg < 0) valEl.classList.add("neg");

  $("summary-n").textContent = fmtNum(totalN);
  $("summary-period").textContent = filterSummary();
  $("summary-total-n").textContent = fmtNum(TOTAL_RESPONDENTS_TO_DATE);
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

// Dynamic color domain: stretch the scale so the actual max in the visible
// data lands at the darkest end of the scheme. For diverging (signed) metrics
// the domain is kept symmetric around 0 so 0 stays at the neutral midpoint
// and the larger absolute extreme drives saturation. Falls back to a small
// neighborhood around the only value when min == max.
function computeDomain(values, meta) {
  if (!values.length) return meta.signed ? [-0.1, 0.1] : [0, 1];
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (meta.signed) {
    const m = Math.max(Math.abs(lo), Math.abs(hi));
    return m > 0 ? [-m, m] : [-0.1, 0.1];
  }
  if (hi - lo < 1e-9) {
    const pad = Math.max(Math.abs(hi) * 0.05, 0.01);
    return [Math.max(0, lo - pad), hi + pad];
  }
  return [lo, hi];
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

  const domain = computeDomain(Object.values(valueByName), meta);
  const fmt = v => fmtMetric(v, meta);
  const interp = makeInterp(meta);
  const colorOpts = interp
    ? { type: "linear", interpolate: interp, domain, clamp: true, unknown: "#cbd5e1" }
    : { type: "linear", scheme: meta.scheme, domain, clamp: true, unknown: "#cbd5e1" };

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
        // No title/tip channel — we attach a custom DOM tooltip below
        // anchored to the actual <path> element under the cursor.
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
    const tip = $("map-tip");
    const positionTip = e => {
      const pad = 14;
      const rect = tip.getBoundingClientRect();
      let x = e.clientX + pad;
      let y = e.clientY + pad;
      if (x + rect.width > window.innerWidth - 8) x = e.clientX - rect.width - pad;
      if (y + rect.height > window.innerHeight - 8) y = e.clientY - rect.height - pad;
      tip.style.left = Math.max(4, x) + "px";
      tip.style.top = Math.max(4, y) + "px";
    };
    const hideTip = () => { tip.style.display = "none"; };

    countryGroup.querySelectorAll(":scope > path").forEach((p, i) => {
      const f = countriesGeo.features[i];
      if (!f || !f.properties || !f.properties.name) return;
      const name = f.properties.name;
      p.style.cursor = "pointer";
      p.addEventListener("click", () => selectCountryByAtlasName(name));
      p.addEventListener("mouseenter", e => {
        const v = valueByName[name];
        const r = rowByName[name];
        if (v == null) {
          tip.innerHTML = `<div class="name">${name}</div><div class="row muted">No data / suppressed</div>`;
        } else {
          tip.innerHTML = `<div class="name">${name}</div>
            <div class="row">${meta.label}: <strong>${fmt(v)}</strong></div>
            <div class="row">n = <strong>${(r?.n_respondents ?? 0).toLocaleString()}</strong></div>`;
        }
        tip.style.display = "block";
        positionTip(e);
      });
      p.addEventListener("mousemove", positionTip);
      p.addEventListener("mouseleave", hideTip);
    });
  }

  const c = $("map-container");
  c.innerHTML = "";
  c.appendChild(plot);

  $("map-title").textContent = "World map — " + meta.label;
  $("map-meta").textContent = `${rows.length.toLocaleString()} country rows · cells under n=50 are suppressed`;

  // Legend — labels reflect the dynamic domain (darkest end = max in data).
  const fmtBound = v => meta.isShare ? (v * 100).toFixed(0) + "%" : meta.signed ? (v >= 0 ? "+" : "") + v.toFixed(2) : v.toFixed(2);
  $("legend-ticks").innerHTML = "";
  $("legend-min").style.visibility = "visible";
  $("legend-max").style.visibility = "visible";
  $("legend-min").textContent = fmtBound(domain[0]);
  $("legend-max").textContent = fmtBound(domain[1]);
  if (interp) {
    const stops = Array.from({length: 11}, (_, i) => interp(i / 10));
    $("legend-swatch").style.background = `linear-gradient(to right, ${stops.join(",")})`;
  }
  $("legend-note").textContent = `${Object.keys(valueByName).length} countries shown · ${filterSummary()}`;
}

// Reverse atlas → GMP name lookup for map clicks. We need to find the
// country_clean value that matches an atlas feature name. Built lazily from
// the country-level rows so we only include names that actually have data.
function gmpNameFromAtlas(atlas) {
  for (const r of DATA.country) {
    if (r.country_clean && atlasName(r.country_clean) === atlas) return r.country_clean;
  }
  return null;
}
function selectCountryByAtlasName(atlas) {
  const gmp = gmpNameFromAtlas(atlas);
  if (gmp) {
    countrySel.value = gmp;
    render();
  }
}

// Detail panel — always visible. Shows the Global aggregate (countrySel
// empty) or the row matching the currently-selected country.
function renderDetail() {
  const country = countrySel.value;
  const rows = currentRows();

  let row, name;
  if (!country) {
    name = "Global";
    row = aggregateGlobal(rows);
  } else {
    name = country;
    row = rows.find(r => r.country_clean === country) || null;
  }

  $("cd-name").textContent = name;
  if (!row) {
    $("cd-body").innerHTML = `<div class="empty">No data for ${name} under the current filters.</div>`;
    return;
  }

  const stats = [
    ["Respondents", fmtNum(row.n_respondents)],
    ["Adoption rate", fmtPct(row.adoption_rate)],
    ["Weighted impact", fmtSigned(row.weighted_impact_index)],
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
        items.push(`<span>${labels[k]}: <strong style="color:${v>0?"var(--pos)":v<0?"var(--neg)":"var(--accent)"}">${fmtSigned(v)}</strong></span>`);
      } else {
        items.push(`<span style="opacity:0.45">${labels[k]}: <em>n/a</em></span>`);
      }
    }
    if (hasAny) html += `<div class="dose-block"><div class="dose-label">Dose-response (net impact by AI-use frequency · n/a means &lt;50 respondents at that level)</div><div class="dose-items">${items.join("")}</div></div>`;
  }
  $("cd-body").innerHTML = html;
}

// Fit a tight y-domain around the time-series data with a small padding,
// so small month-over-month changes are readable instead of flattened
// against the map's full visualization range.
function fitTSDomain(data, meta) {
  const vals = data.map(d => d.value).filter(v => Number.isFinite(v));
  if (vals.length === 0) return meta.signed ? [-0.1, 0.1] : [0, 1];
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min;
  // delta = 15% of the range, with a small floor so a flat series still
  // gets some vertical breathing room.
  const floor = meta.isShare ? 0.005 : meta.signed ? 0.01 : 0.05;
  const delta = Math.max(range * 0.15, floor);
  let lo = min - delta, hi = max + delta;
  if (meta.isShare) lo = Math.max(0, lo);
  return [lo, hi];
}

function renderTimeseriesInto(container, data, meta, height) {
  if (!data || data.length === 0) {
    container.innerHTML = '<div class="empty">Not enough data to plot a trend.</div>';
    return;
  }
  const fmtVal = v => fmtMetric(v, meta);
  const yAxis = { domain: fitTSDomain(data, meta), label: null, grid: true, nice: false };
  if (meta.isShare) yAxis.tickFormat = "%";
  const marks = [];
  if (meta.signed) marks.push(Plot.ruleY([0], { stroke: "#cbd5e1" }));

  const lastIsPartial = data.length > 0 && data[data.length - 1].partial;
  const titleFn = d => `${d.date.toLocaleDateString("en", {month:"short", year:"2-digit"})}: ${fmtVal(d.value)}${d.partial ? " (partial month)" : ""}`;

  if (lastIsPartial && data.length >= 2) {
    // Solid line through completed months only — no connector to the partial
    // tail, since a dashed link visually drags the last complete month into
    // the "uncertain" zone. The outlined dot + caption note carry the signal.
    const solidData = data.slice(0, -1);
    marks.push(Plot.lineY(solidData, { x: "date", y: "value", stroke: "#1F3A5F", strokeWidth: 2, curve: "monotone-x" }));
    // Filled dots for completed months; outlined dot for the partial point.
    marks.push(Plot.dot(solidData, {
      x: "date", y: "value",
      fill: d => d.value,
      stroke: "#1F3A5F", strokeWidth: 1, r: 5,
      title: titleFn, tip: true,
    }));
    marks.push(Plot.dot(data.slice(-1), {
      x: "date", y: "value",
      fill: "#ffffff",
      stroke: "#1F3A5F", strokeWidth: 1.5, r: 5,
      title: titleFn, tip: true,
    }));
  } else {
    marks.push(Plot.lineY(data, { x: "date", y: "value", stroke: "#1F3A5F", strokeWidth: 2, curve: "monotone-x" }));
    marks.push(Plot.dot(data, {
      x: "date", y: "value",
      fill: d => d.value,
      stroke: "#1F3A5F", strokeWidth: 1, r: 5,
      title: titleFn, tip: true,
    }));
  }
  const interp = makeInterp(meta);
  const colorDomain = computeDomain(data.map(d => d.value).filter(Number.isFinite), meta);
  const colorOpts = interp
    ? { type: "linear", interpolate: interp, domain: colorDomain, clamp: true, legend: false }
    : { type: "linear", scheme: meta.scheme, domain: colorDomain, clamp: true, legend: false };
  const plot = Plot.plot({
    width: 600,
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

// Rows for the trend chart: last 12 months ending at the selected month,
// filtered by gender/age but independent of the Period filter. Lets the
// trend stay useful even when the Period is set to "Last 3 months".
function tsRowsRaw() {
  const i = months.indexOf(monthSel.value);
  const lo = Math.max(0, i - 11);
  const sel = new Set(months.slice(lo, i + 1));
  const { rows, gender, age } = pickStratum();
  return rows.filter(r => {
    const ym = `${r.year}-${String(r.month).padStart(2,"0")}`;
    if (!sel.has(ym)) return false;
    if (gender && r.gender_clean !== gender) return false;
    if (age && r.age_band !== age) return false;
    return true;
  });
}

function renderTimeseries() {
  const meta = activeMetricMeta();
  const country = countrySel.value;
  const name = country || "Global";

  let data;
  if (country) {
    const cRows = tsRowsRaw().filter(r => r.country_clean === country);
    data = cRows.map(r => {
      const v = metricForRow(r);
      const ym = ymKey(r);
      return v != null ? { ym, date: ymToDate(ym), value: v, n: r.n_respondents || 0 } : null;
    }).filter(Boolean).sort((a, b) => a.date - b.date);
  } else {
    data = monthlySeries(tsRowsRaw());
  }
  markPartial(data);

  $("ts-title").textContent = `${meta.label} over time — ${name}`;

  if (!data || data.length < 3) {
    $("ts-meta").textContent = filterSummary();
    $("ts-chart").innerHTML = '<div class="empty">Insufficient data to show a trend.</div>';
    return;
  }

  const partialNote = (data.length && data[data.length - 1].partial) ? " · last month partial (in-progress data)" : "";
  $("ts-meta").textContent = `${data.length} months · ${filterSummary()}${partialNote}`;
  renderTimeseriesInto($("ts-chart"), data, meta, 500);
}

function render() {
  renderSummary();
  renderDetail();
  renderMap();
  renderTimeseries();
}

[metricSel, genderSel, ageSel, countrySel, monthSel, winSel].forEach(el => el.addEventListener("change", render));

// Help menu
const helpBtn = $("help-btn");
const helpDrop = $("help-dropdown");
helpBtn.addEventListener("click", e => {
  e.stopPropagation();
  const isOpen = helpDrop.classList.toggle("open");
  helpBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
});
document.addEventListener("click", e => {
  if (!helpDrop.contains(e.target) && e.target !== helpBtn) {
    helpDrop.classList.remove("open");
    helpBtn.setAttribute("aria-expanded", "false");
  }
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && helpDrop.classList.contains("open")) {
    helpDrop.classList.remove("open");
    helpBtn.setAttribute("aria-expanded", "false");
    helpBtn.focus();
  }
});

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
