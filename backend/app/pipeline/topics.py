"""Stage 6: Topic modelling.

Primary engine is **BERTopic** (embedding + UMAP + HDBSCAN + c-TF-IDF), exactly
as named in the synopsis.  A scikit-learn **NMF** model provides the same
interface when BERTopic is unavailable, and **LDA** (LatentDirichletAllocation)
is always run as the "additional comparison method" the synopsis mentions.

Every engine returns topics in a common shape::

    {
      "engine": str,
      "topics": [{topic_id, label, keywords:[[word,score]...], size,
                  representative_idx:[...]}],
      "doc_topics": [topic_id per document],
    }
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .. import config
from ..core.capabilities import capabilities
from .preprocess import clean_corpus, sklearn_stopwords


def _label_from_keywords(words: List[str]) -> str:
    """Build a short human-readable label from the top keywords."""
    picked = [w for w in words if w][:4]
    return " / ".join(w.title() for w in picked) if picked else "Misc"


def _representative_docs(doc_topics: np.ndarray, topic_id: int,
                        scores: np.ndarray, k: int = 4) -> List[int]:
    idx = np.where(doc_topics == topic_id)[0]
    if len(idx) == 0:
        return []
    if scores is not None:
        idx = idx[np.argsort(scores[idx])[::-1]]
    return idx[:k].tolist()


# --------------------------------------------------------------------------- #
# BERTopic (primary)
# --------------------------------------------------------------------------- #
def _run_bertopic(texts: List[str], embeddings: np.ndarray) -> Dict:
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP
    from hdbscan import HDBSCAN

    vectorizer = CountVectorizer(
        stop_words=list(sklearn_stopwords()), ngram_range=(1, 2), min_df=2,
    )
    umap_model = UMAP(
        n_neighbors=10, n_components=5, min_dist=0.0,
        metric="cosine", random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=config.MIN_TOPIC_SIZE, metric="euclidean",
        cluster_selection_method="eom", prediction_data=True,
    )
    model = BERTopic(
        vectorizer_model=vectorizer,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        embedding_model=None,
        calculate_probabilities=False,
        verbose=False,
    )
    doc_topics, _ = model.fit_transform(texts, embeddings=embeddings)
    doc_topics = np.asarray(doc_topics)

    info = model.get_topic_info()
    topics = []
    for _, row in info.iterrows():
        tid = int(row["Topic"])
        kw = model.get_topic(tid) or []
        words = [w for w, _ in kw][:10]
        keywords = [[w, float(s)] for w, s in kw][:10]
        if tid == -1:
            label = "Unclassified / Outliers"
        else:
            label = _label_from_keywords(words)
        topics.append({
            "topic_id": tid,
            "label": label,
            "keywords": keywords,
            "size": int(row["Count"]),
            "representative_idx": _representative_docs(doc_topics, tid, None),
        })
    return {"engine": "BERTopic", "topics": topics,
            "doc_topics": doc_topics.tolist()}


# --------------------------------------------------------------------------- #
# NMF fallback (BERTopic-style output)
# --------------------------------------------------------------------------- #
def _run_nmf(texts: List[str]) -> Dict:
    from sklearn.decomposition import NMF
    from sklearn.feature_extraction.text import TfidfVectorizer

    cleaned = clean_corpus(texts)
    n_topics = config.N_CLUSTERS
    vectorizer = TfidfVectorizer(
        stop_words=list(sklearn_stopwords()), ngram_range=(1, 2),
        min_df=2, max_df=0.6,
    )
    X = vectorizer.fit_transform(cleaned)
    vocab = np.array(vectorizer.get_feature_names_out())
    nmf = NMF(n_components=n_topics, random_state=42, init="nndsvda", max_iter=400)
    W = nmf.fit_transform(X)      # doc x topic
    H = nmf.components_           # topic x term

    doc_topics = W.argmax(axis=1)
    doc_scores = W.max(axis=1)

    topics = []
    for t in range(n_topics):
        top_idx = H[t].argsort()[::-1][:10]
        words = vocab[top_idx].tolist()
        keywords = [[vocab[i], float(H[t][i])] for i in top_idx]
        topics.append({
            "topic_id": int(t),
            "label": _label_from_keywords(words),
            "keywords": keywords,
            "size": int(np.sum(doc_topics == t)),
            "representative_idx": _representative_docs(doc_topics, t, doc_scores),
        })
    topics.sort(key=lambda d: d["size"], reverse=True)
    return {"engine": "NMF (scikit-learn)", "topics": topics,
            "doc_topics": doc_topics.tolist()}


# --------------------------------------------------------------------------- #
# LDA comparison (always run)
# --------------------------------------------------------------------------- #
def _run_lda(texts: List[str], n_topics: int) -> Dict:
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    cleaned = clean_corpus(texts)
    vectorizer = CountVectorizer(
        stop_words=list(sklearn_stopwords()), ngram_range=(1, 1),
        min_df=2, max_df=0.6,
    )
    X = vectorizer.fit_transform(cleaned)
    vocab = np.array(vectorizer.get_feature_names_out())
    lda = LatentDirichletAllocation(
        n_components=n_topics, random_state=42, learning_method="batch",
        max_iter=30,
    )
    doc_topic = lda.fit_transform(X)
    assignments = doc_topic.argmax(axis=1)

    topics = []
    for t in range(n_topics):
        top_idx = lda.components_[t].argsort()[::-1][:10]
        words = vocab[top_idx].tolist()
        topics.append({
            "topic_id": int(t),
            "label": _label_from_keywords(words),
            "keywords": [[vocab[i], float(lda.components_[t][i])] for i in top_idx],
            "size": int(np.sum(assignments == t)),
        })
    topics.sort(key=lambda d: d["size"], reverse=True)
    # Perplexity is a standard (if imperfect) LDA quality signal.
    try:
        perplexity = float(lda.perplexity(X))
    except Exception:
        perplexity = None
    return {"engine": "LDA (scikit-learn)", "topics": topics,
            "doc_topics": assignments.tolist(), "perplexity": perplexity}


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def run_topic_modeling(texts: List[str], embeddings: np.ndarray) -> Dict:
    caps = capabilities()
    if caps["bertopic"]:
        try:
            primary = _run_bertopic(texts, embeddings)
        except Exception as exc:  # pragma: no cover - robustness net
            primary = _run_nmf(texts)
            primary["engine"] += f"  (BERTopic failed: {type(exc).__name__})"
    else:
        primary = _run_nmf(texts)

    n_primary = len([t for t in primary["topics"] if t["topic_id"] != -1])
    lda = _run_lda(texts, n_topics=max(4, min(n_primary or config.N_CLUSTERS, 16)))

    return {
        "primary": primary,
        "lda": lda,
        "comparison": {
            "primary_engine": primary["engine"],
            "primary_topics": n_primary,
            "lda_topics": len(lda["topics"]),
            "lda_perplexity": lda.get("perplexity"),
        },
    }
