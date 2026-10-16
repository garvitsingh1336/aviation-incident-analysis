"""Stage 7: Clustering of similar incidents + 2-D projection for visualisation.

Groups reports by semantic similarity with KMeans over the (L2-normalised)
embedding space, labels each cluster with a class-based TF-IDF ("c-TF-IDF")
keyword list, reports a silhouette score as a quality signal, and computes a
2-D layout (UMAP when available, else SVD) so the dashboard can draw a semantic
map of the corpus.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .. import config
from ..core.capabilities import capabilities
from .preprocess import clean_corpus, sklearn_stopwords


def _cluster_labels(texts: List[str], doc_clusters: np.ndarray,
                   n_clusters: int) -> Dict[int, List[str]]:
    """class-based TF-IDF: treat each cluster's concatenated text as a document."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    cleaned = clean_corpus(texts)
    joined, present = [], []
    for c in range(n_clusters):
        docs = [cleaned[i] for i in np.where(doc_clusters == c)[0]]
        if docs:
            joined.append(" ".join(docs))
            present.append(c)
    if not joined:
        return {}
    vec = TfidfVectorizer(stop_words=list(sklearn_stopwords()),
                          ngram_range=(1, 2), min_df=1)
    X = vec.fit_transform(joined)
    vocab = np.array(vec.get_feature_names_out())
    labels = {}
    for row, c in enumerate(present):
        top = X[row].toarray()[0].argsort()[::-1][:6]
        labels[c] = vocab[top].tolist()
    return labels


def _project_2d(embeddings: np.ndarray) -> np.ndarray:
    caps = capabilities()
    n = embeddings.shape[0]
    if caps["bertopic"] and n > 10:  # umap is installed alongside bertopic
        try:
            from umap import UMAP

            reducer = UMAP(n_components=2, n_neighbors=15, min_dist=0.1,
                          metric="cosine", random_state=42)
            return reducer.fit_transform(embeddings)
        except Exception:
            pass
    from sklearn.decomposition import TruncatedSVD

    k = min(2, max(1, embeddings.shape[1] - 1))
    coords = TruncatedSVD(n_components=2, random_state=42).fit_transform(embeddings) \
        if embeddings.shape[1] > 2 else embeddings[:, :2]
    return coords


def run_clustering(embeddings: np.ndarray, texts: List[str]) -> Dict:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    n = embeddings.shape[0]
    n_clusters = int(min(config.N_CLUSTERS, max(2, n // 15)))
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    doc_clusters = km.fit_predict(embeddings)

    try:
        sil = float(silhouette_score(embeddings, doc_clusters, metric="cosine"))
    except Exception:
        sil = None

    labels = _cluster_labels(texts, doc_clusters, n_clusters)
    coords = _project_2d(embeddings)

    clusters = []
    for c in range(n_clusters):
        members = np.where(doc_clusters == c)[0]
        kw = labels.get(c, [])
        clusters.append({
            "cluster_id": int(c),
            "label": " / ".join(w.title() for w in kw[:3]) if kw else f"Cluster {c}",
            "keywords": kw,
            "size": int(len(members)),
            "representative_idx": members[:4].tolist(),
        })
    clusters.sort(key=lambda d: d["size"], reverse=True)

    return {
        "n_clusters": n_clusters,
        "silhouette": sil,
        "doc_clusters": doc_clusters.tolist(),
        "clusters": clusters,
        "coords_2d": np.asarray(coords, dtype=float).round(3).tolist(),
    }
