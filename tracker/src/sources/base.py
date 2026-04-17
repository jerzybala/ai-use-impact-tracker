"""
Data source abstraction for the AI Use Impact Tracker.

A Source yields a pandas DataFrame containing the required GMP columns.
Everything downstream (normalisation, metric computation, Parquet writes)
operates on the returned DataFrame and has no knowledge of the source.

This is the seam that lets Phase 1 (CSV) swap to Phase 2 (Elasticsearch)
without touching the rest of the pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd


# Canonical minimum column set the pipeline requires.
# Any Source implementation must guarantee these are present.
REQUIRED_COLUMNS = [
    "ai_freq",
    "ai_impact_work",
    "country",
    "gender",
    "biological_sex",
    "age",
    "year",
    "month",
]


@dataclass
class SourceConfig:
    """Configuration common to every source. Subclasses may extend."""
    # Optional month filter (inclusive). If None, fetch all months available.
    year_month_from: tuple[int, int] | None = None
    year_month_to: tuple[int, int] | None = None


class Source(ABC):
    """Abstract base: implement fetch() to return a DataFrame."""

    def __init__(self, config: SourceConfig):
        self.config = config

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Return a DataFrame containing at minimum REQUIRED_COLUMNS."""
        ...

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Check required columns are present; raise if not."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Source returned DataFrame missing required columns: {missing}"
            )
        return df
