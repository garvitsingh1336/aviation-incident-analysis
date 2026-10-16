"""Central configuration for the aviation analysis backend."""
from __future__ import annotations

import os
from pathlib import Path

# Project layout ------------------------------------------------------------ #
BACKEND_DIR = Path(__file__).resolve().parent          # .../backend/app
APP_DIR = BACKEND_DIR
DATA_DIR = APP_DIR / "data"
PROJECT_ROOT = APP_DIR.parent.parent                   # aviation-incident-analysis/
STORE_DIR = Path(os.environ.get("AV_STORE_DIR", PROJECT_ROOT / "data_store"))
STORE_DIR.mkdir(parents=True, exist_ok=True)

# Artifact paths ------------------------------------------------------------ #
ANALYSIS_JSON = STORE_DIR / "analysis.json"
EMBEDDINGS_NPY = STORE_DIR / "embeddings.npy"
EMBEDDER_PKL = STORE_DIR / "embedder.pkl"          # only for the fallback encoder
META_JSON = STORE_DIR / "meta.json"

# Dataset ------------------------------------------------------------------- #
# If a real dataset (e.g. an NTSB / ASRS export) is present at REAL_DATASET_CSV
# it will be used; otherwise the synthetic corpus is generated / loaded.
DEFAULT_DATASET_CSV = DATA_DIR / "reports.csv"
REAL_DATASET_CSV = Path(os.environ.get("AV_DATASET_CSV", DEFAULT_DATASET_CSV))
SYNTHETIC_N = int(os.environ.get("AV_SYNTHETIC_N", "480"))

# Model configuration ------------------------------------------------------- #
EMBEDDING_MODEL = os.environ.get("AV_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SPACY_MODEL = os.environ.get("AV_SPACY_MODEL", "en_core_web_sm")

# Allow forcing the lightweight engine (useful for CI / low-resource machines).
FORCE_LIGHTWEIGHT = os.environ.get("AV_FORCE_LIGHTWEIGHT", "0") == "1"

# Analysis hyper-parameters ------------------------------------------------- #
N_CLUSTERS = int(os.environ.get("AV_N_CLUSTERS", "14"))
MIN_TOPIC_SIZE = int(os.environ.get("AV_MIN_TOPIC_SIZE", "10"))
CORS_ORIGINS = os.environ.get(
    "AV_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
).split(",")
