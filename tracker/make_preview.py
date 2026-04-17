"""
Bake a self-contained preview.html with the metric data embedded inline.

Reads the Parquet metric layer written by main.py and produces
`dashboard/preview.html` with the data as a <script> JSON blob. The
resulting file opens directly via double-click (no server, no DuckDB-WASM)
and still loads Observable Plot + d3 from CDN for visuals.

Run AFTER main.py:

    python3 make_preview.py

Output: ../dashboard/preview.html (overwrites)
"""
from __future__ import annotations

import glob, json, math
from pathlib import Path
import pandas as pd


HERE = Path(__file__).parent
TRACKER_OUT = HERE / "output" / "v1" / "metrics"
DASHBOARD_DIR = HERE.parent / "dashboard"
OUT_HTML = DASHBOARD_DIR / "preview.html"


def load_level(level: str) -> list[dict]:
    files = sorted(TRACKER_OUT.glob(f"stratum_level={level}/**/part-0.parquet"))
    if not files:
        print(f"  warning: no files found for level={level}")
        return []
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    # Parquet -> JSON-safe records
    df = df.replace({float("nan"): None})
    # Coerce NumPy types to native Python for json.dumps
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

    html = HTML_TEMPLATE.replace("__DATA_JSON__", payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"\nWrote {OUT_HTML}")
    print("Open by double-clicking the file — no server needed.")


