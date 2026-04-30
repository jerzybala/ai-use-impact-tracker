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
- **World choropleth** colored by one of 10 metrics (definitions below).
- **Filters**: month + period (Single / Last 3 / Last 6), color-by
  metric, gender, age band, frequency. Filter combinations select the
  appropriate precomputed stratum, so every value shown is exact.
- **Country click** opens a detail card with all impact shares and the
  dose-response curve.

## Metrics

All metrics are computed per (stratum × month). When the **Period** is set to Last 3 / Last 6, values are pooled across the window using respondent-count weights (see `metric_spec.md §9`). See `metric_spec.md §5` for the formal definitions.

| Metric | Definition | Denominator | Range (clipped for map) |
|---|---|---|---|
| **Weighted Impact Index** | Per-respondent score = sum of signed weights for each impact flag selected; map shows the average. Weights: `+1.0` new opportunities, `+0.5` improved quality, `−0.25` job anxiety, `−0.5` adaptation pressure, `−0.75` reduced income, `−1.0` job loss. | AI users with ≥1 impact response | ≈ [−1, +1], shown [−0.3, +0.3] |
| **Net Impact Index** | `positive_impact_share − negative_impact_share`. Positive = improved quality OR new opportunities. Negative = adaptation pressure OR job anxiety OR job loss OR reduced income. | (same) | [−1, +1], shown [−0.5, +0.5] |
| **AI Adoption Rate** | Share whose `ai_freq` is anything other than "Never". | All respondents in stratum | [0, 1], shown [0, 100%] |
| **Frequency Mean (0–6)** | Mean of the `ai_freq` integer scale: 0 Never, 1 Rarely, 2 Monthly, 3 Weekly, 4 Daily, 5 Constantly, 6 Always. | Respondents with non-null `ai_freq` | [0, 6], shown [1, 5] |
| **Improved Quality (share)** | Share who selected "Improved my work quality or output". | AI users with ≥1 impact response | [0, 1], shown [0, 60%] |
| **New Opportunities (share)** | Share who selected "Created new job or income opportunities". | (same) | [0, 1], shown [0, 40%] |
| **Adaptation Pressure (share)** | Share who selected "Increased pressure to adapt or work faster". | (same) | [0, 1], shown [0, 60%] |
| **Job Anxiety (share)** | Share who selected "Made me worry about the future of my job or industry". | (same) | [0, 1], shown [0, 60%] |
| **Job Loss (share)** | Share who selected "Caused me to lose my job". | (same) | [0, 1], shown [0, 15%] |
| **Reduced Income (share)** | Share who selected "Reduced my income or made it harder to find work". | (same) | [0, 1], shown [0, 20%] |

**Notes**
- Impact shares can sum to more than 100% — respondents may select multiple flags simultaneously.
- Cells with fewer than 50 respondents are suppressed (`MIN_N = 50`) and not drawn on the map.
- "Range (clipped for map)" is the visualization domain; outliers saturate at the endpoint color so the rest of the map stays readable.

## Downstream consumer (alternative)

The Parquet output can also be read directly by external dashboards
(Observable Framework, Evidence.dev) via DuckDB-WASM. The Parquet
layout in `metric_spec.md §7` is the stable contract.
