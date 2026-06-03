# AI Use Impact Tracker

An ETL pipeline and self-contained dashboard that turn a **Global Mind Project (GMP)**
survey extract into a versioned **Parquet metric layer** and a single-page,
world-map view of AI use and its self-reported impact on work.

A research initiative by [Sapien Labs](https://sapienlabs.org/) ·
data from the [Global Mind Project](https://sapienlabs.org/global-mind-project/).

---

## What it does

1. **Ingest** a GMP extract (CSV today; Elasticsearch planned) pulling only the columns the metrics need.
2. **Normalise** raw survey responses into canonical fields — AI-use frequency, impact flags, age bands, gender, country.
3. **Compute** metrics across eight demographic stratum levels, with Wilson-score 95% confidence intervals, a weighted AI Impact Index, and dose-response curves, suppressing thin cells below a configurable `min_n` threshold.
4. **Publish** the results as partitioned Parquet (one file per `stratum_level / year / month`).
5. **Bake** a self-contained `preview.html` dashboard that reads the Parquet **client-side via DuckDB-WASM** — no query backend required.

The pipeline is built around a single orchestration seam, `tracker/main.run(config)`,
which is callable identically from the CLI, a Docker container, or AWS Lambda.

---

## Quick start

```bash
pip install -r requirements.txt

# Run the ETL against a CSV extract
python tracker/main.py --source csv --path gmp_ai_only.csv --out ./tracker/output

# Bake the dashboard from the Parquet output
python tracker/make_dashboard.py

# Serve it locally (DuckDB-WASM needs a real HTTP origin, not file://)
./run_dashboard.sh        # opens http://localhost:8765/dashboard/preview.html
```

To run the web UI (upload a CSV, run the pipeline, view the dashboard):

```bash
python app.py             # local dev on http://localhost:5000
gunicorn app:app          # production
```

---

## Repository layout

```
.
├── app.py                  Flask web UI — upload/run/serve, wraps the ETL
├── tracker/
│   ├── main.py             Pipeline entry — run(config); CLI, Docker, Lambda
│   ├── lambda_handler.py   AWS Lambda wrapper around run()
│   ├── make_dashboard.py   Bakes the single-page DuckDB-WASM dashboard
│   └── src/
│       ├── sources/        Pluggable data adapters (the swap seam)
│       │   ├── csv_source.py            local or s3:// CSV (Phase 1)
│       │   └── elasticsearch_source.py  Elastic Cloud adapter (Phase 2 stub)
│       ├── pipeline/       Pure-function transforms, no I/O
│       │   ├── normalize.py             field canonicalisation
│       │   └── metrics.py               stratum metrics + Wilson CIs
│       └── publish/
│           └── parquet_writer.py        partitioned Parquet output
├── dashboard/              Baked static front end (preview.html)
├── docs/                   Metric spec, methodology, dashboard guide
├── Dockerfile              Container build (portable to ECS / Fargate / Batch)
└── requirements.txt
```

---

## Data sources

The pipeline reads from any `Source` that returns a DataFrame with the required
columns (`ai_freq`, `ai_impact_work`, `country`, `gender`, `biological_sex`,
`age`, `year`, `month`). Two adapters are defined:

- **CSV** (`--source csv`) — reads a local path or an `s3://` URL via fsspec. The active Phase 1 path.
- **Elasticsearch** (`--source elasticsearch`) — a documented stub for querying Sapien's Elastic Cloud directly. Swapping sources is a config change; downstream normalisation and metrics are unchanged.

---

## Output contract

```
{output_root}/v1/metrics/
  stratum_level={level}/year={YYYY}/month={MM}/part-0.parquet
  _meta.json        # records the min_n suppression threshold used
```

Parquet is Snappy-compressed and partitioned so a query for one month touches one
file. The metric layer is versioned (`v1/`) and immutable; any change to a metric
definition requires a version bump and a rebuild.

---

## Deployment

The same image runs in multiple places — packaging is a single Docker image,
the invocation target only changes the entrypoint:

| Target | Use | Entry |
|--------|-----|-------|
| **Railway** | current web app | `gunicorn app:app` (Dockerfile `ENTRYPOINT`) |
| **AWS Batch / ECS on Fargate** | full extract ETL / optional app | `python tracker/main.py …` |
| **AWS Lambda** | small (AI-only) extract | `lambda_handler.handler` |

The recommended AWS target — Elasticsearch → S3 raw zone → scheduled container
ETL → versioned Parquet in S3 → static DuckDB-WASM dashboard via CloudFront — is
described in the AWS porting recommendation under `docs/`.

---

## Documentation

See [`docs/`](./docs) for the full set:

- **TRACKER.md** — operator guide and the authoritative metric specification.
- **METRICS.md / How the Metrics Are Computed** — metric definitions and formulae.
- **DASHBOARD_BUILD.md** — building and publishing the dashboard.
- **Confidence_Intervals_Reference** — the Wilson-score CI methodology.

---

## License

Internal research project of Sapien Labs. Not licensed for external redistribution.