# ---------------------------------------------------------------------------
# Single-file dashboard template. Data gets inlined where __DATA_JSON__ sits.
# Plot + d3 still come from CDN; those are CSS/JS, not data.
# ---------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AI Use Impact Tracker — Preview</title>
<style>
  :root { --ink:#1a1a1a; --muted:#6b7280; --accent:#1F3A5F; --accent2:#2E5C8A;
          --pos:#1a7f4e; --neg:#b3261e; --rule:#e5e7eb; --chip:#E8EEF4; }
  html, body { margin: 0; background: #f6f7f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: var(--ink); }
  .shell { max-width: 1200px; margin: 0 auto; padding: 32px 40px 60px; }
  header { padding-bottom: 20px; border-bottom: 1px solid var(--rule); margin-bottom: 28px; }
  h1 { color: var(--accent); margin: 0 0 6px; font-size: 28px; }
  header p { color: var(--muted); margin: 0; max-width: 720px; }
  nav { margin-top: 12px; display: flex; gap: 16px; }
  nav a { color: var(--accent2); text-decoration: none; font-weight: 500; font-size: 14px; cursor: pointer; padding: 6px 10px; border-radius: 6px; }
  nav a.active { background: var(--chip); color: var(--accent); }
  h2 { color: var(--accent); font-size: 18px; margin: 28px 0 10px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 24px; }
  @media (max-width: 1000px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  .card { background: #fff; padding: 16px 18px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
  .card .label { font-size: 12px; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .card .value { font-size: 28px; font-weight: 600; color: var(--accent); }
  .card .sub { font-size: 12px; color: var(--muted); margin-top: 4px; }
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
</style>
</head>
<body>
<div class="shell">

<header>
  <h1>AI Use Impact Tracker</h1>
  <p>How frequency of AI use relates to self-reported impact on work — tracked monthly across countries, gender, and age. Built on the Global Mind Project by Sapien Labs.</p>
  <nav>
    <a data-tab="overview"   class="active" onclick="showTab(event)">Overview</a>
    <a data-tab="countries"  onclick="showTab(event)">By country</a>
    <a data-tab="frequency"  onclick="showTab(event)">Frequency &amp; impact</a>
    <a data-tab="about"      onclick="showTab(event)">Methodology</a>
  </nav>
</header>

<div class="month-bar">
  <label for="month-selector">Showing data for:</label>
  <button id="month-prev" class="month-nav" aria-label="Previous month" title="Previous month">◀</button>
  <select id="month-selector" aria-label="Select month"></select>
  <button id="month-next" class="month-nav" aria-label="Next month" title="Next month">▶</button>
  <span class="hint">Single-month views update with the selection; the shaded band on the time-series marks the selected period. Rolling-window options pool months using n_respondents as weights (approximate).</span>
</div>

<div id="tab-overview" class="tab-content active">
  <div class="kpi-grid">
    <div class="card"><div class="label">Respondents</div><div class="value" id="kpi-n">—</div><div class="sub" id="kpi-n-sub"></div></div>
    <div class="card"><div class="label">AI Adoption Rate</div><div class="value" id="kpi-adopt">—</div><div class="sub">share using AI at all</div></div>
    <div class="card"><div class="label">Positive-impact Share</div><div class="value" id="kpi-pos" style="color:var(--pos)">—</div><div class="sub">quality ↑ or new opportunities</div></div>
    <div class="card"><div class="label">Negative-impact Share</div><div class="value" id="kpi-neg" style="color:var(--neg)">—</div><div class="sub">adaptation pressure or job anxiety</div></div>
    <div class="card"><div class="label">Net Impact Index</div><div class="value" id="kpi-net">—</div><div class="sub">positive − negative, range [−1, 1]</div></div>
  </div>

  <div class="panel"><h3>Positive and Negative impact share over time — global</h3>
    <p class="muted" style="margin:-4px 0 8px">Two sides of the Net Impact Index. When the green line climbs faster than the red one, NII rises because users feel more positive; when the red line falls, NII rises because users feel less anxious or pressured. Both stories matter.</p>
    <div id="chart-net-time"></div>
  </div>

  <div class="two-col">
    <div class="panel"><h3>AI adoption rate — global</h3><div id="chart-adoption"></div></div>
    <div class="panel"><h3>Impact share composition — <span class="sel-month">—</span>
        <button id="comp-label-toggle" class="label-toggle" title="Toggle between short labels and survey wording">Survey wording</button>
      </h3><div id="chart-impact-composition"></div></div>
  </div>

  <div class="two-col">
    <div class="panel"><h3>Net Impact by gender — <span class="sel-month">—</span></h3><div id="chart-gender"></div></div>
    <div class="panel"><h3>Net Impact by age band — <span class="sel-month">—</span></h3><div id="chart-age"></div></div>
  </div>
</div>

<div id="tab-countries" class="tab-content">
  <div class="panel"><h3>Top 12 countries — ranked by Net Impact Index — <span class="sel-month">—</span></h3><div id="chart-country-bar"></div></div>
  <div class="panel">
    <h3>Adoption rate × Net Impact — <span class="sel-month">—</span></h3>
    <p class="muted">Dot size encodes total respondent count (all survey takers in that country-month, not just AI users).</p>
    <div class="scatter-controls">
      <label for="scatter-min-n">Min N:</label>
      <input type="range" id="scatter-min-n" min="50" max="500" step="10" value="50">
      <span id="scatter-min-n-val">50</span>
    </div>
    <div id="chart-country-scatter"></div>
  </div>
  <div class="panel">
    <h3>All country-months (n ≥ 50)</h3>
    <p><input type="text" id="country-search" placeholder="Filter countries…" style="width:260px"></p>
    <div style="max-height: 400px; overflow: auto;"><table id="country-table"></table></div>
  </div>
</div>

<div id="tab-frequency" class="tab-content">
  <div class="panel"><h3>Global dose-response — <span class="sel-month">—</span></h3>
    <p class="muted">Net Impact Index at each AI-use frequency level.</p>
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
    <h3>Methodology</h3>
    <p><b>Source.</b> Global Mind Project (GMP), Sapien Labs. Phase 1 reads a monthly CSV extract; Phase 2 will read directly from GMP's Elasticsearch cluster.</p>
    <p><b>Exposure — ai_freq.</b> A 7-level ordinal: Never (0), Rarely (1), Monthly (2), Weekly (3), Daily (4), Constantly (5), Always (6).</p>
    <p><b>Outcome — ai_impact_work.</b> Multi-select pipe-delimited, split into seven binary flags. <i>Improved quality</i> and <i>new opportunities</i> are positive; <i>adaptation pressure</i> and <i>job anxiety</i> are negative.</p>
    <p><b>Net Impact Index</b> = positive-impact share − negative-impact share. Range [−1, +1]. Denominator: AI users with at least one non-null impact response.</p>
    <p><b>Suppression.</b> Cells with n &lt; 50 respondents are suppressed. 95% Wilson score CIs for share metrics.</p>
    <p><b>Phase 1 limitations.</b> No survey weights; associations are descriptive, not causal. Month-over-month shifts may reflect composition effects rather than attitudinal change.</p>
  </div>
</div>

<footer>Global Mind Project — Sapien Labs • Phase 1 Preview</footer>
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
  // Many pre-2025 GMP months did not yet include the AI questions — these
  // rows report 0% adoption not because nobody used AI but because nobody was
  // asked. Treat "adoption essentially zero" as "question not asked" and drop.
  const sortedGlobal = sortedGlobalAll.filter(d => d.adoption_rate != null && d.adoption_rate >= 0.05);
  // "latest" = most recent month that actually has an impact metric computed
  const globalWithImpact = sortedGlobal.filter(d => d.net_impact_index != null);
  const latest = (globalWithImpact.length ? globalWithImpact : sortedGlobal).slice(-1)[0];

  // Compact month labels: "2024-04" → "Apr '24". Keeps the axis readable
  // at any density without aggressive rotation.
  const MONTH_ABBR = ["", "Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const fmtMonthLabel = (ymStr) => {
    const [y, m] = ymStr.split("-");
    return `${MONTH_ABBR[+m]} '${y.slice(2)}`;
  };
  // If there are many months, thin ticks so they don't overlap.
  const monthKeys = sortedGlobal.map(ym);
  const tickEvery = monthKeys.length > 18 ? 3 : (monthKeys.length > 10 ? 2 : 1);
  const thinnedTicks = monthKeys.filter((_, i) => (monthKeys.length - 1 - i) % tickEvery === 0);

  // ======================================================================
  // Pooled-rows helper for rolling-window ("Last N months") views.
  // Weights each month's metric by n_respondents. Approximate: the exact
  // denominator for impact_share_* is AI users who answered the impact
  // question, which differs from n_respondents. Within a short window
  // (3-6 mo) with stable NA rates, this stays within ~1pp of exact.
  // ======================================================================
  const NUMERIC_METRIC_KEYS = [
    "adoption_rate", "positive_impact_share", "negative_impact_share", "net_impact_index",
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

  // ----- Static lookups (month-independent) -----
  const ageOrder = ["18-20","21-24","25-34","35-44","45-54","55-64","65-74","75-84","85+"];
  const FREQ_LABELS = ["Never","Rarely","Monthly","Weekly","Daily","Constantly","Always"];
  const countryNonSup = country.filter(d => !d.suppressed);
  const countryTotals = d3.rollups(countryNonSup, v => d3.sum(v, d => d.n_respondents), d => d.country_clean)
    .sort((a,b) => b[1] - a[1]);
  const topCountries = countryTotals.slice(0, 12).map(d => d[0]);

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

  // ----- Resolve the selector value into a pooled or single-month selection -----
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
      }).filter(d => d && d.n_respondents >= 50 && d.net_impact_index != null);

      const ageByA = d3.group(ageBand.filter(r => !r.suppressed && inWin(r)), r => r.age_band);
      const agePooled = Array.from(ageByA, ([a, rs]) => {
        const p = poolRows(rs); if (!p) return null; p.age_band = a; return p;
      }).filter(d => d && d.n_respondents >= 50 && d.net_impact_index != null);

      const ctyByC = d3.group(countryNonSup.filter(r => inWin(r)), r => r.country_clean);
      const ctyPooledAll = Array.from(ctyByC, ([c, rs]) => {
        const p = poolRows(rs); if (!p) return null; p.country_clean = c; return p;
      }).filter(d => d && d.n_respondents >= 50 && d.net_impact_index != null);
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
    const selGender = gender.filter(d => !d.suppressed && d.net_impact_index != null
      && d.year === selected.year && d.month === selected.month);
    const selAge = ageBand.filter(d => !d.suppressed && d.net_impact_index != null
      && d.year === selected.year && d.month === selected.month);
    const selCountryAll = countryNonSup.filter(d => d.net_impact_index != null
      && d.year === selected.year && d.month === selected.month);
    const selCountry = selCountryAll.filter(d => topCountries.includes(d.country_clean));
    return {
      isRolling: false, monthKey: ymKey,
      selected, selGender, selAge, selCountry, selCountryAll,
      doseGlobalRows: [selected]
    };
  }

  // ----- Twin-line + freq-stack precomputed once (data itself is month-indep) -----
  const trendLong = [];
  for (const r of globalWithImpact) {
    if (r.positive_impact_share != null) trendLong.push({ month: ym(r), share: r.positive_impact_share, series: "Positive", nii: r.net_impact_index });
    if (r.negative_impact_share != null) trendLong.push({ month: ym(r), share: r.negative_impact_share, series: "Negative", nii: r.net_impact_index });
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

  // ----- Time-series renderer: re-runs on selection change so the selection
  //       indicator (dashed rule for single month, shaded band for rolling)
  //       reflects the current view. -----
  function renderTimeSeries(sel) {
    const indicator = sel.isRolling
      ? Plot.ruleX(sel.windowMonths, { stroke: "#444", strokeOpacity: 0.14, strokeWidth: 22 })
      : Plot.ruleX([sel.monthKey], { stroke: "#333", strokeDasharray: "4,3", strokeWidth: 1.5 });

    document.getElementById("chart-net-time").replaceChildren(Plot.plot({
      height: 340, marginLeft: 70, marginRight: 80, marginBottom: 50, marginTop: 40,
      y: { label: "Share of AI users with impact answer", labelAnchor: "center", labelArrow: "none", grid: true, tickFormat: d => (d * 100).toFixed(0) + "%", zero: true },
      x: { type: "band", label: null, ticks: thinnedTicks, tickFormat: fmtMonthLabel, tickRotate: -30 },
      color: { domain: ["Positive", "Negative"], range: ["#1a7f4e", "#b3261e"], legend: true },
      marks: [
        indicator,
        Plot.lineY(trendLong, { x: "month", y: "share", stroke: "series", strokeWidth: 2.5 }),
        Plot.dot(trendLong, { x: "month", y: "share", fill: "series", r: 5 }),
        Plot.text(trendLong.filter(d => d.month === latestMonthKey), {
          x: "month", y: "share",
          text: d => (d.share * 100).toFixed(1) + "%",
          dx: 10, textAnchor: "start",
          fill: d => d.series === "Positive" ? "#1a7f4e" : "#b3261e",
          fontWeight: 600, fontSize: 12
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

  // ----- Country table (full history — sortable columns) -----
  const TABLE_COLS = [
    { key: "year",                  label: "Year",       cls: "",    fmt: d => d.year },
    { key: "month",                 label: "Month",      cls: "",    fmt: d => String(d.month).padStart(2,"0") },
    { key: "country_clean",         label: "Country",    cls: "",    fmt: d => d.country_clean ?? "" },
    { key: "n_respondents",         label: "N",          cls: "num", fmt: d => d.n_respondents },
    { key: "adoption_rate",         label: "Adoption",   cls: "num", fmt: d => d.adoption_rate == null ? "" : (d.adoption_rate*100).toFixed(1)+"%" },
    { key: "positive_impact_share", label: "Positive",   cls: "num", fmt: d => d.positive_impact_share == null ? "" : (d.positive_impact_share*100).toFixed(1)+"%" },
    { key: "negative_impact_share", label: "Negative",   cls: "num", fmt: d => d.negative_impact_share == null ? "" : (d.negative_impact_share*100).toFixed(1)+"%" },
    { key: "net_impact_index",      label: "Net Impact", cls: "num", fmt: d => d.net_impact_index == null ? "" : (d.net_impact_index>=0?"+":"") + d.net_impact_index.toFixed(3) }
  ];
  let tableSortKey = "net_impact_index";
  let tableSortAsc = false;  // default: highest NII first
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
          const extra = c.key === "net_impact_index" ? (d.net_impact_index >= 0 ? " pos" : " neg") : "";
          return `<td class="${c.cls}${extra}">${c.fmt(d)}</td>`;
        }).join("")}
      </tr>`).join("")}
      </tbody>`;
    // Attach click handlers to <th> for sorting
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

  // ----- Populate the month selector (rolling windows + single months) -----
  const availableMonths = globalWithImpact.slice().reverse();  // latest first
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

  // Chronological (oldest-first) list for prev/next navigation
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

  // ----- Composition chart renderer + label toggle -----
  let compUseSurvey = false;  // false = short labels, true = survey wording
  function drawCompositionChart(compRaw) {
    const labelKey = compUseSurvey ? "long" : "short";
    const compData = compRaw.map(d => ({ ...d, label: d[labelKey] }));
    const compMax = compData.length ? Math.max(...compData.map(d => d.share)) * 1.15 : 1;
    document.getElementById("chart-impact-composition").replaceChildren(Plot.plot({
      height: 260, marginLeft: compUseSurvey ? 310 : 140, marginRight: 60,
      x: { grid: true, tickFormat: d => (d*100).toFixed(0)+"%", label: "% of AI users", domain: [0, compMax] },
      y: { label: null },
      marks: [
        Plot.barX(compData, { y: "label", x: "share",
          fill: d => d.cat === "pos" ? "#1a7f4e" : d.cat === "neg" ? "#b3261e" : "#888",
          sort: { y: "x", reverse: true } }),
        Plot.text(compData, { y: "label", x: "share",
          text: d => (d.share*100).toFixed(1) + "%", textAnchor: "start", dx: 4, fontSize: 11 })
      ]
    }));
  }
  const compToggle = document.getElementById("comp-label-toggle");
  compToggle.addEventListener("click", () => {
    compUseSurvey = !compUseSurvey;
    compToggle.textContent = compUseSurvey ? "Short labels" : "Survey wording";
    if (window.__compRaw) drawCompositionChart(window.__compRaw);
  });

  // ----- Scatter chart renderer + min-N slider -----
  function drawScatter() {
    const minN = +document.getElementById("scatter-min-n").value;
    const data = (window.__scatterCountryData || []).filter(d => d.n_respondents >= minN);
    document.getElementById("chart-country-scatter").replaceChildren(Plot.plot({
      height: 380, marginLeft: 80, marginRight: 30,
      x: { grid: true, label: "AI adoption rate", tickFormat: d => (d*100).toFixed(0)+"%" },
      y: { grid: true, label: "Net Impact Index" },
      marks: [
        Plot.ruleY([0], { stroke: "#bbb" }),
        Plot.dot(data, { x: "adoption_rate", y: "net_impact_index",
          r: d => Math.sqrt(d.n_respondents) / 2,
          fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
          fillOpacity: 0.7, stroke: "white" }),
        Plot.text(data, { x: "adoption_rate", y: "net_impact_index",
          text: "country_clean", dx: -12, textAnchor: "end", fontSize: 11 })
      ]
    }));
  }
  const scatterSlider = document.getElementById("scatter-min-n");
  const scatterLabel = document.getElementById("scatter-min-n-val");
  scatterSlider.addEventListener("input", () => {
    scatterLabel.textContent = scatterSlider.value;
    drawScatter();
  });

  // ----- Main rendering for the current selection (single month or pooled) -----
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
    document.getElementById("kpi-n").textContent = Math.round(selected.n_respondents).toLocaleString();
    document.getElementById("kpi-n-sub").textContent = detailLabel;
    document.getElementById("kpi-adopt").textContent = fmtPct(selected.adoption_rate);
    document.getElementById("kpi-pos").textContent = fmtPct(selected.positive_impact_share);
    document.getElementById("kpi-neg").textContent = fmtPct(selected.negative_impact_share);
    const netEl = document.getElementById("kpi-net");
    netEl.textContent = fmtSigned(selected.net_impact_index, 3);
    netEl.style.color = selected.net_impact_index == null ? "var(--muted)"
      : (selected.net_impact_index >= 0 ? "var(--pos)" : "var(--neg)");

    // --- Time-series with selection indicator ---
    renderTimeSeries(sel);

    // --- Impact composition (two label sets: short / survey wording) ---
    const compRaw = [
      { short: "Improved quality",    long: "Improved my work quality or output",                share: selected.impact_share_improved_quality,    cat: "pos" },
      { short: "New opportunities",   long: "Created new job or income opportunities",          share: selected.impact_share_new_opportunities,   cat: "pos" },
      { short: "Adaptation pressure", long: "Increased pressure to adapt or work faster",       share: selected.impact_share_adaptation_pressure, cat: "neg" },
      { short: "Job anxiety",         long: "Made me worry about the future of my job or industry", share: selected.impact_share_job_anxiety,     cat: "neg" },
      { short: "Job loss",            long: "Caused me to lose my job",                          share: selected.impact_share_job_loss,            cat: "neg" },
      { short: "Reduced income",      long: "Reduced my income or made it harder to find work",  share: selected.impact_share_reduced_income,      cat: "neg" },
      { short: "No impact",           long: "No impact",                                        share: selected.impact_share_none,                cat: "neu" },
      { short: "Other",               long: "Another impact not listed here",                   share: selected.impact_share_other,               cat: "neu" },
      { short: "Not sure",            long: "Not sure",                                         share: selected.impact_share_not_sure,            cat: "neu" }
    ].filter(d => d.share != null);
    // Store so the toggle can re-render without re-resolving the whole month
    window.__compRaw = compRaw;
    drawCompositionChart(compRaw);

    // --- Gender ---
    document.getElementById("chart-gender").replaceChildren(Plot.plot({
      height: 240, marginLeft: 120,
      x: { grid: true, label: "Net Impact Index", domain: [-0.4, 0.5] },
      y: { label: null },
      marks: [
        Plot.ruleX([0], { stroke: "#bbb" }),
        Plot.barX(sel.selGender, { y: "gender_clean", x: "net_impact_index",
          fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e", sort: { y: "x" } })
      ]
    }));

    // --- Age band ---
    document.getElementById("chart-age").replaceChildren(Plot.plot({
      height: 240, marginLeft: 60,
      x: { grid: true, label: "Net Impact Index", domain: [-0.4, 0.5] },
      y: { domain: ageOrder, label: null },
      marks: [
        Plot.ruleX([0], { stroke: "#bbb" }),
        Plot.barX(sel.selAge, { y: "age_band", x: "net_impact_index",
          fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e" })
      ]
    }));

    // --- Country: top-12 bars + scatter ---
    document.getElementById("chart-country-bar").replaceChildren(Plot.plot({
      height: 360, marginLeft: 140,
      x: { grid: true, label: "Net Impact Index", domain: [-0.3, 0.7] },
      y: { label: null },
      marks: [
        Plot.ruleX([0], { stroke: "#bbb" }),
        Plot.barX(sel.selCountry, { y: "country_clean", x: "net_impact_index",
          fill: d => d.net_impact_index >= 0 ? "#1a7f4e" : "#b3261e",
          sort: { y: "x", reverse: true } }),
        Plot.text(sel.selCountry, { y: "country_clean", x: "net_impact_index",
          text: d => fmtSigned(d.net_impact_index, 2),
          dx: d => d.net_impact_index >= 0 ? 4 : -4,
          textAnchor: d => d.net_impact_index >= 0 ? "start" : "end" })
      ]
    }));

    // Scatter: store full country data for min-N filtering
    window.__scatterCountryData = sel.selCountryAll;
    drawScatter();

    // Update slider label display
    document.getElementById("scatter-min-n-val").textContent = document.getElementById("scatter-min-n").value;

    // --- Dose-response: global, gender, age ---
    const doseGlobal = unpackDose(sel.doseGlobalRows);
    document.getElementById("chart-dose-global").replaceChildren(Plot.plot({
      height: 300, marginLeft: 70,
      x: { domain: FREQ_LABELS, label: "AI frequency" },
      y: { grid: true, label: "Net Impact Index", labelAnchor: "center", labelArrow: "none", domain: [-0.2, 0.6] },
      marks: [
        Plot.ruleY([0], { stroke: "#bbb" }),
        Plot.lineY(doseGlobal, { x: "freq_label", y: "net_impact", stroke: "#1F3A5F", strokeWidth: 2.5 }),
        Plot.dot(doseGlobal, { x: "freq_label", y: "net_impact", fill: "#1F3A5F", r: 6 }),
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

  // Wire up and render initial view (latest single month)
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
