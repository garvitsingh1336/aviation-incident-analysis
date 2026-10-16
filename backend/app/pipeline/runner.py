"""Pipeline orchestrator.

Runs every stage once, assembles a single JSON-serialisable analysis artifact,
and persists it (plus the embedding matrix and the query encoder) to the store
directory.  The API layer then serves the cached artifact and only needs the
embedder loaded to answer live semantic-search queries.

Flow (matches the synopsis "Proposed Method"):
    load -> preprocess -> NER -> embeddings -> topics(+LDA) -> clustering
         -> contributing factors -> relationships -> trends -> assemble/persist
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict

import numpy as np

from .. import config
from ..core.capabilities import capabilities, engine_summary
from . import (clustering, data_loader, embeddings as emb, factors, ner,
               relationships, topics, trends)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_analysis(verbose: bool = True) -> Dict:
    def log(msg: str) -> None:
        if verbose:
            print(f"[pipeline] {msg}", flush=True)

    log("Stage 1-2: loading & preparing reports ...")
    df = data_loader.load_reports()
    texts = data_loader.corpus_texts(df)        # factor-focused (embeddings/topics)
    narratives = data_loader.narratives(df)     # full text (NER + display)
    n = len(texts)
    log(f"  -> {n} reports loaded")

    log("Stage 4: named entity recognition ...")
    per_report_entities, entity_aggregate = ner.run_ner(narratives)

    log("Stage 5: building semantic embeddings ...")
    matrix, embedder = emb.build_embeddings(texts)
    log(f"  -> embeddings {matrix.shape} via {embedder.backend}")

    log("Stage 6: topic modelling (BERTopic/NMF + LDA comparison) ...")
    topic_out = topics.run_topic_modeling(texts, matrix)
    primary = topic_out["primary"]
    doc_topics = primary["doc_topics"]

    log("Stage 7: clustering similar incidents ...")
    cluster_out = clustering.run_clustering(matrix, texts)

    log("Stage 8: contributing-factor analysis ...")
    factor_out = factors.analyse_factors(
        primary, doc_topics,
        severities=df["severity"].tolist(),
        true_factors=df["true_factors"].tolist()
        if "true_factors" in df.columns and df["true_factors"].notna().any() else None,
    )

    log("Stage 9: relationship (co-occurrence) analysis ...")
    rel_out = relationships.analyse_relationships(texts)

    log("Stage 10: trend analysis ...")
    trend_out = trends.analyse_trends(df["year"].tolist(), rel_out["per_report_themes"])

    log("Assembling report records ...")
    topic_label = {t["topic_id"]: t["label"] for t in primary["topics"]}
    cluster_label = {c["cluster_id"]: c["label"] for c in cluster_out["clusters"]}
    coords = cluster_out["coords_2d"]
    doc_clusters = cluster_out["doc_clusters"]
    per_themes = rel_out["per_report_themes"]

    reports = []
    for i in range(n):
        row = df.iloc[i]
        date_val = row["date"]
        reports.append({
            "idx": i,
            "report_id": row["report_id"],
            "date": None if _isna(date_val) else str(date_val.date()),
            "year": None if _isna(row["year"]) else int(row["year"]),
            "narrative": row["narrative"],
            "aircraft_type": _clean(row.get("aircraft_type")),
            "airport": _clean(row.get("airport")),
            "location": _clean(row.get("location")),
            "operator": _clean(row.get("operator")),
            "phase_of_flight": _clean(row.get("phase_of_flight")),
            "severity": _clean(row.get("severity")),
            "injury_level": _clean(row.get("injury_level")),
            "topic_id": int(doc_topics[i]),
            "topic_label": topic_label.get(int(doc_topics[i]), "Unclassified"),
            "cluster_id": int(doc_clusters[i]),
            "cluster_label": cluster_label.get(int(doc_clusters[i]), ""),
            "themes": per_themes[i],
            "entities": per_report_entities[i],
            "x": coords[i][0] if i < len(coords) else 0.0,
            "y": coords[i][1] if i < len(coords) else 0.0,
        })

    # Corpus-level statistics.
    sev_counts = df["severity"].value_counts(dropna=True).to_dict()
    stats = {
        "total_reports": n,
        "date_range": [
            None if df["date"].isna().all() else str(df["date"].min().date()),
            None if df["date"].isna().all() else str(df["date"].max().date()),
        ],
        "severity_counts": {str(k): int(v) for k, v in sev_counts.items()},
        "n_topics": len([t for t in primary["topics"] if t["topic_id"] != -1]),
        "n_clusters": cluster_out["n_clusters"],
        "n_themes": len(rel_out["nodes"]),
        "silhouette": cluster_out["silhouette"],
    }

    analysis = {
        "meta": {
            "generated_at": _now_iso(),
            "capabilities": capabilities(),
            "engines": engine_summary(),
            "embedding_backend": embedder.backend,
        },
        "stats": stats,
        "reports": reports,
        "topics": primary,
        "topics_comparison": topic_out["comparison"],
        "lda": topic_out["lda"],
        "clusters": {k: v for k, v in cluster_out.items() if k != "coords_2d"},
        "factors": factor_out,
        "relationships": {"nodes": rel_out["nodes"], "edges": rel_out["edges"]},
        "trends": trend_out,
        "entities": entity_aggregate,
    }

    log("Persisting artifacts ...")
    _persist(analysis, matrix, embedder)
    log(f"Done. Analysis written to {config.ANALYSIS_JSON}")
    return analysis


def _persist(analysis: Dict, matrix: np.ndarray, embedder) -> None:
    config.STORE_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.ANALYSIS_JSON, "w", encoding="utf-8") as fh:
        json.dump(analysis, fh, ensure_ascii=False)
    np.save(config.EMBEDDINGS_NPY, matrix)
    embedder.save(config.EMBEDDER_PKL)
    with open(config.META_JSON, "w", encoding="utf-8") as fh:
        json.dump({"generated_at": analysis["meta"]["generated_at"],
                   "n": matrix.shape[0]}, fh)


def artifacts_exist() -> bool:
    return config.ANALYSIS_JSON.exists() and config.EMBEDDINGS_NPY.exists()


# -- small helpers ---------------------------------------------------------- #
def _isna(v) -> bool:
    try:
        import pandas as pd

        return pd.isna(v)
    except Exception:
        return v is None


def _clean(v):
    if _isna(v):
        return None
    return v


if __name__ == "__main__":
    build_analysis(verbose=True)
