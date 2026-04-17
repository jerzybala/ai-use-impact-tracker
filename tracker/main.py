"""
AI Use Impact Tracker — pipeline entry point.

This function is the single orchestration seam. It is callable:
  - from the CLI:        `python main.py --source csv --path data.csv --out ./output`
  - from Docker:         set as CMD in Dockerfile
  - from AWS Lambda:     wrapped by lambda_handler.py
  - from a test:         `run(config_dict)` directly

Deliberately keeps I/O narrow so deployment targets are interchangeable.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow running as `python main.py` without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from src.sources import CSVSource, CSVSourceConfig, ElasticsearchSource, ElasticsearchSourceConfig
from src.pipeline import normalize, compute_metrics
from src.publish import write as write_parquet


def run(config: dict) -> dict:
    """
    Execute the full ETL → metric → publish pipeline.

    config keys:
      source: "csv" | "elasticsearch"
      source_config: dict forwarded to the chosen source
      output_root:   str (local path or s3://...)

    Returns a summary dict suitable for logs / Lambda response.
    """
    t0 = time.time()
    print(f"[run] starting with source={config['source']}")

    # 1. Source
    if config["source"] == "csv":
        source = CSVSource(CSVSourceConfig(**config.get("source_config", {})))
    elif config["source"] == "elasticsearch":
        source = ElasticsearchSource(ElasticsearchSourceConfig(**config.get("source_config", {})))
    else:
        raise ValueError(f"Unknown source: {config['source']}")

    raw = source.fetch()

    # 2. Normalise
    clean = normalize(raw)

    # 3. Metrics
    metrics = compute_metrics(clean)

    # 4. Publish
    paths = write_parquet(metrics, config["output_root"])

    elapsed = time.time() - t0
    summary = {
        "source": config["source"],
        "rows_ingested": int(len(raw)),
        "stratum_levels": list(metrics.keys()),
        "files_written": len(paths),
        "output_root": config["output_root"],
        "elapsed_seconds": round(elapsed, 1),
    }
    print(f"[run] done in {elapsed:.1f}s — summary: {json.dumps(summary, indent=2)}")
    return summary


def _cli():
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=["csv", "elasticsearch"], default="csv")
    p.add_argument("--path", help="CSV path (when --source=csv)")
    p.add_argument("--out", required=True, help="Output root (local path or s3://)")
    p.add_argument("--year-month-from", nargs=2, type=int, metavar=("YEAR", "MONTH"))
    p.add_argument("--year-month-to", nargs=2, type=int, metavar=("YEAR", "MONTH"))
    args = p.parse_args()

    source_config = {}
    if args.source == "csv":
        source_config["path"] = args.path
    if args.year_month_from:
        source_config["year_month_from"] = tuple(args.year_month_from)
    if args.year_month_to:
        source_config["year_month_to"] = tuple(args.year_month_to)

    run({
        "source": args.source,
        "source_config": source_config,
        "output_root": args.out,
    })


if __name__ == "__main__":
    _cli()
