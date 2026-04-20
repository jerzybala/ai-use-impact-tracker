"""
Bake a self-contained v2 dashboard — Tara's weighted AI Impact Index.

Same mechanics as make_preview.py (embeds JSON, Observable Plot from CDN)
but built around the weighted_impact_index as the primary outcome metric.

Run AFTER main.py:

    python3 make_preview_v2.py

Output: ../dashboard/preview_v2.html (overwrites)
"""
from __future__ import annotations

import glob, json, math
from pathlib import Path
import pandas as pd


HERE = Path(__file__).parent
TRACKER_OUT = HERE / "output" / "v1" / "metrics"
DASHBOARD_DIR = HERE.parent / "dashboard"
OUT_HTML = DASHBOARD_DIR / "preview_v2.html"


def load_level(level: str) -> list[dict]:
    files = sorted(TRACKER_OUT.glob(f"stratum_level={level}/**/part-0.parquet"))
    if not files:
        print(f"  warning: no files found for level={level}")
        return []
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
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


def main():
    if not TRACKER_OUT.exists():
        raise SystemExit(
            f"No ETL output at {TRACKER_OUT}. Run:\n"
            f"  python3 main.py --source csv --path <your.csv> --out ./output"
        )

    print("Loading Parquet outputs…")
    data = {
        "global":   load_level("global"),
        "country":  load_level("country"),
        "gender":   load_level("gender"),
        "age_band": load_level("age_band"),
    }
    for k, v in data.items():
        print(f"  {k:10} rows={len(v)}")

    payload = json.dumps(data, separators=(",", ":"))
    size_kb = len(payload) / 1024
    print(f"Embedded JSON size: {size_kb:.1f} KB")

    html = HTML_TEMPLATE_V2.replace("__DATA_JSON__", payload)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"\nWrote {OUT_HTML}")
    print("Open by double-clicking the file — no server needed.")


