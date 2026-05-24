"""
Unit tests for HybridSearch — alpha extremes, normalization math, NaN guard.
Uses a 5-doc toy corpus so BM25 and vector signals differ detectably.
"""
from __future__ import annotations

import pytest

from app.search.bm25 import BM25Index
from app.search.hybrid import HybridSearch, SearchResult, minmax_normalize, zscore_normalize
from app.search.vector import VectorIndex


CORPUS = [
    {"doc_id": "doc_001", "title": "Machine learning", "text": "machine learning trains models on data", "category": "computer_science"},
    {"doc_id": "doc_002", "title": "Photosynthesis",   "text": "photosynthesis converts sunlight to energy in plants", "category": "biology"},
    {"doc_id": "doc_003", "title": "Quantum physics",  "text": "quantum mechanics describes particle behavior at small scales", "category": "physics"},
    {"doc_id": "doc_004", "title": "Neural networks",  "text": "neural networks are machine learning models with layers", "category": "computer_science"},
    {"doc_id": "doc_005", "title": "DNA structure",    "text": "dna is a molecule that carries genetic information", "category": "biology"},
]


@pytest.fixture(scope="module")
def hybrid() -> HybridSearch:
    docs_list = [f"{d['title']} {d['text']}" for d in CORPUS]
    ids = [d["doc_id"] for d in CORPUS]
    doc_store = {d["doc_id"]: d for d in CORPUS}

    bm25 = BM25Index()
    bm25.build(docs_list, ids)

    vec = VectorIndex()
    vec.build(docs_list, ids)

    return HybridSearch(bm25, vec, doc_store)


class TestHybridAlphaExtremes:
    def test_alpha_1_pure_bm25(self, hybrid: HybridSearch) -> None:
        """alpha=1.0 → hybrid score == normalised BM25 score (vector contribution = 0)."""
        results = hybrid.search("machine learning", top_k=5, alpha=1.0)
        for r in results:
            assert abs(r.hybrid_score - r.bm25_score) < 1e-4

    def test_alpha_0_pure_vector(self, hybrid: HybridSearch) -> None:
        """alpha=0.0 → hybrid score == normalised vector score (BM25 contribution = 0)."""
        results = hybrid.search("machine learning", top_k=5, alpha=0.0)
        for r in results:
            assert abs(r.hybrid_score - r.vector_score) < 1e-4

    def test_alpha_05_blend(self, hybrid: HybridSearch) -> None:
        """alpha=0.5 → hybrid is the average of norm_bm25 and norm_vector."""
        results = hybrid.search("machine learning", top_k=5, alpha=0.5)
        for r in results:
            expected = 0.5 * r.bm25_score + 0.5 * r.vector_score
            assert abs(r.hybrid_score - expected) < 1e-4


class TestHybridNormalization:
    def test_minmax_output_in_01(self) -> None:
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        normed = minmax_normalize(scores)
        assert min(normed) == pytest.approx(0.0)
        assert max(normed) == pytest.approx(1.0)

    def test_minmax_math_correct(self) -> None:
        scores = [0.0, 5.0, 10.0]
        normed = minmax_normalize(scores)
        assert normed == pytest.approx([0.0, 0.5, 1.0])

    def test_minmax_nan_guard(self) -> None:
        """Scenario C regression: all-equal scores must not produce NaN."""
        normed = minmax_normalize([1.0, 1.0, 1.0])
        assert normed == [0.5, 0.5, 0.5]

    def test_minmax_single_element(self) -> None:
        assert minmax_normalize([3.7]) == [0.5]

    def test_zscore_zero_mean_unit_std(self) -> None:
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        normed = zscore_normalize(scores)
        mean = sum(normed) / len(normed)
        assert abs(mean) < 1e-9

    def test_zscore_nan_guard(self) -> None:
        normed = zscore_normalize([4.0, 4.0, 4.0])
        assert normed == [0.5, 0.5, 0.5]

    def test_zscore_math_correct(self) -> None:
        scores = [0.0, 1.0]
        normed = zscore_normalize(scores)
        assert normed[0] < 0 and normed[1] > 0


class TestHybridFilters:
    def test_filter_by_category(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("learning", top_k=10, filters={"category": "biology"})
        for r in results:
            doc_cats = {d["doc_id"]: d["category"] for d in CORPUS}
            assert doc_cats[r.doc_id] == "biology"

    def test_no_filter_returns_all_candidates(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("science", top_k=5, filters={})
        assert len(results) <= 5

    def test_nonexistent_filter_returns_empty(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("machine", top_k=10, filters={"category": "nonexistent"})
        assert results == []


class TestSearchResult:
    def test_result_fields_present(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("machine learning", top_k=3)
        assert len(results) >= 1
        r = results[0]
        assert isinstance(r, SearchResult)
        assert r.doc_id
        assert r.title
        assert isinstance(r.snippet, str)
        assert isinstance(r.bm25_score, float)
        assert isinstance(r.vector_score, float)
        assert isinstance(r.hybrid_score, float)

    def test_top_k_respected(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("machine learning", top_k=2)
        assert len(results) <= 2

    def test_results_sorted_descending(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("learning", top_k=5)
        scores = [r.hybrid_score for r in results]
        assert scores == sorted(scores, reverse=True)
