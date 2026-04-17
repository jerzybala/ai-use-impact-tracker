"""
Parquet writer — emits the §7 output contract.

Path layout:
    {output_root}/v1/metrics/stratum_level={level}/year={YYYY}/month={MM}/part-0.parquet

output_root can be a local path or an s3:// URL (handled via pyarrow's fsspec
integration in Phase 2).
"""
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


VERSION = "v1"


def write(metrics: dict[str, pd.DataFrame], output_root: str) -> list[str]:
    """
    Write one Parquet file per (stratum_level, year, month) partition.
    Returns the list of paths written.
    """
    root = Path(output_root) / VERSION / "metrics"
    root.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for level, df in metrics.items():
        if df.empty:
            continue
        # Serialise dict-valued columns (dose_response) to JSON strings for portability
        if "dose_response" in df.columns:
            df = df.copy()
            df["dose_response"] = df["dose_response"].map(
                lambda d: json.dumps(d) if isinstance(d, dict) else None
            )

        for (year, month), part in df.groupby(["year", "month"], dropna=False):
            if pd.isna(year) or pd.isna(month):
                continue
            path = (root
                    / f"stratum_level={level}"
                    / f"year={int(year)}"
                    / f"month={int(month):02d}")
            path.mkdir(parents=True, exist_ok=True)
            fname = path / "part-0.parquet"
            table = pa.Table.from_pandas(part, preserve_index=False)
            pq.write_table(table, fname, compression="snappy")
            written.append(str(fname))

    print(f"[publish] wrote {len(written)} Parquet files under {root}")
    return written
