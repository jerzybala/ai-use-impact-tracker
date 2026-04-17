"""
CSV source adapter — Phase 1 implementation.

Reads a local CSV file (or one path-addressable via an fsspec URL,
e.g. s3://...) and returns a DataFrame with the required GMP columns.

Optimised to pull only the columns we need so a 1–2 GB extract doesn't
blow out memory during ingest.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from .base import Source, SourceConfig, REQUIRED_COLUMNS


@dataclass
class CSVSourceConfig(SourceConfig):
    path: str = ""
    # Columns beyond REQUIRED_COLUMNS to also fetch (e.g. employment, education)
    extra_columns: tuple[str, ...] = ()


class CSVSource(Source):
    def __init__(self, config: CSVSourceConfig):
        if not config.path:
            raise ValueError("CSVSourceConfig.path is required")
        super().__init__(config)
        self.config: CSVSourceConfig = config

    def fetch(self) -> pd.DataFrame:
        cols = list(REQUIRED_COLUMNS) + list(self.config.extra_columns)
        path = self.config.path
        print(f"[csv_source] reading {path} (columns={len(cols)})")

        df = pd.read_csv(
            path,
            usecols=cols,
            dtype=str,              # ingest everything as string; cast later
            low_memory=False,
            na_filter=False,        # keep 'N/A' literal so we can canonicalise
        )

        # Coerce year/month to int after ingest
        for c in ("year", "month"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

        # Apply optional year_month filter
        if self.config.year_month_from or self.config.year_month_to:
            ym = df["year"] * 100 + df["month"].fillna(0).astype(int)
            if self.config.year_month_from:
                y, m = self.config.year_month_from
                ym_from = y * 100 + m
                df = df[ym >= ym_from]
            if self.config.year_month_to:
                y, m = self.config.year_month_to
                ym_to = y * 100 + m
                df = df[ym <= ym_to]

        print(f"[csv_source] loaded {len(df):,} rows")
        return self.validate(df)
