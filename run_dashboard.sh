#!/usr/bin/env bash
#
# AI Use Impact Tracker — local dashboard launcher.
#
# Starts a local HTTP server in this folder and opens the zero-install
# preview in your default browser. DuckDB-WASM requires a real HTTP
# origin (it won't work via file://), which is why we need a server.
#
# Usage:
#   ./run_dashboard.sh          # default: port 8765
#   ./run_dashboard.sh 9000     # custom port
#
set -e

PORT="${1:-8765}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- sanity: Parquet output present? -----------------------------------------
if [ ! -d "$DIR/tracker/output/v1/metrics/stratum_level=global" ]; then
  echo ""
  echo "No ETL output found at $DIR/tracker/output/"
  echo "Run the pipeline first:"
  echo ""
  echo "    cd \"$DIR/tracker\""
  echo "    pip install -r requirements.txt"
  echo "    python3 main.py --source csv --path <your-gmp.csv> --out ./output"
  echo ""
  exit 1
fi

# --- pick python --------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "python not found — please install Python 3."
  exit 1
fi

URL="http://localhost:${PORT}/dashboard/preview.html"

echo ""
echo "AI Use Impact Tracker — local preview"
echo "  serving:  $DIR"
echo "  open:     $URL"
echo ""
echo "(press Ctrl-C to stop)"
echo ""

# --- open browser once the server is listening --------------------------------
(
  # wait up to 5s for the port to be accepting connections
  for i in 1 2 3 4 5; do
    if (echo >/dev/tcp/127.0.0.1/${PORT}) >/dev/null 2>&1; then break; fi
    sleep 1
  done
  if command -v open >/dev/null 2>&1; then        # macOS
    open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then  # Linux
    xdg-open "$URL"
  fi
) &

cd "$DIR"
exec "$PY" -m http.server "$PORT"
