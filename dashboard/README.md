# AI Use Impact Tracker — Dashboard

Static, public-facing front end for the AI Use Impact Tracker. Reads the
Parquet metric layer produced by `../tracker/` via DuckDB-WASM (client-side)
— no dashboard server required, scales to any number of readers from CDN.

## Two modes

### 1. Framework build (production target)

The canonical project — pages in `src/*.md`, data loaders in `src/data/*.py`,
configured in `observablehq.config.js`. Builds to a fully static site ready
to deploy to Railway, CloudFront, Netlify, or any static host.

```bash
npm install              # installs @observablehq/framework
npm run dev              # local preview with hot reload, http://localhost:3000
npm run build            # static build in ./dist/
```

The build requires network access to npm's CDN for dependency resolution at
build time (how Framework handles transitive imports).

### 2. Preview (zero-install)

`preview.html` is a self-contained single-file version that works without
any build step. Open it in a browser via a local server (it uses
DuckDB-WASM which requires a real HTTP origin, not `file://`):

```bash
# From the repository root:
python3 -m http.server 8000
# Then open http://localhost:8000/dashboard/preview.html
```

The preview reads Parquet directly from `../tracker/output/` using
DuckDB-WASM. It is suitable for internal review; the Framework build is
the path for stakeholder publication.

## Layout

```
dashboard/
├── observablehq.config.js    Site config: pages, theme, footer
├── package.json              Framework + d3 + plot deps
├── preview.html              Zero-install single-page preview
└── src/
    ├── index.md              Overview: KPIs + global time series
    ├── by-country.md         Country rankings + scatter + table
    ├── by-frequency.md       Dose-response + freq distribution over time
    ├── about.md              Methodology page
    └── data/
        ├── global.parquet.py      Consolidates stratum_level=global
        ├── country.parquet.py     Consolidates stratum_level=country
        ├── gender.parquet.py      Consolidates stratum_level=gender
        └── age_band.parquet.py    Consolidates stratum_level=age_band
```

## Deployment

Target: static files on CloudFront (AWS) or Railway's static site hosting.
The full pipeline runs:

```
GMP data → tracker/ ETL → Parquet on S3 → dashboard/ build → CDN
```

The ETL (`tracker/`) and dashboard (`dashboard/`) are intentionally
decoupled. They communicate only via the Parquet layout defined in
`tracker/metric_spec.md §7`.
