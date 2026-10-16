"""Stage 5: Text embeddings.

Converts report narratives into dense semantic vectors.  Primary engine is
``sentence-transformers`` (as named in the synopsis); the fallback is a
TF-IDF + TruncatedSVD ("LSA") pipeline from scikit-learn.  Both produce L2
-normalised vectors so cosine similarity reduces to a dot product, and both are
exposed through a single :class:`Embedder` interface that can re-encode a query
string at search time.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np

from .. import config
from ..core.capabilities import capabilities


class Embedder:
    """Uniform, serialisable encoder wrapping either backend."""

    def __init__(self, backend: str, model_name: str = "",
                 sklearn_pipe=None):
        self.backend = backend
        self.model_name = model_name
        self._sklearn_pipe = sklearn_pipe
        self._st_model = None  # lazily loaded sentence-transformers model

    # -- encoding ----------------------------------------------------------- #
    def encode(self, texts: List[str]) -> np.ndarray:
        if self.backend == "sentence-transformers":
            model = self._load_st()
            vecs = model.encode(texts, normalize_embeddings=True,
                                show_progress_bar=False)
            return np.asarray(vecs, dtype=np.float32)
        # tfidf-svd fallback
        from .preprocess import clean_corpus

        X = self._sklearn_pipe.transform(clean_corpus(texts))
        return _l2_normalize(np.asarray(X, dtype=np.float32))

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    def _load_st(self):
        if self._st_model is None:
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer(self.model_name)
        return self._st_model

    # -- persistence -------------------------------------------------------- #
    def save(self, path: Path) -> None:
        payload = {"backend": self.backend, "model_name": self.model_name}
        if self.backend != "sentence-transformers":
            payload["sklearn_pipe"] = self._sklearn_pipe
        with open(path, "wb") as fh:
            pickle.dump(payload, fh)

    @classmethod
    def load(cls, path: Path) -> "Embedder":
        with open(path, "rb") as fh:
            payload = pickle.load(fh)
        return cls(
            backend=payload["backend"],
            model_name=payload.get("model_name", ""),
            sklearn_pipe=payload.get("sklearn_pipe"),
        )


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def build_embeddings(texts: List[str]):
    """Return ``(matrix, embedder)`` for the given corpus."""
    caps = capabilities()
    if caps["sentence_transformers"]:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(config.EMBEDDING_MODEL)
        matrix = model.encode(texts, normalize_embeddings=True,
                              show_progress_bar=False, batch_size=64)
        matrix = np.asarray(matrix, dtype=np.float32)
        embedder = Embedder("sentence-transformers", config.EMBEDDING_MODEL)
        embedder._st_model = model
        return matrix, embedder

    # ---- Fallback: TF-IDF + TruncatedSVD (latent semantic analysis) ------- #
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import make_pipeline

    from .preprocess import clean_corpus, sklearn_stopwords

    cleaned = clean_corpus(texts)
    n_docs = len(cleaned)
    n_comp = int(min(256, max(2, n_docs - 1)))
    vectorizer = TfidfVectorizer(
        stop_words=list(sklearn_stopwords()),
        ngram_range=(1, 2), min_df=2, max_df=0.6,
    )
    svd = TruncatedSVD(n_components=n_comp, random_state=42)
    pipe = make_pipeline(vectorizer, svd)
    matrix = pipe.fit_transform(cleaned)
    matrix = _l2_normalize(np.asarray(matrix, dtype=np.float32))
    embedder = Embedder("tfidf-svd", "tfidf+svd", sklearn_pipe=pipe)
    return matrix, embedder
