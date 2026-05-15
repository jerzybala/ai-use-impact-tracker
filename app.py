"""
AI Use Impact Tracker — web application.

Wraps the existing ETL + dashboard bake pipeline behind a Flask UI.
Users upload (or point to) a CSV, the pipeline runs, and the dashboard
is served back.

    python app.py          # local dev on port 5000
    gunicorn app:app       # production (Railway)
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

from flask import (
    Flask,
    redirect,
    render_template_string,
    request,
    send_file,
    send_from_directory,
    url_for,
    jsonify,
)

# ---------------------------------------------------------------------------
# Make tracker/ importable regardless of how the app is launched
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tracker"))
import json, math                                              # noqa: E402

# Defer heavy tracker imports — if they fail, the app still starts and
# shows a useful error in Railway's runtime logs instead of a silent crash.
run_etl = None
HTML_TEMPLATE = None
build_payload = None
try:
    from tracker.main import run as run_etl                              # noqa: E402
    from tracker.make_dashboard import (                                 # noqa: E402
        HTML_TEMPLATE, build_payload, bake_html, load_meta,
    )
    print("[app] Tracker imports OK", flush=True)
except Exception as exc:
    print(f"[app] WARNING: tracker import failed: {exc}", flush=True)
    import traceback; traceback.print_exc()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2 GB upload limit
print(f"[app] Flask app created, PORT={os.environ.get('PORT','(not set)')}", flush=True)


@app.route("/health")
def health():
    """Simple health check that always responds."""
    return "ok"

DATA_DIR = Path(os.environ.get("DATA_DIR", HERE / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DOCS_DIR = HERE / "docs"

# Path to a pre-bundled CSV that ships with the deployment (e.g. uploaded
# once to a Railway Volume). When present, the upload page shows a
# one-click "Use latest GMP extract" option that runs the pipeline against
# this file. Override with the BUNDLED_CSV_PATH env var.
BUNDLED_CSV_PATH = Path(os.environ.get("BUNDLED_CSV_PATH", "/data/bundled.csv"))


def bundled_csv_meta() -> dict | None:
    """Return display info for the bundled CSV, or None if not present."""
    if not BUNDLED_CSV_PATH.is_file():
        return None
    st = BUNDLED_CSV_PATH.stat()
    size_mb = st.st_size / (1024 * 1024)
    return {
        "path": str(BUNDLED_CSV_PATH),
        "size_mb": f"{size_mb:.0f}",
        "mtime": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)),
    }

# In-memory job registry: job_id → {status, progress, error, html_path, ...}
JOBS: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Landing page — upload or point to a file
# ---------------------------------------------------------------------------
UPLOAD_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>AI Use Impact Tracker</title>
<style>
  :root { --accent:#1F3A5F; --accent2:#2E5C8A; --rule:#e5e7eb; --chip:#E8EEF4; --muted:#6b7280; }
  html, body { margin:0; background:#f6f7f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color:#1a1a1a; }
  .shell { max-width:680px; margin:80px auto; padding:0 24px; }
  h1 { color:var(--accent); font-size:26px; margin:0 0 8px; }
  p.sub { color:var(--muted); margin:0 0 32px; }
  .card { background:#fff; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.07); padding:28px 32px; margin-bottom:20px; }
  .card h2 { margin:0 0 16px; font-size:17px; color:var(--accent); }
  label { display:block; font-size:13px; font-weight:600; color:var(--accent); margin-bottom:6px; }
  input[type="file"], input[type="text"] { width:100%; padding:10px; border:1px solid var(--rule); border-radius:8px; font-size:14px; box-sizing:border-box; }
  input[type="file"] { padding:8px; background:#fafafa; }
  .or { text-align:center; color:var(--muted); font-size:13px; margin:18px 0; }
  button { background:var(--accent); color:#fff; border:none; border-radius:8px; padding:12px 28px; font-size:15px; font-weight:600; cursor:pointer; margin-top:12px; }
  button:hover { background:var(--accent2); }
  button:disabled { opacity:0.5; cursor:not-allowed; }
  #status { margin-top:18px; padding:14px; border-radius:8px; font-size:14px; display:none; }
  #status.running { display:block; background:#eef6ff; color:var(--accent); }
  #status.done    { display:block; background:#e8f5e9; color:#1a7f4e; }
  #status.error   { display:block; background:#fdecec; color:#b3261e; }
  .spinner { display:inline-block; width:14px; height:14px; border:2px solid var(--accent2); border-top-color:transparent; border-radius:50%; animation:spin .7s linear infinite; vertical-align:middle; margin-right:8px; }
  @keyframes spin { to { transform:rotate(360deg); } }
  footer { text-align:center; color:var(--muted); font-size:12px; margin-top:40px; }
  a { color:var(--accent2); }

  /* Previous dashboards list */
  .sessions { margin-top:8px; }
  .sessions .row { display:flex; align-items:center; justify-content:space-between; padding:6px 0; gap:12px; border-bottom:1px solid #f1f3f5; }
  .sessions .row:last-child { border-bottom:none; }
  .sessions .row a { font-size:14px; color:var(--accent2); text-decoration:none; }
  .sessions .row a:hover { text-decoration:underline; }
  .del-btn { background:transparent; border:1px solid var(--rule); color:#9ca3af; font-size:12px; padding:4px 10px; border-radius:6px; cursor:pointer; margin-top:0; }
  .del-btn:hover { color:#b3261e; border-color:#fca5a5; background:#fdecec; }
  .sessions-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
  .sessions-header h2 { margin:0; }
  .del-all-btn { background:transparent; border:1px solid var(--rule); color:#9ca3af; font-size:12px; padding:5px 12px; border-radius:6px; cursor:pointer; }
  .del-all-btn:hover { color:#b3261e; border-color:#fca5a5; background:#fdecec; }

  .min-n-row { display:flex; align-items:center; gap:10px; margin-top:14px; }
  .min-n-row label { margin:0; flex-shrink:0; font-size:13px; }
  .min-n-row input[type="number"] { width:90px; padding:6px 8px; }
  .min-n-row .hint { color:var(--muted); font-size:12px; font-weight:normal; }

  .bundled-btn { display:flex; flex-direction:column; align-items:flex-start; gap:4px;
    width:100%; text-align:left; padding:14px 18px; margin:0 0 4px; cursor:pointer;
    background:var(--accent); color:#fff; border:none; border-radius:8px;
    font-size:15px; font-weight:600; }
  .bundled-btn:hover { background:var(--accent2); }
  .bundled-btn .meta { font-size:12px; font-weight:normal; opacity:0.85; }
</style>
</head>
<body>
<div class="shell">
  <h1>AI Use Impact Tracker</h1>
  <p class="sub">Upload a GMP CSV extract to generate the interactive dashboard.</p>

  <div class="card">
    <h2>Load data</h2>
    {% if bundled %}
    <button type="button" class="bundled-btn" id="use-bundled-btn"
            data-path="{{ bundled.path }}">
      Use latest GMP extract
      <span class="meta">{{ bundled.size_mb }} MB · last updated {{ bundled.mtime }}</span>
    </button>
    <div class="or">— or upload your own —</div>
    {% endif %}
    <form id="upload-form" enctype="multipart/form-data">
      <label for="csv-file">Upload CSV file</label>
      <input type="file" id="csv-file" name="file" accept=".csv">

      <div class="or">— or —</div>

      <label for="csv-path">Server-side file path</label>
      <input type="text" id="csv-path" name="path" placeholder="/data/gmp_extract.csv">

      <div class="min-n-row">
        <label for="min-n">Minimum respondents per cell</label>
        <input type="number" id="min-n" name="min_n" value="50" min="1" max="10000">
        <span class="hint">default 50 · lower = noisier</span>
      </div>

      <button type="submit" id="run-btn">Run pipeline</button>
    </form>
    <div id="status"></div>
  </div>

  {% if sessions %}
  <div class="card" id="sessions-card">
    <div class="sessions-header">
      <h2>Previous dashboards</h2>
      <button type="button" class="del-all-btn" id="del-all-btn">Delete all</button>
    </div>
    <div class="sessions">
      {% for s in sessions %}
      <div class="row" data-job="{{ s.id }}">
        <a href="/dashboard/{{ s.id }}">{{ s.label }}</a>
        <button type="button" class="del-btn" onclick="deleteSession('{{ s.id }}')">Delete</button>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <footer>Global Mind Project — Sapien Labs</footer>
</div>
<script>
const form = document.getElementById("upload-form");
const status = document.getElementById("status");
const btn = document.getElementById("run-btn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  btn.disabled = true;
  status.className = "running";
  status.innerHTML = '<span class="spinner"></span>Uploading & running pipeline…';

  const fd = new FormData();
  const fileInput = document.getElementById("csv-file");
  const pathInput = document.getElementById("csv-path");
  const minNInput = document.getElementById("min-n");

  if (fileInput.files.length) {
    fd.append("file", fileInput.files[0]);
  } else if (pathInput.value.trim()) {
    fd.append("path", pathInput.value.trim());
  } else {
    status.className = "error";
    status.textContent = "Please select a file or enter a path.";
    btn.disabled = false;
    return;
  }

  fd.append("min_n", (minNInput.value || "50").trim());

  try {
    const res = await fetch("/ingest", { method: "POST", body: fd });
    const data = await res.json();
    if (data.error) {
      status.className = "error";
      status.textContent = "Error: " + data.error;
      btn.disabled = false;
      return;
    }
    // Start polling
    pollJob(data.job_id);
  } catch (err) {
    status.className = "error";
    status.textContent = "Upload failed: " + err.message;
    btn.disabled = false;
  }
});

const bundledBtn = document.getElementById("use-bundled-btn");
if (bundledBtn) {
  bundledBtn.addEventListener("click", async () => {
    btn.disabled = true;
    bundledBtn.disabled = true;
    status.className = "running";
    status.innerHTML = '<span class="spinner"></span>Loading bundled dataset…';

    const fd = new FormData();
    fd.append("path", bundledBtn.dataset.path);
    fd.append("min_n", (document.getElementById("min-n").value || "50").trim());

    try {
      const res = await fetch("/ingest", { method: "POST", body: fd });
      const data = await res.json();
      if (data.error) {
        status.className = "error";
        status.textContent = "Error: " + data.error;
        btn.disabled = false;
        bundledBtn.disabled = false;
        return;
      }
      pollJob(data.job_id);
    } catch (err) {
      status.className = "error";
      status.textContent = "Failed: " + err.message;
      btn.disabled = false;
      bundledBtn.disabled = false;
    }
  });
}

const delAllBtn = document.getElementById("del-all-btn");
if (delAllBtn) {
  delAllBtn.addEventListener("click", async () => {
    if (!confirm("Delete ALL previous dashboards? This cannot be undone.")) return;
    delAllBtn.disabled = true;
    try {
      const res = await fetch("/delete-all", { method: "POST" });
      if (res.ok) {
        const card = document.getElementById("sessions-card");
        if (card) card.remove();
      } else {
        const txt = await res.text();
        alert("Delete all failed: " + txt);
        delAllBtn.disabled = false;
      }
    } catch (err) {
      alert("Delete all failed: " + err.message);
      delAllBtn.disabled = false;
    }
  });
}

async function deleteSession(id) {
  if (!confirm("Delete this dashboard? This cannot be undone.")) return;
  try {
    const res = await fetch("/delete/" + encodeURIComponent(id), { method: "POST" });
    if (res.ok) {
      const row = document.querySelector('.row[data-job="' + id + '"]');
      if (row) row.remove();
    } else {
      const txt = await res.text();
      alert("Delete failed: " + txt);
    }
  } catch (err) {
    alert("Delete failed: " + err.message);
  }
}

async function pollJob(jobId) {
  const res = await fetch("/job/" + jobId);
  const data = await res.json();
  if (data.status === "running") {
    status.className = "running";
    status.innerHTML = '<span class="spinner"></span>' + (data.progress || "Processing…");
    setTimeout(() => pollJob(jobId), 1500);
  } else if (data.status === "done") {
    status.className = "done";
    status.innerHTML = '✓ Dashboard ready — <a href="/dashboard/' + jobId + '">Open dashboard</a>';
    btn.disabled = false;
  } else {
    status.className = "error";
    status.textContent = "Error: " + (data.error || "Unknown error");
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Landing page with upload form and list of previous sessions."""
    sessions = []
    for d in sorted(DATA_DIR.iterdir(), reverse=True):
        html = d / "dashboard" / "preview.html"
        if html.exists():
            # Use directory mtime for the label
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(html.stat().st_mtime))
            sessions.append({"id": d.name, "label": f"Dashboard — {ts}"})
    return render_template_string(UPLOAD_PAGE, sessions=sessions[:20], bundled=bundled_csv_meta())


