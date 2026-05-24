"""BM25 keyword index backed by rank-bm25 (BM25Okapi), persisted with joblib."""
from __future__ import annotations

from pathlib import Path

import joblib
from rank_bm25 import BM25Okapi

INDEX_FILENAME = "bm25_index.pkl"


class BM25Index:
    """Wraps BM25Okapi with build / query / save / load interface."""

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._doc_ids: list[str] = []

    def build(self, docs: list[str], doc_ids: list[str]) -> None:
        """Tokenize and fit BM25Okapi on the provided corpus strings."""
        if len(docs) != len(doc_ids):
            raise ValueError("docs and doc_ids must have equal length")
        tokenized = [doc.lower().split() for doc in docs]
        self._bm25 = BM25Okapi(tokenized)
        self._doc_ids = list(doc_ids)

    def query(self, q: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Return top_k (doc_id, raw_bm25_score) pairs, descending by score.
        Returns empty list if index not built or query is blank.
        """
        if self._bm25 is None:
            raise RuntimeError("BM25Index is not built. Call build() or load() first.")
        tokens = q.lower().split()
        if not tokens:
            return []
        scores: list[float] = self._bm25.get_scores(tokens).tolist()
        ranked = sorted(
            zip(self._doc_ids, scores), key=lambda x: x[1], reverse=True
        )
        return ranked[:top_k]

    def save(self, path: Path) -> None:
        """Persist index to <path>/bm25_index.pkl."""
        path.mkdir(parents=True, exist_ok=True)
        payload = {"bm25": self._bm25, "doc_ids": self._doc_ids}
        joblib.dump(payload, path / INDEX_FILENAME)

    def load(self, path: Path) -> None:
        """Load index from <path>/bm25_index.pkl."""
        payload = joblib.load(path / INDEX_FILENAME)
        self._bm25 = payload["bm25"]
        self._doc_ids = payload["doc_ids"]

    @property
    def num_docs(self) -> int:
        return len(self._doc_ids)
