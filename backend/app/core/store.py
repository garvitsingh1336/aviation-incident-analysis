"""In-memory analysis store shared by the API layer.

Loads the persisted analysis artifact, the embedding matrix and the query
encoder once, then serves them.  If no artifacts exist yet it triggers a full
pipeline build.  A lightweight lookup index makes single-report access O(1).
"""
from __future__ import annotations

import json
import threading
from typing import Dict, List, Optional

import numpy as np

from .. import config
from ..pipeline import runner
from ..pipeline.embeddings import Embedder
from ..pipeline.search import SemanticSearcher


class AnalysisStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.analysis: Optional[Dict] = None
        self.embeddings: Optional[np.ndarray] = None
        self.searcher: Optional[SemanticSearcher] = None
        self._by_idx: Dict[int, Dict] = {}

    # -- lifecycle ---------------------------------------------------------- #
    def ensure_loaded(self, rebuild: bool = False) -> None:
        with self._lock:
            if self.analysis is not None and not rebuild:
                return
            if rebuild or not runner.artifacts_exist():
                runner.build_analysis(verbose=True)
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        with open(config.ANALYSIS_JSON, "r", encoding="utf-8") as fh:
            self.analysis = json.load(fh)
        self.embeddings = np.load(config.EMBEDDINGS_NPY)
        embedder = Embedder.load(config.EMBEDDER_PKL)
        self.searcher = SemanticSearcher(self.embeddings, embedder)
        self._by_idx = {r["idx"]: r for r in self.analysis["reports"]}

    def rebuild(self) -> Dict:
        self.ensure_loaded(rebuild=True)
        return self.analysis["meta"]

    # -- accessors ---------------------------------------------------------- #
    def report(self, idx: int) -> Optional[Dict]:
        return self._by_idx.get(idx)

    def reports(self) -> List[Dict]:
        return self.analysis["reports"]

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        hits = self.searcher.search(query, top_k=top_k)
        return [{**hit, "report": self._by_idx.get(hit["idx"])} for hit in hits]

    def similar(self, idx: int, top_k: int = 6) -> List[Dict]:
        hits = self.searcher.similar_to(idx, top_k=top_k)
        return [{**hit, "report": self._by_idx.get(hit["idx"])} for hit in hits]


# Module-level singleton used by the API.
store = AnalysisStore()