@app.route("/ingest", methods=["POST"])
def ingest():
    """Accept a CSV upload or server-side path; kick off the ETL in a thread."""
    job_id = uuid.uuid4().hex[:12]
    job_dir = DATA_DIR / job_id
    job_dir.mkdir(parents=True)

    csv_path = None

    # Option 1: file upload
    f = request.files.get("file")
    if f and f.filename:
        csv_path = job_dir / "upload.csv"
        f.save(str(csv_path))

    # Option 2: server-side path
    if not csv_path:
        p = request.form.get("path", "").strip()
        if p and Path(p).is_file():
            csv_path = Path(p)
        elif p:
            return jsonify({"error": f"File not found on server: {p}"}), 400

    if not csv_path:
        return jsonify({"error": "No file provided"}), 400

    # Defensive parsing of min_n form field
    try:
        min_n = int(request.form.get("min_n", "50"))
        if min_n < 1 or min_n > 10000:
            min_n = 50
    except (ValueError, TypeError):
        min_n = 50

    JOBS[job_id] = {"status": "running", "progress": "Starting ETL…", "error": None}

    def _run():
        try:
            JOBS[job_id]["progress"] = f"Running ETL pipeline (min_n={min_n})…"
            output_root = str(job_dir / "tracker_output" / "v1" / "metrics")
            # Point the ETL at the right output location
            etl_out = str(job_dir / "tracker_output")
            run_etl({
                "source": "csv",
                "source_config": {"path": str(csv_path)},
                "output_root": etl_out,
                "min_n": min_n,
            })

            JOBS[job_id]["progress"] = "Baking dashboard…"
            _bake_dashboard(job_dir)

            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["progress"] = "Complete"
        except Exception as exc:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(exc)

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})


