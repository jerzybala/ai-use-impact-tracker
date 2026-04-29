# AI Use Impact Tracker — ETL + dashboard baker

Pipeline that converts a GMP data extract into a versioned Parquet
metric layer, plus a single-page HTML dashboard baker for a
self-contained world-map view.

## Layout

```
tracker/
├── metric_spec.md          Authoritative definitions (§1–§9)
├── main.py                 ETL entry — CLI, Docker, and Lambda all call run()
├── lambda_handler.py       AWS Lambda wrapper
├── make_dashboard.py       Bakes ../dashboard/preview.html (single-page, world-map)
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

`make_preview.py` and `make_preview_v2.py` are the previous v1/v2 bakers; superseded by `make_dashboard.py`.

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

## Bake the dashboard

After the ETL has written Parquet output, generate the single-page
HTML dashboard:

```bash
python make_dashboard.py
```

This loads the `global`, `country`, `country_gender`, `country_age_band`,
and `country_gender_age_band` strata, embeds them as inline JSON, and
writes `../dashboard/preview.html`. The file is fully self-contained
(Observable Plot, d3, topojson, and world-atlas are loaded from CDN at
view time) — open it by double-click, or serve it via the Flask app
at the project root (`app.py`).

## Dashboard features

- **Top KPIs**: Weighted Impact Index, respondents, AI adoption rate,
  impact denominator — all reflecting the active filters.
- **World choropleth** colored by one of 10 metrics (see `metric_spec.md`
  §5 for definitions).
- **Filters**: month + period (Single / Last 3 / Last 6), color-by
  metric, gender, age band, frequency. Filter combinations select the
  appropriate precomputed stratum, so every value shown is exact.
- **Country click** opens a detail card with all impact shares and the
  dose-response curve.

## Downstream consumer (alternative)

The Parquet output can also be read directly by external dashboards
(Observable Framework, Evidence.dev) via DuckDB-WASM. The Parquet
layout in `metric_spec.md §7` is the stable contract.
