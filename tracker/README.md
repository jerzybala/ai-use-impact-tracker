# AI Use Impact Tracker — ETL

Phase 1 pipeline that converts a GMP data extract into a versioned Parquet
metric layer ready to be consumed by a static dashboard (Observable
Framework or Evidence.dev) via DuckDB-WASM.

## Layout

```
tracker/
├── metric_spec.md          Authoritative definitions (§1–§8)
├── main.py                 Entry point — CLI, Docker, and Lambda all call run()
├── lambda_handler.py       AWS Lambda wrapper
├── Dockerfile              Railway / ECS / Fargate container
├── requirements.txt
└── src/
    ├── sources/            Data source adapters (the swap seam)
    │   ├── base.py                 Abstract Source + REQUIRED_COLUMNS
    │   ├── csv_source.py           Phase 1 (local / S3 CSV)
    │   └── elasticsearch_source.py Phase 2 stub (Sapien Labs ES)
    ├── pipeline/           Pure-function DataFrame transforms (no I/O)
    │   ├── normalize.py            Implements metric_spec §4
    │   └── metrics.py              Implements metric_spec §5–§6
    └── publish/
        └── parquet_writer.py       Implements metric_spec §7 output contract
```

## Design principle

Only `src/sources/` knows where data comes from. Everything downstream
operates on a DataFrame. To migrate CSV → Elasticsearch, swap one config
line; the normaliser, metric layer, and publisher are unchanged.

## Local run

```bash
pip install -r requirements.txt

python main.py \
  --source csv \
  --path "../SAMPLE DATA .xlsx" \
  --out ./output
```

Outputs land at `output/v1/metrics/stratum_level=.../year=YYYY/month=MM/part-0.parquet`.

## Container run (Railway / ECS)

```bash
docker build -t ai-use-tracker .
docker run --rm -v $(pwd)/data:/data ai-use-tracker
```

Mount the input CSV and output directory into `/data`.

## Lambda run

Package `main.py` + `lambda_handler.py` + `src/` as a Lambda layer or
container image. Invoke with payload matching the `run()` config dict:

```json
{
  "source": "csv",
  "source_config": {"path": "s3://sapien-gmp/exports/latest.csv"},
  "output_root": "s3://sapien-gmp/tracker/"
}
```

## Downstream consumer

The Parquet output is read by the dashboard (Observable Framework
recommended) via DuckDB-WASM. The dashboard is a separate project; this
ETL's only contract with it is the Parquet layout in `metric_spec.md §7`.
