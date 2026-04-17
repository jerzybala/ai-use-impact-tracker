"""
Normalisation layer. Pure functions on DataFrames. No I/O.

Implements the rules defined in metric_spec.md §4.
"""
from __future__ import annotations

import pandas as pd
import numpy as np


# --- §4.1  ai_freq → integer scale -----------------------------------------

AI_FREQ_MAP = {
    "I have never used an AI assistant": 0,
    "Rarely": 1,
    "A few times a month": 2,
    "Several days a week": 3,
    "Several times a day": 4,
    "Constantly": 5,
    "Constamment": 5,                   # French
    "Constantly (when awake)": 5,       # spec variant
    "All of the time": 6,
}

AI_FREQ_LABEL = {
    0: "Never", 1: "Rarely", 2: "Monthly", 3: "Weekly",
    4: "Daily", 5: "Constantly", 6: "Always",
}


def normalize_ai_freq(s: pd.Series) -> pd.Series:
    return s.map(AI_FREQ_MAP).astype("Int64")


# --- §4.2  ai_impact_work → binary flags -----------------------------------

# atomic_option -> flag name
IMPACT_OPTIONS = {
    "No impact": "impact_none",
    "Improved my work quality or output": "impact_improved_quality",
    "Created new job or income opportunities": "impact_new_opportunities",
    "Increased pressure to adapt or work faster": "impact_adaptation_pressure",
    "Made me worry about the future of my job or industry": "impact_job_anxiety",
    "Another impact not listed here": "impact_other",
    "Not sure": "impact_not_sure",
    # translation variants observed in data
    "No estoy seguro/a": "impact_not_sure",
    "Not No estoy seguro/a": "impact_not_sure",
}

ALL_IMPACT_FLAGS = sorted(set(IMPACT_OPTIONS.values())) + ["impact_na"]

POSITIVE_FLAGS = ["impact_improved_quality", "impact_new_opportunities"]
NEGATIVE_FLAGS = ["impact_adaptation_pressure", "impact_job_anxiety"]


def parse_impact_work(s: pd.Series) -> pd.DataFrame:
    """
    Split pipe-delimited ai_impact_work into one-hot flag columns.
    Returns a DataFrame aligned to s.index with ALL_IMPACT_FLAGS columns.
    """
    # Initialise all flags to False
    out = pd.DataFrame(False, index=s.index, columns=ALL_IMPACT_FLAGS)

    na_mask = s.isna() | s.str.strip().isin(["", "N/A", "NA", "nan", "None"])
    out.loc[na_mask, "impact_na"] = True

    non_na = s[~na_mask]
    # Split on pipe, strip, drop empties
    split = non_na.str.split("|")
    for idx, tokens in split.items():
        for tok in tokens:
            tok = tok.strip()
            if not tok:
                continue
            flag = IMPACT_OPTIONS.get(tok)
            if flag is not None:
                out.at[idx, flag] = True
            else:
                # unknown option -> treat as "other"
                out.at[idx, "impact_other"] = True

    return out


# --- §4.3  age → age band --------------------------------------------------

VALID_AGE_BANDS = {"18-20", "21-24", "25-34", "35-44",
                   "45-54", "55-64", "65-74", "75-84", "85+"}


def normalize_age_band(s: pd.Series) -> pd.Series:
    def _map(v):
        if pd.isna(v):
            return None
        v = str(v).strip()
        if v in VALID_AGE_BANDS:
            return v
        # raw integers 18–20
        try:
            n = int(float(v))
            if 18 <= n <= 20:
                return "18-20"
        except (ValueError, TypeError):
            pass
        return None
    return s.map(_map)


# --- §4.4  gender ----------------------------------------------------------

VALID_GENDERS = {"Female", "Male", "Non-binary",
                 "Other/Intersex", "Prefer not to say"}


def normalize_gender(df: pd.DataFrame) -> pd.Series:
    g = df["gender"].where(df["gender"].isin(VALID_GENDERS))
    b = df["biological_sex"].where(df["biological_sex"].isin(VALID_GENDERS))
    return g.fillna(b)


# --- §4.5  country ---------------------------------------------------------

# Minimal starter dictionary — expand as non-Latin-script variants surface.
COUNTRY_ALIASES = {
    "भारत (इंडिया)": "India",       # Devanagari
    "‡§≠‡§æ‡§∞‡§§ (‡§á‡§Ç‡§°‡§ø‡§Ø‡§æ)": "India",  # MacRoman-mangled Devanagari (observed in CSV export)
    "Korea| South": "South Korea",     # pipe leak from another column
    # add more as discovered
}


def normalize_country(s: pd.Series) -> pd.Series:
    return s.map(lambda v: COUNTRY_ALIASES.get(v, v) if isinstance(v, str) else v)


# --- Orchestrator ----------------------------------------------------------

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all §4 rules. Returns a new DataFrame with:
      - ai_freq_int (0–6, nullable)
      - ai_freq_label (string)
      - all ALL_IMPACT_FLAGS columns (bool)
      - age_band (string, nullable)
      - gender_clean (string, nullable)
      - country_clean (string)
      - year, month (int)
    """
    print(f"[normalize] input rows: {len(df):,}")

    out = pd.DataFrame(index=df.index)
    out["year"] = df["year"].astype("Int64")
    out["month"] = df["month"].astype("Int64")

    out["ai_freq_int"] = normalize_ai_freq(df["ai_freq"])
    out["ai_freq_label"] = out["ai_freq_int"].map(AI_FREQ_LABEL)

    flags = parse_impact_work(df["ai_impact_work"])
    out = pd.concat([out, flags], axis=1)

    out["age_band"] = normalize_age_band(df["age"])
    out["gender_clean"] = normalize_gender(df)
    out["country_clean"] = normalize_country(df["country"])

    print(f"[normalize] distinct ai_freq_int: {out['ai_freq_int'].dropna().unique().tolist()}")
    print(f"[normalize] impact_na share: {out['impact_na'].mean():.1%}")
    print(f"[normalize] non-null age_band: {out['age_band'].notna().mean():.1%}")
    print(f"[normalize] non-null gender:   {out['gender_clean'].notna().mean():.1%}")

    return out
