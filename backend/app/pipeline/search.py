"""Stage 11: Semantic search.

Uses the persisted embedding matrix and the same :class:`Embedder` that built it
to answer meaning-based queries.  A query such as "poor visibility" returns
reports that discuss fog, low ceilings or reduced visibility even when the exact
phrase never appears — the key advantage of embeddings over keyword search.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .embeddings import Embedder


class SemanticSearcher:
    def __init__(self, embeddings: np.ndarray, embedder: Embedder):
        self.embeddings = embeddings              # (n, d) L2-normalised
        self.embedder = embedder

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        q = self.embedder.encode_one(query).astype(np.float32)
        qn = q / (np.linalg.norm(q) or 1.0)
        # embeddings already L2-normalised => cosine similarity is a dot product.
        scores = self.embeddings @ qn
        order = np.argsort(scores)[::-1][:top_k]
        return [{"idx": int(i), "score": round(float(scores[i]), 4)} for i in order]

    def similar_to(self, idx: int, top_k: int = 6) -> List[Dict]:
        """Reports most similar to a given report (excludes itself)."""
        scores = self.embeddings @ self.embeddings[idx]
        order = np.argsort(scores)[::-1]
        order = [int(i) for i in order if int(i) != idx][:top_k]
        return [{"idx": i, "score": round(float(scores[i]), 4)} for i in order]
