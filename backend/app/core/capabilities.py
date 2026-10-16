"""Runtime capability detection.

The synopsis specifies a "full" AI/ML stack (sentence-transformers, BERTopic,
spaCy).  To guarantee the pipeline always runs — even offline or on a machine
where those heavy libraries could not be installed — every stage has a
scikit-learn fallback.  This module reports which engines are actually available
so the rest of the code (and the UI) can adapt and be honest about what ran.
"""
from __future__ import annotations

import importlib.util
from functools import lru_cache
from typing import Dict

from .. import config


def _has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


@lru_cache(maxsize=1)
def capabilities() -> Dict[str, bool]:
    """Return a dict describing which optional engines are usable."""
    if config.FORCE_LIGHTWEIGHT:
        return {
            "sentence_transformers": False,
            "bertopic": False,
            "spacy": False,
            "spacy_model": False,
            "torch": False,
            "forced_lightweight": True,
        }

    caps = {
        "sentence_transformers": _has("sentence_transformers"),
        "bertopic": _has("bertopic") and _has("umap") and _has("hdbscan"),
        "spacy": _has("spacy"),
        "torch": _has("torch"),
        "forced_lightweight": False,
    }
    # A spaCy install is only useful with a downloaded pipeline.
    caps["spacy_model"] = False
    if caps["spacy"]:
        try:
            import spacy  # noqa: WPS433

            caps["spacy_model"] = spacy.util.is_package(config.SPACY_MODEL)
        except Exception:  # pragma: no cover - defensive
            caps["spacy_model"] = False
    return caps


def engine_summary() -> Dict[str, str]:
    """Human-readable description of the engine chosen for each stage."""
    c = capabilities()
    return {
        "embeddings": (
            f"sentence-transformers ({config.EMBEDDING_MODEL})"
            if c["sentence_transformers"] else "scikit-learn TF-IDF + TruncatedSVD"
        ),
        "topic_modeling": (
            "BERTopic (UMAP + HDBSCAN + c-TF-IDF)"
            if c["bertopic"] else "scikit-learn NMF (BERTopic-style c-TF-IDF labels)"
        ),
        "ner": (
            f"spaCy ({config.SPACY_MODEL})"
            if c["spacy_model"] else "rule-based / gazetteer NER"
        ),
        "clustering": "scikit-learn KMeans (cosine space)",
        "lda": "scikit-learn LatentDirichletAllocation",
    }
