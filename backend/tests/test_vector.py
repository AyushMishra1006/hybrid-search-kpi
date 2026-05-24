"""Unit tests for VectorIndex — encode, query, nearest-neighbor, metadata validation."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.search.vector import DIMENSION, MODEL_NAME, VectorIndex


CORPUS_DOCS = [
    "machine learning trains models on data",
    "photosynthesis converts sunlight into energy in plants",
    "the French Revolution transformed society and government",
]
CORPUS_IDS = ["doc_001", "doc_002", "doc_003"]


@pytest.fixture(scope="module")
def built_index() -> VectorIndex:
    idx = VectorIndex()
    idx.build(CORPUS_DOCS, CORPUS_IDS)
    return idx


class TestVectorBuild:
    def test_num_docs(self, built_index: VectorIndex) -> None:
        assert built_index.num_docs == 3

    def test_mismatched_lengths_raise(self) -> None:
        idx = VectorIndex()
        with pytest.raises(ValueError):
            idx.build(["doc a", "doc b"], ["id_1"])

    def test_query_before_build_raises(self) -> None:
        idx = VectorIndex()
        with pytest.raises(RuntimeError):
            idx.query("machine learning")


class TestVectorQuery:
    def test_nearest_neighbor_ml_query(self, built_index: VectorIndex) -> None:
        results = built_index.query("supervised learning algorithm", top_k=3)
        assert results[0][0] == "doc_001"

    def test_nearest_neighbor_biology_query(self, built_index: VectorIndex) -> None:
        results = built_index.query("chlorophyll and sunlight in leaves", top_k=3)
        assert results[0][0] == "doc_002"

    def test_scores_descending(self, built_index: VectorIndex) -> None:
        results = built_index.query("machine learning", top_k=3)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_respected(self, built_index: VectorIndex) -> None:
        results = built_index.query("learning", top_k=2)
        assert len(results) == 2

    def test_scores_in_valid_cosine_range(self, built_index: VectorIndex) -> None:
        results = built_index.query("machine learning", top_k=3)
        for _, score in results:
            assert -1.01 <= score <= 1.01


class TestVectorPersistence:
    def test_save_load_round_trip(self, built_index: VectorIndex) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            built_index.save(path, corpus_hash="abc123")
            assert (path / "faiss.index").exists()
            assert (path / "doc_ids.json").exists()
            assert (path / "metadata.json").exists()

            loaded = VectorIndex()
            loaded.load(path)
            assert loaded.num_docs == built_index.num_docs

            orig = built_index.query("machine learning", top_k=2)
            restored = loaded.query("machine learning", top_k=2)
            assert [d for d, _ in orig] == [d for d, _ in restored]

    def test_metadata_json_fields(self, built_index: VectorIndex) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            built_index.save(path, corpus_hash="test_hash")
            meta = json.loads((path / "metadata.json").read_text())
            assert meta["model_name"] == MODEL_NAME
            assert meta["dimension"] == DIMENSION
            assert meta["corpus_hash"] == "test_hash"
            assert meta["num_docs"] == 3


class TestMetadataValidation:
    def test_valid_metadata_passes(self, built_index: VectorIndex) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            built_index.save(path)
            VectorIndex.validate_metadata(path)  # should not raise

    def test_wrong_model_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            bad_meta = {
                "model_name": "paraphrase-MiniLM-L3-v2",
                "dimension": 128,
                "corpus_hash": "",
                "build_timestamp": "2024-01-01T00:00:00+00:00",
                "num_docs": 3,
            }
            (path / "metadata.json").write_text(json.dumps(bad_meta))
            with pytest.raises(ValueError, match="Rebuild with"):
                VectorIndex.validate_metadata(path)

    def test_missing_metadata_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(FileNotFoundError):
                VectorIndex.validate_metadata(Path(tmp))