# ---------------------------------------------------------------------------
# V2 Dashboard template — Tara's Weighted Impact Index as primary metric
# ---------------------------------------------------------------------------
HTML_TEMPLATE_V2 = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AI Use Impact Tracker — v2 (Weighted Index)</title>
<style>
  :root { --ink:#1a1a1a; --muted:#6b7280; --accent:#1F3A5F; --accent2:#2E5C8A;
          --pos:#1a7f4e; --neg:#b3261e; --rule:#e5e7eb; --chip:#E8EEF4;
          --wii:#6366f1; }
  html, body { margin: 0; background: #f6f7f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: var(--ink); }
  .shell { max-width: 1200px; margin: 0 auto; padding: 32px 40px 60px; }
  header { padding-bottom: 20px; border-bottom: 1px solid var(--rule); margin-bottom: 28px; }
  h1 { color: var(--accent); margin: 0 0 6px; font-size: 28px; }
  .badge { display: inline-block; background: var(--wii); color: #fff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; vertical-align: middle; margin-left: 10px; letter-spacing: 0.5px; }
  header p { color: var(--muted); margin: 0; max-width: 720px; }
  nav { margin-top: 12px; display: flex; gap: 16px; }
  nav a { color: var(--accent2); text-decoration: none; font-weight: 500; font-size: 14px; cursor: pointer; padding: 6px 10px; border-radius: 6px; }
  nav a.active { background: var(--chip); color: var(--accent); }
  h2 { color: var(--accent); font-size: 18px; margin: 28px 0 10px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
  @media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  .card { background: #fff; padding: 16px 18px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
  .card .label { font-size: 12px; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .card .value { font-size: 28px; font-weight: 600; color: var(--accent); }
  .card .sub { font-size: 12px; color: var(--muted); margin-top: 4px; }
  .card.hero { border: 2px solid var(--wii); }
  .card.hero .value { color: var(--wii); font-size: 34px; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  .panel { background: #fff; padding: 18px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); margin-bottom: 20px; }
  .panel h3 { margin: 0 0 12px; font-size: 15px; color: #333; font-weight: 600; }
  .muted { color: var(--muted); font-size: 13px; }
  input[type="text"] { padding: 5px 8px; border: 1px solid var(--rule); border-radius: 5px; font-size: 13px; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .err { color: var(--neg); padding: 30px; background: #fdecec; border-radius: 10px; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { border-bottom: 1px solid var(--rule); padding: 6px 10px; text-align: left; }
  th { background: var(--chip); color: var(--accent); position: sticky; top: 0; white-space: nowrap; }
  th.sortable { cursor: pointer; user-select: none; }
  th.sortable:hover { background: #d0dae6; }
  tbody tr:hover { background: #f9fafb; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .pos { color: var(--pos); font-weight: 600; }
  .neg { color: var(--neg); font-weight: 600; }
  footer { margin-top: 40px; color: var(--muted); font-size: 12px; text-align: center; border-top: 1px solid var(--rule); padding-top: 16px; }
  .month-bar { display: flex; align-items: center; gap: 12px; background: #fff; padding: 12px 18px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); margin-bottom: 20px; flex-wrap: wrap; }
  .month-bar label { font-weight: 600; color: var(--accent); font-size: 14px; }
  .month-bar select { padding: 6px 10px; border: 1px solid var(--rule); border-radius: 6px; font-size: 14px; background: #fff; color: var(--ink); font-weight: 500; cursor: pointer; min-width: 140px; }
  .month-bar select:focus { outline: 2px solid var(--accent2); outline-offset: 1px; }
  .month-bar .hint { color: var(--muted); font-size: 12px; margin-left: auto; max-width: 380px; }
  .month-bar .month-nav { background: #fff; border: 1px solid var(--rule); border-radius: 6px; padding: 5px 10px; font-size: 13px; color: var(--accent); cursor: pointer; line-height: 1; }
  .month-bar .month-nav:hover:not(:disabled) { background: var(--chip); }
  .month-bar .month-nav:disabled { opacity: 0.35; cursor: not-allowed; }
  .scatter-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 13px; color: var(--muted); }
  .scatter-controls label { font-weight: 600; color: var(--accent); }
  .scatter-controls input[type="range"] { width: 160px; accent-color: var(--accent2); }
  .scatter-controls span { font-weight: 600; color: var(--accent); min-width: 28px; }
  .label-toggle { font-size: 11px; font-weight: 500; color: var(--accent2); background: var(--chip); border: 1px solid var(--rule); border-radius: 4px; padding: 2px 8px; margin-left: 10px; cursor: pointer; vertical-align: middle; }
  .label-toggle:hover { background: #dbe4ed; }
  .weight-table { font-size: 13px; border-collapse: collapse; margin: 12px 0; }
  .weight-table th, .weight-table td { padding: 5px 12px; border-bottom: 1px solid var(--rule); }
  .weight-table .w { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
</style>
</head>
<body>
<div class="shell">

<header>
  <h1>AI Use Impact Tracker <span class="badge">v2</span></h1>
  <p>Weighted AI Impact Index — each impact flag carries a signed severity weight. Built on the Global Mind Project by Sapien Labs.</p>
  <nav>
    <a data-tab="overview"   class="active" onclick="showTab(event)">Overview</a>
    <a data-tab="countries"  onclick="showTab(event)">By country</a>
    <a data-tab="frequency"  onclick="showTab(event)">Frequency &amp; impact</a>
    <a data-tab="about"      onclick="showTab(event)">Methodology</a>
  </nav>
</header>

<div class="month-bar">
  <label for="month-selector">Showing data for:</label>
  <button id="month-prev" class="month-nav" aria-label="Previous month" title="Previous month">&#9664;</button>
  <select id="month-selector" aria-label="Select month"></select>
  <button id="month-next" class="month-nav" aria-label="Next month" title="Next month">&#9654;</button>
  <span class="hint">Single-month views update with the selection; the shaded band on the time-series marks the selected period. Rolling-window options pool months using n_respondents as weights (approximate).</span>
</div>

<div id="tab-overview" class="tab-content active">
  <div class="kpi-grid">
    <div class="card hero"><div class="label">Weighted Impact Index</div><div class="value" id="kpi-wii">—</div><div class="sub" id="kpi-wii-ci"></div></div>
    <div class="card"><div class="label">Respondents</div><div class="value" id="kpi-n">—</div><div class="sub" id="kpi-n-sub"></div></div>
    <div class="card"><div class="label">AI Adoption Rate</div><div class="value" id="kpi-adopt">—</div><div class="sub">share using AI at all</div></div>
    <div class="card"><div class="label">Impact Denominator</div><div class="value" id="kpi-denom">—</div><div class="sub">AI users with impact response</div></div>
  </div>

  <div class="panel"><h3>Weighted Impact Index over time — global</h3>
    <p class="muted" style="margin:-4px 0 8px">Per-respondent score = sum of flag weights for all selected impacts, averaged over the impact denominator. Purple line tracks the aggregate; dots colored by sign.</p>
    <div id="chart-wii-time"></div>
  </div>

  <div class="two-col">
    <div class="panel"><h3>AI adoption rate — global</h3><div id="chart-adoption"></div></div>
    <div class="panel"><h3>Impact composition (weighted) — <span class="sel-month">—</span>
        <button id="comp-label-toggle" class="label-toggle" title="Toggle between short labels and survey wording">Survey wording</button>
      </h3><div id="chart-impact-composition"></div></div>
  </div>

  <div class="two-col">
    <div class="panel"><h3>Weighted Impact by gender — <span class="sel-month">—</span></h3><div id="chart-gender"></div></div>
    <div class="panel"><h3>Weighted Impact by age band — <span class="sel-month">—</span></h3><div id="chart-age"></div></div>
  </div>
</div>

<div id="tab-countries" class="tab-content">
  <div class="panel"><h3>Top 12 countries — ranked by Weighted Impact Index — <span class="sel-month">—</span></h3><div id="chart-country-bar"></div></div>
  <div class="panel">
    <h3>Adoption rate × Weighted Impact — <span class="sel-month">—</span></h3>
    <p class="muted">Dot size encodes total respondent count.</p>
    <div class="scatter-controls">
      <label for="scatter-min-n">Min N:</label>
      <input type="range" id="scatter-min-n" min="50" max="500" step="10" value="50">
      <span id="scatter-min-n-val">50</span>
    </div>
    <div id="chart-country-scatter"></div>
  </div>
  <div class="panel">
    <h3>All country-months (n &ge; 50)</h3>
    <p><input type="text" id="country-search" placeholder="Filter countries…" style="width:260px"></p>
    <div style="max-height: 400px; overflow: auto;"><table id="country-table"></table></div>
  </div>
</div>

<div id="tab-frequency" class="tab-content">
  <div class="panel"><h3>Dose-response: Weighted Impact by AI frequency — <span class="sel-month">—</span></h3>
    <p class="muted">Weighted Impact Index at each AI-use frequency level. Higher frequency generally correlates with more positive impact.</p>
    <div id="chart-dose-global"></div>
  </div>
  <div class="two-col">
    <div class="panel"><h3>Dose-response by gender — <span class="sel-month">—</span></h3><div id="chart-dose-gender"></div></div>
    <div class="panel"><h3>Dose-response by age band — <span class="sel-month">—</span></h3><div id="chart-dose-age"></div></div>
  </div>
  <div class="panel"><h3>Frequency distribution over time — global</h3><div id="chart-freq-stack"></div></div>
</div>

<div id="tab-about" class="tab-content">
  <div class="panel">
    <h3>Methodology — v2 Weighted Impact Index</h3>
    <p><b>Source.</b> Global Mind Project (GMP), Sapien Labs. Monthly CSV extract of survey responses.</p>
    <p><b>Exposure — ai_freq.</b> A 7-level ordinal: Never (0), Rarely (1), Monthly (2), Weekly (3), Daily (4), Constantly (5), Always (6).</p>
    <p><b>Outcome — ai_impact_work.</b> Multi-select pipe-delimited, split into nine binary flags. Each flag carries a signed severity weight:</p>
    <table class="weight-table">
      <thead><tr><th>Impact flag</th><th class="w">Weight</th></tr></thead>
      <tbody>
        <tr><td>Created new job or income opportunities</td><td class="w pos">+1.00</td></tr>
        <tr><td>Improved my work quality or output</td><td class="w pos">+0.50</td></tr>
        <tr><td>No impact / Not sure / Other</td><td class="w">0.00</td></tr>
        <tr><td>Made me worry about the future of my job</td><td class="w neg">−0.25</td></tr>
        <tr><td>Increased pressure to adapt or work faster</td><td class="w neg">−0.50</td></tr>
        <tr><td>Reduced my income or made it harder to find work</td><td class="w neg">−0.75</td></tr>
        <tr><td>Caused me to lose my job</td><td class="w neg">−1.00</td></tr>
      </tbody>
    </table>
    <p><b>Per-respondent score</b> = sum of weights for all flags selected by that respondent. <b>Weighted Impact Index</b> = mean of per-respondent scores across the impact denominator (AI users with at least one non-null impact response).</p>
    <p><b>Asymmetry by design.</b> Negative weights are heavier because severe outcomes (job loss, income reduction) are considered more consequential than mild positives. The index is <em>not</em> symmetric around zero.</p>
    <p><b>95% CI</b> computed via SEM (standard error of the mean of per-respondent scores).</p>
    <p><b>Suppression.</b> Cells with n &lt; 50 respondents are suppressed.</p>
    <p><b>Limitations.</b> No survey weights; associations are descriptive, not causal. Month-over-month shifts may reflect composition effects rather than attitudinal change.</p>
  </div>
</div>

<footer>Global Mind Project — Sapien Labs • v2 Weighted Impact Dashboard</footer>
</div>

<!-- Embedded data — no fetch, works from file:// -->
<script id="embedded-data" type="application/json">__DATA_JSON__</script>

<script type="module">
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.16/+esm";
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

window.showTab = function(e) {
  const tab = e.target.dataset.tab;
  document.querySelectorAll("nav a").forEach(a => a.classList.toggle("active", a.dataset.tab === tab));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.toggle("active", c.id === "tab-" + tab));
};

const DATA = JSON.parse(document.getElementById("embedded-data").textContent);
const { global: globalRows, country, gender, age_band: ageBand } = DATA;

try { render(); }
catch (err) {
  document.querySelector(".shell").insertAdjacentHTML("afterbegin",
    `<div class="err"><b>Error:</b> ${err.message}</div>`);
  console.error(err);
}

function render() {
  const ym = d => `${d.year}-${String(d.month).padStart(2,"0")}`;
  const fmtPct = (v, d=1) => v == null ? "—" : (v*100).toFixed(d) + "%";
  const fmtSigned = (v, d=2) => v == null ? "—" : (v >= 0 ? "+" : "") + v.toFixed(d);

  const sortedGlobalAll = globalRows.filter(d => !d.suppressed).sort((a,b) => a.year-b.year || a.month-b.month);
  if (!sortedGlobalAll.length) throw new Error("No global data found — did the ETL run?");
  const sortedGlobal = sortedGlobalAll.filter(d => d.adoption_rate != null && d.adoption_rate >= 0.05);
  const globalWithImpact = sortedGlobal.filter(d => d.weighted_impact_index != null);
  const latest = (globalWithImpact.length ? globalWithImpact : sortedGlobal).slice(-1)[0];

  const MONTH_ABBR = ["", "Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const fmtMonthLabel = (ymStr) => {
    const [y, m] = ymStr.split("-");
    return `${MONTH_ABBR[+m]} '${y.slice(2)}`;
  };
  const monthKeys = sortedGlobal.map(ym);
  const tickEvery = monthKeys.length > 18 ? 3 : (monthKeys.length > 10 ? 2 : 1);
  const thinnedTicks = monthKeys.filter((_, i) => (monthKeys.length - 1 - i) % tickEvery === 0);

  // ======================================================================
  // Pooled-rows helper for rolling-window views
  // ======================================================================
  const NUMERIC_METRIC_KEYS = [
    "adoption_rate", "positive_impact_share", "negative_impact_share",
    "net_impact_index", "weighted_impact_index",
    "impact_share_improved_quality", "impact_share_new_opportunities",
    "impact_share_adaptation_pressure", "impact_share_job_anxiety",
    "impact_share_job_loss", "impact_share_reduced_income",
    "impact_share_none", "impact_share_other", "impact_share_not_sure",
    "freq_share_0","freq_share_1","freq_share_2","freq_share_3",
    "freq_share_4","freq_share_5","freq_share_6"
  ];
  function poolRows(rows) {
    if (!rows || !rows.length) return null;
    const totalN = rows.reduce((s, r) => s + (r.n_respondents || 0), 0);
    if (!totalN) return null;
    const out = { n_respondents: totalN, suppressed: false };
    for (const id of ["country_clean","gender_clean","age_band"]) {
      if (rows[0][id] !== undefined) out[id] = rows[0][id];
    }
    for (const k of NUMERIC_METRIC_KEYS) {
      let num = 0, den = 0;
      for (const r of rows) {
        if (r[k] == null) continue;
        num += r[k] * r.n_respondents;
        den += r.n_respondents;
      }
      out[k] = den ? num / den : null;
    }
    // Pool n_impact_denominator
    let denomSum = 0;
    for (const r of rows) { denomSum += r.n_impact_denominator || 0; }
    out.n_impact_denominator = denomSum;
    const dosePool = {};
    for (let lvl = 0; lvl <= 6; lvl++) {
      let num = 0, den = 0;
      for (const r of rows) {
        let d = r.dose_response;
        if (typeof d === "string") { try { d = JSON.parse(d); } catch { d = null; } }
        if (!d || d[lvl] == null) continue;
        num += d[lvl] * r.n_respondents;
        den += r.n_respondents;
      }
      if (den) dosePool[lvl] = num / den;
    }
    out.dose_response = dosePool;
    return out;
  }

  // ----- Static lookups -----
  const ageOrder = ["18-20","21-24","25-34","35-44","45-54","55-64","65-74","75-84","85+"];
  const FREQ_LABELS = ["Never","Rarely","Monthly","Weekly","Daily","Constantly","Always"];
  const countryNonSup = country.filter(d => !d.suppressed);
  const countryTotals = d3.rollups(countryNonSup, v => d3.sum(v, d => d.n_respondents), d => d.country_clean)
    .sort((a,b) => b[1] - a[1]);
  const topCountries = countryTotals.slice(0, 12).map(d => d[0]);

  // Impact flag weights for the composition chart (display only)
  const WEIGHTS = {
    impact_share_new_opportunities:   +1.0,
    impact_share_improved_quality:    +0.5,
    impact_share_adaptation_pressure: -0.5,
    impact_share_job_anxiety:         -0.25,
    impact_share_job_loss:            -1.0,
    impact_share_reduced_income:      -0.75,
    impact_share_none:                 0.0,
    impact_share_other:                0.0,
    impact_share_not_sure:             0.0
  };

  function unpackDose(rows, groupKey) {
    const out = [];
    for (const r of rows) {
      if (r.suppressed) continue;
      let dose = r.dose_response;
      if (typeof dose === "string") { try { dose = JSON.parse(dose); } catch { dose = null; } }
      if (!dose) continue;
      for (const [lvl, val] of Object.entries(dose)) {
        if (val == null) continue;
        out.push({ group: groupKey ? r[groupKey] : "Global",
          freq_label: FREQ_LABELS[Number(lvl)], net_impact: val });
      }
    }
    return out;
  }

  // ----- Resolve selection -----
  function resolveSelection(ymKey) {
    if (ymKey === "R3" || ymKey === "R6") {
      const n = ymKey === "R3" ? 3 : 6;
      const windowRows = globalWithImpact.slice(-n);
      if (!windowRows.length) return { selected: null };
      const windowKeys = windowRows.map(ym);
      const winSet = new Set(windowKeys);
      const inWin = r => winSet.has(`${r.year}-${String(r.month).padStart(2,"0")}`);

      const pooledGlobal = poolRows(windowRows);

      const genderByG = d3.group(gender.filter(r => !r.suppressed && inWin(r)), r => r.gender_clean);
      const genderPooled = Array.from(genderByG, ([g, rs]) => {
        const p = poolRows(rs); if (!p) return null; p.gender_clean = g; return p;
      }).filter(d => d && d.n_respondents >= 50 && d.weighted_impact_index != null);

      const ageByA = d3.group(ageBand.filter(r => !r.suppressed && inWin(r)), r => r.age_band);
      const agePooled = Array.from(ageByA, ([a, rs]) => {
        const p = poolRows(rs); if (!p) return null; p.age_band = a; return p;
      }).filter(d => d && d.n_respondents >= 50 && d.weighted_impact_index != null);

      const ctyByC = d3.group(countryNonSup.filter(r => inWin(r)), r => r.country_clean);
      const ctyPooledAll = Array.from(ctyByC, ([c, rs]) => {
        const p = poolRows(rs); if (!p) return null; p.country_clean = c; return p;
      }).filter(d => d && d.n_respondents >= 50 && d.weighted_impact_index != null);
      const ctyPooled = ctyPooledAll.filter(d => topCountries.includes(d.country_clean));

      return {
        isRolling: true, rollingN: n, windowMonths: windowKeys,
        selected: pooledGlobal, selGender: genderPooled, selAge: agePooled,
        selCountry: ctyPooled, selCountryAll: ctyPooledAll,
        doseGlobalRows: [pooledGlobal]
      };
    }
    const selected = globalWithImpact.find(d => ym(d) === ymKey);
    if (!selected) return { selected: null };
    const selGender = gender.filter(d => !d.suppressed && d.weighted_impact_index != null
      && d.year === selected.year && d.month === selected.month);
    const selAge = ageBand.filter(d => !d.suppressed && d.weighted_impact_index != null
      && d.year === selected.year && d.month === selected.month);
    const selCountryAll = countryNonSup.filter(d => d.weighted_impact_index != null
      && d.year === selected.year && d.month === selected.month);
    const selCountry = selCountryAll.filter(d => topCountries.includes(d.country_clean));
    return {
      isRolling: false, monthKey: ymKey,
      selected, selGender, selAge, selCountry, selCountryAll,
      doseGlobalRows: [selected]
    };
  }

  // ----- Time-series data (precomputed) -----
  const wiiTrend = [];
  for (const r of globalWithImpact) {
    if (r.weighted_impact_index != null) wiiTrend.push({ month: ym(r), wii: r.weighted_impact_index });
  }
  const latestMonthKey = ym(latest);
  const freqLong = [];
  for (const r of sortedGlobal) {
    for (let lvl = 0; lvl <= 6; lvl++) {
      const share = r[`freq_share_${lvl}`];
      if (share == null) continue;
      freqLong.push({ month: ym(r), label: FREQ_LABELS[lvl], lvl, share });
    }
  }

  // ----- Time-series renderer -----
  function renderTimeSeries(sel) {
    const indicator = sel.isRolling
      ? Plot.ruleX(sel.windowMonths, { stroke: "#444", strokeOpacity: 0.14, strokeWidth: 22 })
      : Plot.ruleX([sel.monthKey], { stroke: "#333", strokeDasharray: "4,3", strokeWidth: 1.5 });

    document.getElementById("chart-wii-time").replaceChildren(Plot.plot({
      height: 340, marginLeft: 70, marginRight: 80, marginBottom: 50, marginTop: 40,
      y: { label: "Weighted Impact Index", labelAnchor: "center", labelArrow: "none", grid: true, zero: true },
      x: { type: "band", label: null, ticks: thinnedTicks, tickFormat: fmtMonthLabel, tickRotate: -30 },
      marks: [
        indicator,
        Plot.ruleY([0], { stroke: "#ccc", strokeWidth: 1 }),
        Plot.lineY(wiiTrend, { x: "month", y: "wii", stroke: "#6366f1", strokeWidth: 2.5 }),
        Plot.dot(wiiTrend, { x: "month", y: "wii", fill: d => d.wii >= 0 ? "#1a7f4e" : "#b3261e", r: 5 }),
        Plot.text(wiiTrend.filter(d => d.month === latestMonthKey), {
          x: "month", y: "wii",
          text: d => (d.wii >= 0 ? "+" : "") + d.wii.toFixed(3),
          dx: 10, textAnchor: "start",
          fill: "#6366f1", fontWeight: 600, fontSize: 12
        })
      ]
    }));

    document.getElementById("chart-adoption").replaceChildren(Plot.plot({
      height: 260, marginBottom: 50,
      y: { grid: true, label: "% using AI at all", tickFormat: d => (d*100).toFixed(0)+"%", domain: [0,1] },
      x: { type: "band", label: null, ticks: thinnedTicks, tickFormat: fmtMonthLabel, tickRotate: -30 },
      marks: [
        Plot.barY(sortedGlobal, { x: ym, y: "adoption_rate", fill: "#2E5C8A" }),
        indicator
      ]
    }));

    document.getElementById("chart-freq-stack").replaceChildren(Plot.plot({
      height: 340, marginLeft: 60, marginBottom: 50, marginTop: 40,
      y: { grid: true, label: "Share", labelAnchor: "center", labelArrow: "none", tickFormat: d => (d*100).toFixed(0)+"%" },
      x: { type: "band", label: null, ticks: thinnedTicks, tickFormat: fmtMonthLabel, tickRotate: -30 },
      color: { legend: true, domain: FREQ_LABELS, scheme: "blues" },
      marks: [
        Plot.barY(freqLong, { x: "month", y: "share", fill: "label", order: "lvl" }),
        indicator
      ]
    }));
  }

  // ----- Country table -----
  const TABLE_COLS = [
    { key: "year",                   label: "Year",       cls: "",    fmt: d => d.year },
    { key: "month",                  label: "Month",      cls: "",    fmt: d => String(d.month).padStart(2,"0") },
    { key: "country_clean",          label: "Country",    cls: "",    fmt: d => d.country_clean ?? "" },
    { key: "n_respondents",          label: "N",          cls: "num", fmt: d => d.n_respondents },
    { key: "adoption_rate",          label: "Adoption",   cls: "num", fmt: d => d.adoption_rate == null ? "" : (d.adoption_rate*100).toFixed(1)+"%" },
    { key: "weighted_impact_index",  label: "Weighted Impact", cls: "num", fmt: d => d.weighted_impact_index == null ? "" : (d.weighted_impact_index>=0?"+":"") + d.weighted_impact_index.toFixed(3) },
    { key: "positive_impact_share",  label: "Positive",   cls: "num", fmt: d => d.positive_impact_share == null ? "" : (d.positive_impact_share*100).toFixed(1)+"%" },
    { key: "negative_impact_share",  label: "Negative",   cls: "num", fmt: d => d.negative_impact_share == null ? "" : (d.negative_impact_share*100).toFixed(1)+"%" }
  ];
  let tableSortKey = "weighted_impact_index";
  let tableSortAsc = false;
  let tableFilteredRows = countryNonSup;

  function drawTable(rows) {
    tableFilteredRows = rows;
    const sorted = rows.slice().sort((a,b) => {
      let va = a[tableSortKey] ?? (tableSortAsc ? Infinity : -Infinity);
      let vb = b[tableSortKey] ?? (tableSortAsc ? Infinity : -Infinity);
      if (typeof va === "string") va = va.toLowerCase();
      if (typeof vb === "string") vb = vb.toLowerCase();
      return tableSortAsc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
    });
    const arrow = k => k === tableSortKey ? (tableSortAsc ? " ▲" : " ▼") : "";
    document.getElementById("country-table").innerHTML = `
      <thead><tr>
        ${TABLE_COLS.map(c => `<th class="${c.cls} sortable" data-sort="${c.key}">${c.label}${arrow(c.key)}</th>`).join("")}
      </tr></thead><tbody>
      ${sorted.slice(0, 400).map(d => `<tr>
        ${TABLE_COLS.map(c => {
          const extra = c.key === "weighted_impact_index" ? (d.weighted_impact_index >= 0 ? " pos" : " neg") : "";
          return `<td class="${c.cls}${extra}">${c.fmt(d)}</td>`;
        }).join("")}
      </tr>`).join("")}
      </tbody>`;
    document.querySelectorAll("#country-table th.sortable").forEach(th => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (tableSortKey === key) { tableSortAsc = !tableSortAsc; }
        else { tableSortKey = key; tableSortAsc = (key === "country_clean" || key === "year" || key === "month"); }
        drawTable(tableFilteredRows);
      });
    });
  }
  drawTable(countryNonSup);
  document.getElementById("country-search").addEventListener("input", e => {
    const q = e.target.value.toLowerCase();
    drawTable(countryNonSup.filter(d => (d.country_clean||"").toLowerCase().includes(q)));
  });

  // ----- Populate month selector -----
  const availableMonths = globalWithImpact.slice().reverse();
  const selector = document.getElementById("month-selector");
  const singleOptsHtml = availableMonths.map(d => {
    const key = ym(d);
    return `<option value="${key}">${fmtMonthLabel(key)}</option>`;
  }).join("");
  selector.innerHTML = `
    <optgroup label="Rolling windows (pooled)">
      <option value="R3">Last 3 months</option>
      <option value="R6">Last 6 months</option>
    </optgroup>
    <optgroup label="Single month">${singleOptsHtml}</optgroup>
  `;

  const singleMonthKeys = availableMonths.map(ym).slice().reverse();
  const prevBtn = document.getElementById("month-prev");
  const nextBtn = document.getElementById("month-next");
  function updateNavButtons(ymKey) {
    if (ymKey === "R3" || ymKey === "R6") {
      prevBtn.disabled = false;
      prevBtn.title = "Jump to latest single month";
      nextBtn.disabled = true;
      nextBtn.title = "Disabled in pooled view";
      return;
    }
    const idx = singleMonthKeys.indexOf(ymKey);
    prevBtn.disabled = idx <= 0;
    prevBtn.title = "Previous month";
    nextBtn.disabled = idx < 0 || idx >= singleMonthKeys.length - 1;
    nextBtn.title = "Next month";
  }
  prevBtn.addEventListener("click", () => {
    const cur = selector.value;
    if (cur === "R3" || cur === "R6") {
      selector.value = singleMonthKeys.at(-1);
    } else {
      const idx = singleMonthKeys.indexOf(cur);
      if (idx <= 0) return;
      selector.value = singleMonthKeys[idx - 1];
    }
    renderMonth(selector.value);
  });
  nextBtn.addEventListener("click", () => {
    const cur = selector.value;
    if (cur === "R3" || cur === "R6") return;
    const idx = singleMonthKeys.indexOf(cur);
    if (idx < 0 || idx >= singleMonthKeys.length - 1) return;
    selector.value = singleMonthKeys[idx + 1];
    renderMonth(selector.value);
  });

  // ----- Composition chart with weights annotation -----
  let compUseSurvey = false;
  function drawCompositionChart(compRaw) {
    const labelKey = compUseSurvey ? "long" : "short";
    const compData = compRaw.map(d => ({ ...d, label: d[labelKey] }));
    const compMax = compData.length ? Math.max(...compData.map(d => d.share)) * 1.15 : 1;
    document.getElementById("chart-impact-composition").replaceChildren(Plot.plot({
      height: 280, marginLeft: compUseSurvey ? 310 : 180, marginRight: 80,
      x: { grid: true, tickFormat: d => (d*100).toFixed(0)+"%", label: "% of AI users", domain: [0, compMax] },
      y: { label: null },
      marks: [
        Plot.barX(compData, { y: "label", x: "share",
          fill: d => d.cat === "pos" ? "#1a7f4e" : d.cat === "neg" ? "#b3261e" : "#888",
          sort: { y: "x", reverse: true } }),
        Plot.text(compData, { y: "label", x: "share",
          text: d => `${(d.share*100).toFixed(1)}%  [w=${d.weight >= 0 ? "+" : ""}${d.weight.toFixed(2)}]`,
          textAnchor: "start", dx: 4, fontSize: 11 })
      ]
    }));
  }
  const compToggle = document.getElementById("comp-label-toggle");
  compToggle.addEventListener("click", () => {
    compUseSurvey = !compUseSurvey;
    compToggle.textContent = compUseSurvey ? "Short labels" : "Survey wording";
    if (window.__compRaw) drawCompositionChart(window.__compRaw);
  });

  // ----- Scatter chart -----
  function drawScatter() {
    const minN = +document.getElementById("scatter-min-n").value;
    const data = (window.__scatterCountryData || []).filter(d => d.n_respondents >= minN);
    document.getElementById("chart-country-scatter").replaceChildren(Plot.plot({
      height: 380, marginLeft: 80, marginRight: 120,
      x: { grid: true, label: "AI adoption rate", tickFormat: d => (d*100).toFixed(0)+"%" },
      y: { grid: true, label: "Weighted Impact Index" },
      marks: [
        Plot.ruleY([0], { stroke: "#bbb" }),
        Plot.dot(data, { x: "adoption_rate", y: "weighted_impact_index",
          r: d => Math.sqrt(d.n_respondents) / 2,
          fill: d => d.weighted_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
          fillOpacity: 0.7, stroke: "white" }),
        Plot.text(data, { x: "adoption_rate", y: "weighted_impact_index",
          text: "country_clean", dx: 12, textAnchor: "start", fontSize: 11 })
      ]
    }));
  }
  const scatterSlider = document.getElementById("scatter-min-n");
  const scatterLabel = document.getElementById("scatter-min-n-val");
  scatterSlider.addEventListener("input", () => {
    scatterLabel.textContent = scatterSlider.value;
    drawScatter();
  });

  // ----- Main rendering for current selection -----
  function renderMonth(ymKey) {
    const sel = resolveSelection(ymKey);
    if (!sel.selected) return;

    const isRolling = sel.isRolling;
    const shortLabel = isRolling ? `Last ${sel.rollingN} mo. (pooled)` : fmtMonthLabel(ymKey);
    const detailLabel = isRolling
      ? `${fmtMonthLabel(sel.windowMonths[0])} – ${fmtMonthLabel(sel.windowMonths.at(-1))} (pooled)`
      : fmtMonthLabel(ymKey);
    document.querySelectorAll(".sel-month").forEach(el => el.textContent = shortLabel);

    // --- KPI cards ---
    const selected = sel.selected;
    const wiiEl = document.getElementById("kpi-wii");
    wiiEl.textContent = fmtSigned(selected.weighted_impact_index, 3);
    wiiEl.style.color = selected.weighted_impact_index == null ? "var(--muted)"
      : (selected.weighted_impact_index >= 0 ? "var(--pos)" : "var(--neg)");
    const ciEl = document.getElementById("kpi-wii-ci");
    if (selected.weighted_impact_index_ci_low != null) {
      ciEl.textContent = `95% CI: [${selected.weighted_impact_index_ci_low.toFixed(3)}, ${selected.weighted_impact_index_ci_high.toFixed(3)}]`;
    } else {
      ciEl.textContent = detailLabel;
    }
    document.getElementById("kpi-n").textContent = Math.round(selected.n_respondents).toLocaleString();
    document.getElementById("kpi-n-sub").textContent = detailLabel;
    document.getElementById("kpi-adopt").textContent = fmtPct(selected.adoption_rate);
    document.getElementById("kpi-denom").textContent = selected.n_impact_denominator != null
      ? Math.round(selected.n_impact_denominator).toLocaleString() : "—";

    // --- Time-series ---
    renderTimeSeries(sel);

    // --- Impact composition with weights ---
    const compRaw = [
      { short: "New opportunities (+1.0)",  long: "Created new job or income opportunities",          share: selected.impact_share_new_opportunities,   cat: "pos", weight: +1.0  },
      { short: "Improved quality (+0.5)",   long: "Improved my work quality or output",               share: selected.impact_share_improved_quality,    cat: "pos", weight: +0.5  },
      { short: "Job anxiety (−0.25)",       long: "Made me worry about the future of my job or industry", share: selected.impact_share_job_anxiety,     cat: "neg", weight: -0.25 },
      { short: "Adaptation pressure (−0.5)",long: "Increased pressure to adapt or work faster",       share: selected.impact_share_adaptation_pressure, cat: "neg", weight: -0.5  },
      { short: "Reduced income (−0.75)",    long: "Reduced my income or made it harder to find work", share: selected.impact_share_reduced_income,      cat: "neg", weight: -0.75 },
      { short: "Job loss (−1.0)",           long: "Caused me to lose my job",                         share: selected.impact_share_job_loss,            cat: "neg", weight: -1.0  },
      { short: "No impact (0)",             long: "No impact",                                        share: selected.impact_share_none,                cat: "neu", weight: 0     },
      { short: "Other (0)",                 long: "Another impact not listed here",                   share: selected.impact_share_other,               cat: "neu", weight: 0     },
      { short: "Not sure (0)",              long: "Not sure",                                         share: selected.impact_share_not_sure,            cat: "neu", weight: 0     }
    ].filter(d => d.share != null);
    window.__compRaw = compRaw;
    drawCompositionChart(compRaw);

    // --- Gender bar chart using weighted index ---
    document.getElementById("chart-gender").replaceChildren(Plot.plot({
      height: 240, marginLeft: 120,
      x: { grid: true, label: "Weighted Impact Index", domain: [-0.3, 0.4] },
      y: { label: null },
      marks: [
        Plot.ruleX([0], { stroke: "#bbb" }),
        Plot.barX(sel.selGender, { y: "gender_clean", x: "weighted_impact_index",
          fill: d => d.weighted_impact_index >= 0 ? "#1a7f4e" : "#b3261e", sort: { y: "x" } })
      ]
    }));

    // --- Age band bar chart using weighted index ---
    document.getElementById("chart-age").replaceChildren(Plot.plot({
      height: 240, marginLeft: 60,
      x: { grid: true, label: "Weighted Impact Index", domain: [-0.3, 0.4] },
      y: { domain: ageOrder, label: null },
      marks: [
        Plot.ruleX([0], { stroke: "#bbb" }),
        Plot.barX(sel.selAge, { y: "age_band", x: "weighted_impact_index",
          fill: d => d.weighted_impact_index >= 0 ? "#1a7f4e" : "#b3261e" })
      ]
    }));

    // --- Country: top-12 bars + scatter ---
    document.getElementById("chart-country-bar").replaceChildren(Plot.plot({
      height: 360, marginLeft: 140,
      x: { grid: true, label: "Weighted Impact Index", domain: [-0.3, 0.5] },
      y: { label: null },
      marks: [
        Plot.ruleX([0], { stroke: "#bbb" }),
        Plot.barX(sel.selCountry, { y: "country_clean", x: "weighted_impact_index",
          fill: d => d.weighted_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
          sort: { y: "x", reverse: true } })
      ]
    }));

    window.__scatterCountryData = sel.selCountryAll;
    drawScatter();
    document.getElementById("scatter-min-n-val").textContent = document.getElementById("scatter-min-n").value;

    // --- Dose-response (still uses NII since that's what _aggregate computes per freq level) ---
    const doseGlobal = unpackDose(sel.doseGlobalRows);
    document.getElementById("chart-dose-global").replaceChildren(Plot.plot({
      height: 300, marginLeft: 70,
      x: { domain: FREQ_LABELS, label: "AI frequency" },
      y: { grid: true, label: "Net Impact Index", labelAnchor: "center", labelArrow: "none", domain: [-0.2, 0.6] },
      marks: [
        Plot.ruleY([0], { stroke: "#bbb" }),
        Plot.lineY(doseGlobal, { x: "freq_label", y: "net_impact", stroke: "#6366f1", strokeWidth: 2.5 }),
        Plot.dot(doseGlobal, { x: "freq_label", y: "net_impact", fill: "#6366f1", r: 6 }),
        Plot.text(doseGlobal, { x: "freq_label", y: "net_impact",
          text: d => fmtSigned(d.net_impact, 2), dy: -14, fontSize: 11 })
      ]
    }));

    const doseGender = unpackDose(sel.selGender, "gender_clean");
    document.getElementById("chart-dose-gender").replaceChildren(Plot.plot({
      height: 300, marginLeft: 60, marginTop: 40,
      x: { domain: FREQ_LABELS, label: "AI frequency" },
      y: { grid: true, label: "Net Impact Index", labelAnchor: "center", labelArrow: "none" },
      color: { legend: true },
      marks: [
        Plot.ruleY([0], { stroke: "#bbb" }),
        Plot.lineY(doseGender, { x: "freq_label", y: "net_impact", stroke: "group", strokeWidth: 2 }),
        Plot.dot(doseGender, { x: "freq_label", y: "net_impact", fill: "group", r: 4 })
      ]
    }));

    const doseAge = unpackDose(sel.selAge, "age_band");
    document.getElementById("chart-dose-age").replaceChildren(Plot.plot({
      height: 320, marginLeft: 60, marginTop: 60,
      x: { domain: FREQ_LABELS, label: "AI frequency" },
      y: { grid: true, label: "Net Impact Index", labelAnchor: "center", labelArrow: "none" },
      color: { legend: true, domain: ageOrder },
      marks: [
        Plot.ruleY([0], { stroke: "#bbb" }),
        Plot.lineY(doseAge, { x: "freq_label", y: "net_impact", stroke: "group", strokeWidth: 2 }),
        Plot.dot(doseAge, { x: "freq_label", y: "net_impact", fill: "group", r: 4 })
      ]
    }));

    updateNavButtons(ymKey);
  }

  // Wire up and render initial view
  selector.value = ym(latest);
  selector.addEventListener("change", e => renderMonth(e.target.value));
  renderMonth(ym(latest));
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
