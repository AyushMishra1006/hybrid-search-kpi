"""
Hybrid BM25 + vector search with configurable alpha weighting.
Normalization strategies: min-max (default) and z-score.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.utils.preprocessing import highlight_snippet


@dataclass
class SearchResult:
    doc_id: str
    title: str
    snippet: str
    bm25_score: float
    vector_score: float
    hybrid_score: float
    category: str = ""


def minmax_normalize(scores: list[float]) -> list[float]:
    """Scale scores to [0, 1]. Returns [0.5, ...] if all scores are equal."""
    min_s = min(scores)
    max_s = max(scores)
    if max_s == min_s:
        return [0.5] * len(scores)
    span = max_s - min_s
    return [(s - min_s) / span for s in scores]


def zscore_normalize(scores: list[float]) -> list[float]:
    """Z-score normalise scores. Returns [0.5, ...] if std is 0."""
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    std = variance ** 0.5
    if std == 0:
        return [0.5] * len(scores)
    return [(s - mean) / std for s in scores]


class HybridSearch:
    """Combines BM25 and vector indexes for hybrid retrieval."""

    def __init__(
        self,
        bm25_index: BM25Index,
        vector_index: VectorIndex,
        doc_store: dict[str, dict[str, Any]],
    ) -> None:
        self._bm25 = bm25_index
        self._vector = vector_index
        self._docs = doc_store  # doc_id → {title, text, category, ...}

    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        filters: dict[str, Any] | None = None,
        normalization: str = "minmax",
    ) -> list[SearchResult]:
        """
        Retrieve top_k*3 candidates from each index, fuse scores, apply filters,
        return top_k results.
        """
        if filters is None:
            filters = {}

        candidate_k = max(top_k * 3, 30)

        bm25_raw = self._bm25.query(query, top_k=candidate_k)
        vector_raw = self._vector.query(query, top_k=candidate_k)

        bm25_map: dict[str, float] = dict(bm25_raw)
        vector_map: dict[str, float] = dict(vector_raw)
        all_ids = list(set(bm25_map) | set(vector_map))

        bm25_scores = [bm25_map.get(did, 0.0) for did in all_ids]
        vector_scores = [vector_map.get(did, 0.0) for did in all_ids]

        normalize = zscore_normalize if normalization == "zscore" else minmax_normalize
        norm_bm25 = normalize(bm25_scores)
        norm_vector = normalize(vector_scores)

        fused = [
            (did, b, v, alpha * b + (1 - alpha) * v)
            for did, b, v in zip(all_ids, norm_bm25, norm_vector)
        ]

        if filters:
            fused = [
                (did, b, v, h)
                for did, b, v, h in fused
                if self._matches_filters(did, filters)
            ]

        fused.sort(key=lambda x: x[3], reverse=True)
        top = fused[:top_k]

        return [self._build_result(did, b, v, h, query) for did, b, v, h in top]

    def _matches_filters(self, doc_id: str, filters: dict[str, Any]) -> bool:
        doc = self._docs.get(doc_id)
        if doc is None:
            return False
        return all(doc.get(k) == v for k, v in filters.items())

    def _build_result(
        self,
        doc_id: str,
        bm25_score: float,
        vector_score: float,
        hybrid_score: float,
        query: str,
    ) -> SearchResult:
        doc = self._docs.get(doc_id, {})
        text = doc.get("text", "")
        return SearchResult(
            doc_id=doc_id,
            title=doc.get("title", doc_id),
            snippet=highlight_snippet(text, query),
            bm25_score=round(bm25_score, 6),
            vector_score=round(vector_score, 6),
            hybrid_score=round(hybrid_score, 6),
            category=doc.get("category", ""),
        )
