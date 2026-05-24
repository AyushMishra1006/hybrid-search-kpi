"""Unit tests for BM25Index — 3-doc toy corpus, deterministic ordering."""
import tempfile
from pathlib import Path

import pytest

from app.search.bm25 import BM25Index


CORPUS_DOCS = [
    "machine learning is a subset of artificial intelligence",
    "deep learning uses neural networks with many layers",
    "natural language processing handles text and speech",
]
CORPUS_IDS = ["doc_001", "doc_002", "doc_003"]


@pytest.fixture()
def built_index() -> BM25Index:
    idx = BM25Index()
    idx.build(CORPUS_DOCS, CORPUS_IDS)
    return idx


class TestBM25Build:
    def test_num_docs(self, built_index: BM25Index) -> None:
        assert built_index.num_docs == 3

    def test_mismatched_lengths_raise(self) -> None:
        idx = BM25Index()
        with pytest.raises(ValueError):
            idx.build(["doc a", "doc b"], ["id_1"])

    def test_query_before_build_raises(self) -> None:
        idx = BM25Index()
        with pytest.raises(RuntimeError):
            idx.query("machine learning")


class TestBM25Query:
    def test_top_result_for_ml_query(self, built_index: BM25Index) -> None:
        results = built_index.query("machine learning", top_k=3)
        assert results[0][0] == "doc_001"

    def test_top_result_for_nlp_query(self, built_index: BM25Index) -> None:
        results = built_index.query("natural language text", top_k=3)
        assert results[0][0] == "doc_003"

    def test_returns_correct_count(self, built_index: BM25Index) -> None:
        results = built_index.query("learning", top_k=2)
        assert len(results) <= 2

    def test_scores_descending(self, built_index: BM25Index) -> None:
        results = built_index.query("learning neural", top_k=3)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_blank_query_returns_empty(self, built_index: BM25Index) -> None:
        results = built_index.query("", top_k=10)
        assert results == []

    def test_top_k_larger_than_corpus(self, built_index: BM25Index) -> None:
        results = built_index.query("machine", top_k=100)
        assert len(results) == 3


class TestBM25Persistence:
    def test_save_load_round_trip(self, built_index: BM25Index) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            built_index.save(path)
            assert (path / "bm25_index.pkl").exists()

            loaded = BM25Index()
            loaded.load(path)
            assert loaded.num_docs == built_index.num_docs

            original_results = built_index.query("machine learning", top_k=3)
            loaded_results = loaded.query("machine learning", top_k=3)
            assert original_results == loaded_results