def _bake_dashboard(job_dir: Path):
    """Bake preview.html using the shared make_dashboard payload builder."""
    metrics_root = job_dir / "tracker_output" / "v1" / "metrics"
    meta = load_meta(metrics_root)
    payload = build_payload(metrics_root)

    out_dir = job_dir / "dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)

    html = bake_html(payload, meta)
    (out_dir / "preview.html").write_text(html, encoding="utf-8")


@app.route("/job/<job_id>")
def job_status(job_id):
    """Poll endpoint for job progress."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"status": "error", "error": "Unknown job"}), 404
    return jsonify(job)


@app.route("/dashboard/<job_id>")
def dashboard(job_id):
    """Serve the baked single-page dashboard for a given job."""
    html_path = DATA_DIR / job_id / "dashboard" / "preview.html"
    if not html_path.exists():
        return "Dashboard not found", 404
    return send_file(str(html_path), mimetype="text/html")


# Legacy routes redirect to the unified path.
@app.route("/dashboard-v1/<job_id>")
@app.route("/dashboard-v2/<job_id>")
def dashboard_legacy(job_id):
    return redirect(url_for("dashboard", job_id=job_id))


@app.route("/delete/<job_id>", methods=["POST"])
def delete_session(job_id):
    """Remove a baked dashboard session from disk + the in-memory registry."""
    # Defensive check: refuse anything that could escape DATA_DIR
    if not job_id or "/" in job_id or ".." in job_id or job_id.startswith("."):
        return "invalid id", 400
    target = DATA_DIR / job_id
    try:
        target = target.resolve()
        if DATA_DIR.resolve() not in target.parents:
            return "invalid id", 400
    except Exception:
        return "invalid id", 400
    if not target.exists() or not target.is_dir():
        return "not found", 404
    shutil.rmtree(target)
    JOBS.pop(job_id, None)
    return "ok"


@app.route("/docs/<path:filename>")
def docs(filename):
    """Serve documentation files (markdown, html, pdf) from /docs."""
    return send_from_directory(str(DOCS_DIR), filename)


@app.route("/delete-all", methods=["POST"])
def delete_all():
    """Remove every baked dashboard session from disk + the in-memory registry."""
    data_root = DATA_DIR.resolve()
    removed = 0
    failed: list[str] = []
    for d in list(DATA_DIR.iterdir()):
        if not d.is_dir():
            continue
        try:
            target = d.resolve()
            # Defensive: refuse anything that could escape DATA_DIR
            if data_root not in target.parents:
                continue
            shutil.rmtree(target)
            JOBS.pop(d.name, None)
            removed += 1
        except Exception as exc:
            failed.append(f"{d.name}: {exc}")
    if failed:
        return f"removed {removed}; failed: {'; '.join(failed)}", 500
    return f"removed {removed}"


@app.route("/latest")
def latest():
    """Serve the most recently baked dashboard from the local repo, if any."""
    local_html = HERE / "dashboard" / "preview.html"
    if local_html.exists():
        return send_file(str(local_html), mimetype="text/html")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"Starting AI Use Impact Tracker on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
