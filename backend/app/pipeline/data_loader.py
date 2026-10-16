"""Stage 1-2: Data collection and preparation.

Loads the aviation report corpus from a real dataset if one is configured,
otherwise generates / loads the synthetic corpus.  The loader also performs the
"data preparation" step from the synopsis: dropping empty narratives, removing
duplicates, coercing dates and normalising the column names so that downstream
stages can rely on a stable schema.
"""
from __future__ import annotations

import re
from typing import List

import pandas as pd

from .. import config
from ..data.generate_dataset import generate_reports

# Canonical schema the rest of the pipeline expects.
REQUIRED = ["report_id", "date", "narrative"]
OPTIONAL = [
    "event_text", "aircraft_type", "airport", "location", "operator",
    "phase_of_flight", "severity", "injury_level", "true_factors",
]

# Common column aliases so real datasets (e.g. NTSB) load with minimal effort.
ALIASES = {
    "narrative": ["narrative", "text", "summary", "report", "description",
                  "remarks", "synopsis", "probable_cause", "final_narrative"],
    "date": ["date", "event_date", "ev_date", "occurrence_date", "report_date"],
    "report_id": ["report_id", "id", "ntsb_no", "ev_id", "acn", "case_number"],
    "aircraft_type": ["aircraft_type", "aircraft", "make_model", "model", "acft_model"],
    "airport": ["airport", "apt_code", "icao", "airport_code"],
    "location": ["location", "city", "place", "site"],
    "severity": ["severity", "ev_highest_injury", "damage", "event_severity"],
}


def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower_map = {c.lower().strip(): c for c in df.columns}
    rename = {}
    for canonical, options in ALIASES.items():
        for opt in options:
            if opt in lower_map and canonical not in df.columns:
                rename[lower_map[opt]] = canonical
                break
    if rename:
        df = df.rename(columns=rename)
    return df


def load_reports() -> pd.DataFrame:
    """Return the cleaned report corpus as a DataFrame."""
    path = config.REAL_DATASET_CSV
    if path.exists():
        df = pd.read_csv(path)
        df = _standardise_columns(df)
    else:
        # Generate a fresh synthetic corpus and persist it for reproducibility.
        df = generate_reports(n=config.SYNTHETIC_N)
        config.DEFAULT_DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(config.DEFAULT_DATASET_CSV, index=False)

    df = _prepare(df)
    return df


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    # Drop rows without usable text and de-duplicate.
    df = df.copy()
    df["narrative"] = df["narrative"].astype(str).str.strip()
    df = df[df["narrative"].str.len() > 20]
    df = df.drop_duplicates(subset=["narrative"])

    # Coerce date; keep a parsed column for trend analysis.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year

    # Ensure optional columns exist so the schema is stable.
    for col in OPTIONAL:
        if col not in df.columns:
            df[col] = None

    df = df.reset_index(drop=True)
    df["idx"] = df.index  # positional index used to align embeddings/labels
    df["analysis_text"] = _build_analysis_text(df)
    return df


# Manufacturer / airport-code cues to strip from analysis text when a dataset
# does not provide a pre-separated event narrative.
_MAKERS_RE = re.compile(
    r"\b(Boeing|Airbus|Cessna|Piper|Beechcraft|Bombardier|Embraer|Gulfstream|"
    r"Diamond|Cirrus|Robinson|ATR)\b[\w\-]*", re.IGNORECASE,
)
_ICAO_RE = re.compile(r"\b[KP][A-Z]{3}\b")


def _build_analysis_text(df: pd.DataFrame) -> pd.Series:
    """Text used for embeddings/topics/clustering — focused on *what happened*.

    Prefers a pre-separated ``event_text`` column; otherwise strips structured
    context (aircraft, airport, location, operator, ICAO codes) out of the
    narrative so topics reflect contributing factors rather than aircraft type.
    """
    if "event_text" in df.columns and df["event_text"].notna().any():
        return df["event_text"].fillna(df["narrative"]).astype(str)

    def strip_context(row) -> str:
        text = str(row["narrative"])
        for col in ("aircraft_type", "airport", "location", "operator"):
            val = row.get(col)
            if isinstance(val, str) and len(val) > 1:
                text = re.sub(re.escape(val), " ", text, flags=re.IGNORECASE)
        text = _MAKERS_RE.sub(" ", text)
        text = _ICAO_RE.sub(" ", text)
        text = re.sub(r"\(\s*\)", " ", text)          # empty parens left behind
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text or str(row["narrative"])

    return df.apply(strip_context, axis=1)


def corpus_texts(df: pd.DataFrame) -> List[str]:
    """Factor-focused text for the ML pipeline (embeddings, topics, clustering)."""
    return df["analysis_text"].astype(str).tolist()


def narratives(df: pd.DataFrame) -> List[str]:
    """Full human-readable narratives (used for NER and display)."""
    return df["narrative"].astype(str).tolist()
