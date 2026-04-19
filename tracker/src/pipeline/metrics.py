"""
Metric-layer aggregation. Pure functions on DataFrames. No I/O.

Implements §5 of metric_spec.md: core indicators, impact indicators,
dose-response, and Wilson-score 95% CIs for share metrics.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .normalize import (
    ALL_IMPACT_FLAGS, POSITIVE_FLAGS, NEGATIVE_FLAGS, AI_FREQ_LABEL,
    IMPACT_WEIGHTS,
)

# §6
MIN_N = 50

# §2 — stratum levels we publish
STRATUM_LEVELS = [
    "global",
    "country",
    "gender",
    "age_band",
    "country_gender",
    "country_age_band",
    "gender_age_band",
    "country_gender_age_band",
]


# ---------------------------------------------------------------------------
# Wilson 95% score interval (§5.4)
# ---------------------------------------------------------------------------

def wilson_ci(k: np.ndarray, n: np.ndarray, z: float = 1.96):
    """Vectorised Wilson score interval."""
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n > 0, k / n, np.nan)
        denom = 1 + (z ** 2) / n
        center = (p + (z ** 2) / (2 * n)) / denom
        half = (z * np.sqrt((p * (1 - p) + (z ** 2) / (4 * n)) / n)) / denom
        lo = np.where(n > 0, np.clip(center - half, 0, 1), np.nan)
        hi = np.where(n > 0, np.clip(center + half, 0, 1), np.nan)
    return lo, hi


# ---------------------------------------------------------------------------
# Per-stratum aggregation
# ---------------------------------------------------------------------------

def _aggregate(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Compute all §5 metrics for one grouping set."""
    # Derived per-row composites
    df = df.copy()
    df["is_user"] = (df["ai_freq_int"] >= 1).astype("Int64")
    df["is_positive"] = df[POSITIVE_FLAGS].any(axis=1)
    df["is_negative"] = df[NEGATIVE_FLAGS].any(axis=1)
    # Impact denominator mask: uses AI AND has at least one real flag
    impact_flag_cols = [c for c in ALL_IMPACT_FLAGS if c != "impact_na"]
    df["has_impact_response"] = df[impact_flag_cols].any(axis=1)
    df["in_impact_denom"] = (df["is_user"] == 1) & df["has_impact_response"]

    grouped = df.groupby(group_cols, dropna=False)
    rows = []
    for keys, g in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = dict(zip(group_cols, keys))
        n = len(g)
        rec["n_respondents"] = n
        rec["suppressed"] = n < MIN_N

        if rec["suppressed"]:
            rows.append(rec)
            continue

        # Adoption
        n_users = int(g["is_user"].sum())
        rec["adoption_rate"] = n_users / n
        lo, hi = wilson_ci(np.array([n_users]), np.array([n]))
        rec["adoption_rate_ci_low"] = float(lo[0])
        rec["adoption_rate_ci_high"] = float(hi[0])

        # Freq mean + distribution
        freq = g["ai_freq_int"].dropna()
        if len(freq) > 0:
            rec["freq_mean"] = float(freq.mean())
            sem = float(freq.std(ddof=1) / math.sqrt(len(freq))) if len(freq) > 1 else 0.0
            rec["freq_mean_ci_low"] = rec["freq_mean"] - 1.96 * sem
            rec["freq_mean_ci_high"] = rec["freq_mean"] + 1.96 * sem
            for lvl in range(7):
                rec[f"freq_share_{lvl}"] = float((freq == lvl).mean())
        else:
            rec["freq_mean"] = None
            rec["freq_mean_ci_low"] = rec["freq_mean_ci_high"] = None
            for lvl in range(7):
                rec[f"freq_share_{lvl}"] = None

        # Impact indicators — denominator is in_impact_denom
        denom_df = g[g["in_impact_denom"]]
        n_denom = len(denom_df)
        rec["n_impact_denominator"] = n_denom

        def _share(flag_mask, label):
            k = int(flag_mask.sum())
            share = k / n_denom if n_denom > 0 else None
            lo, hi = wilson_ci(np.array([k]), np.array([n_denom]))
            rec[f"{label}"] = share
            rec[f"{label}_ci_low"] = float(lo[0]) if n_denom > 0 else None
            rec[f"{label}_ci_high"] = float(hi[0]) if n_denom > 0 else None

        if n_denom >= MIN_N:
            for flag in [c for c in ALL_IMPACT_FLAGS if c != "impact_na"]:
                _share(denom_df[flag], f"impact_share_{flag.replace('impact_', '')}")
            _share(denom_df["is_positive"], "positive_impact_share")
            _share(denom_df["is_negative"], "negative_impact_share")
            rec["net_impact_index"] = rec["positive_impact_share"] - rec["negative_impact_share"]

            # Tara's weighted AI Impact Index (v2)
            # Per-respondent score = sum of IMPACT_WEIGHTS[flag] for each True flag
            # Then average across the impact denominator.
            weight_cols = [c for c in ALL_IMPACT_FLAGS if c != "impact_na" and c in IMPACT_WEIGHTS]
            weights_arr = np.array([IMPACT_WEIGHTS[c] for c in weight_cols])
            per_resp = denom_df[weight_cols].values.astype(float) @ weights_arr
            rec["weighted_impact_index"] = float(np.mean(per_resp))
            if len(per_resp) > 1:
                sem = float(np.std(per_resp, ddof=1) / math.sqrt(len(per_resp)))
                rec["weighted_impact_index_ci_low"] = rec["weighted_impact_index"] - 1.96 * sem
                rec["weighted_impact_index_ci_high"] = rec["weighted_impact_index"] + 1.96 * sem
            else:
                rec["weighted_impact_index_ci_low"] = None
                rec["weighted_impact_index_ci_high"] = None
        else:
            rec["net_impact_index"] = None
            rec["weighted_impact_index"] = None
            rec["weighted_impact_index_ci_low"] = None
            rec["weighted_impact_index_ci_high"] = None

        # Dose-response: net_impact_index by ai_freq level
        dose = {}
        for lvl in range(7):
            lvl_df = denom_df[denom_df["ai_freq_int"] == lvl]
            if len(lvl_df) >= MIN_N:
                pos = lvl_df["is_positive"].mean()
                neg = lvl_df["is_negative"].mean()
                dose[str(lvl)] = float(pos - neg)
            else:
                dose[str(lvl)] = None
        rec["dose_response"] = dose

        rows.append(rec)

    return pd.DataFrame(rows)


def compute_metrics(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Return {stratum_level: metrics_dataframe} for all STRATUM_LEVELS.
    Each dataframe is partitioned by (year, month) downstream.
    """
    print(f"[metrics] computing across {len(STRATUM_LEVELS)} stratum levels on {len(df):,} rows")

    # Base time cols always present
    time_cols = ["year", "month"]

    level_to_cols = {
        "global":                  [],
        "country":                 ["country_clean"],
        "gender":                  ["gender_clean"],
        "age_band":                ["age_band"],
        "country_gender":          ["country_clean", "gender_clean"],
        "country_age_band":        ["country_clean", "age_band"],
        "gender_age_band":         ["gender_clean", "age_band"],
        "country_gender_age_band": ["country_clean", "gender_clean", "age_band"],
    }

    out: dict[str, pd.DataFrame] = {}
    for level, cols in level_to_cols.items():
        group = time_cols + cols
        agg = _aggregate(df, group)
        agg["stratum_level"] = level
        out[level] = agg
        print(f"[metrics]   {level}: {len(agg):,} cells "
              f"({int(agg['suppressed'].sum()):,} suppressed)")

    return out
