"""API contract tests: shape, score breakdown, validation, dashboard endpoints."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex

_DOCS = [
    {
        "doc_id": "doc_001",
        "title": "Deep Reinforcement Learning: An Overview",
        "text": "Reinforcement learning is a machine learning paradigm where agents learn by interacting with an environment using reward signals",
        "source": "arxiv",
        "created_at": "2017-01-01",
        "category": "cs.LG",
        "year": "2017",
    },
    {
        "doc_id": "doc_002",
        "title": "Attention Mechanisms in Neural Machine Translation",
        "text": "Attention mechanisms allow sequence to sequence models to focus on relevant parts of the input when generating each output token",
        "source": "arxiv",
        "created_at": "2017-03-01",
        "category": "cs.CL",
        "year": "2017",
    },
    {
        "doc_id": "doc_003",
        "title": "Convolutional Neural Networks for Image Recognition",
        "text": "Convolutional networks learn hierarchical feature representations from raw pixel values enabling state of the art image classification",
        "source": "arxiv",
        "created_at": "2017-06-01",
        "category": "cs.CV",
        "year": "2017",
    },
    {
        "doc_id": "doc_004",
        "title": "Generative Adversarial Networks for Image Synthesis",
        "text": "Generative adversarial networks train a generator and discriminator jointly to produce realistic synthetic images",
        "source": "arxiv",
        "created_at": "2017-09-01",
        "category": "cs.CV",
        "year": "2017",
    },
    {
        "doc_id": "doc_005",
        "title": "Neural Information Retrieval with Dense Representations",
        "text": "Dense retrieval models encode queries and documents into vector spaces and retrieve by approximate nearest neighbour search",
        "source": "arxiv",
        "created_at": "2017-11-01",
        "category": "cs.IR",
        "year": "2017",
    },
]


def _write_docs_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for doc in _DOCS:
            fh.write(json.dumps(doc) + "\n")


def _build_toy_indexes(tmp: Path) -> None:
    corpus = [d["title"] + " " + d["text"] for d in _DOCS]
    ids = [d["doc_id"] for d in _DOCS]

    bm25 = BM25Index()
    bm25.build(corpus, ids)
    bm25.save(tmp / "bm25")

    vec = VectorIndex()
    vec.build(corpus, ids)
    vec.save(tmp / "vector", corpus_hash="testhash")


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory):
    tmp = tmp_path_factory.mktemp("api_test")
    _write_docs_jsonl(tmp / "docs.jsonl")
    _build_toy_indexes(tmp)

    import app.api.main as main_mod

    # Patch module-level path constants before lifespan fires
    orig = (main_mod._BM25_DIR, main_mod._VECTOR_DIR, main_mod._DOCS_JSONL, main_mod._DB_PATH)
    main_mod._BM25_DIR = tmp / "bm25"
    main_mod._VECTOR_DIR = tmp / "vector"
    main_mod._DOCS_JSONL = tmp / "docs.jsonl"
    main_mod._DB_PATH = tmp / "test.db"

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    main_mod._BM25_DIR, main_mod._VECTOR_DIR, main_mod._DOCS_JSONL, main_mod._DB_PATH = orig


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        assert client.get("/health").status_code == 200

    def test_has_required_fields(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "status" in data
        assert "version" in data
        assert "commit" in data

    def test_status_is_ok(self, client: TestClient) -> None:
        assert client.get("/health").json()["status"] == "OK"


# ---------------------------------------------------------------------------
# /search
# ---------------------------------------------------------------------------

class TestSearchEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        assert client.post("/search", json={"query": "machine learning"}).status_code == 200

    def test_top_level_fields_present(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning"}).json()
        assert "results" in data
        assert "query" in data
        assert "latency_ms" in data
        assert "result_count" in data
        assert "filters_applied" in data

    def test_each_result_has_three_scores(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning"}).json()
        assert len(data["results"]) > 0
        item = data["results"][0]
        assert "bm25_score" in item
        assert "vector_score" in item
        assert "hybrid_score" in item

    def test_each_result_has_doc_id_title_snippet(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning"}).json()
        item = data["results"][0]
        assert "doc_id" in item
        assert "title" in item
        assert "snippet" in item

    def test_result_count_matches_results_length(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning"}).json()
        assert data["result_count"] == len(data["results"])

    def test_query_echoed_in_response(self, client: TestClient) -> None:
        q = "neural networks brain"
        assert client.post("/search", json={"query": q}).json()["query"] == q

    def test_filters_applied_echoed(self, client: TestClient) -> None:
        filters = {"category": "cs.LG"}
        data = client.post("/search", json={"query": "reinforcement learning", "filters": filters}).json()
        assert data["filters_applied"] == filters

    def test_top_k_limits_results(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "science", "top_k": 2}).json()
        assert len(data["results"]) <= 2

    def test_latency_is_positive_float(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning"}).json()
        assert isinstance(data["latency_ms"], float)
        assert data["latency_ms"] > 0

    def test_empty_query_returns_422(self, client: TestClient) -> None:
        assert client.post("/search", json={"query": ""}).status_code == 422

    def test_top_k_zero_returns_422(self, client: TestClient) -> None:
        assert client.post("/search", json={"query": "ml", "top_k": 0}).status_code == 422

    def test_top_k_over_50_returns_422(self, client: TestClient) -> None:
        assert client.post("/search", json={"query": "ml", "top_k": 51}).status_code == 422

    def test_alpha_over_1_returns_422(self, client: TestClient) -> None:
        assert client.post("/search", json={"query": "ml", "alpha": 1.5}).status_code == 422

    def test_alpha_1_pure_bm25_returns_results(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning", "alpha": 1.0}).json()
        assert len(data["results"]) > 0

    def test_alpha_0_pure_vector_returns_results(self, client: TestClient) -> None:
        data = client.post("/search", json={"query": "machine learning", "alpha": 0.0}).json()
        assert len(data["results"]) > 0


# ---------------------------------------------------------------------------
# /feedback
# ---------------------------------------------------------------------------

class TestFeedbackEndpoint:
    def test_returns_204(self, client: TestClient) -> None:
        r = client.post("/feedback", json={"query": "ml", "doc_id": "doc_001", "relevant": True})
        assert r.status_code == 204


# ---------------------------------------------------------------------------
# /metrics
# ---------------------------------------------------------------------------

class TestMetricsEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        assert client.get("/metrics").status_code == 200

    def test_content_type_is_plain_text(self, client: TestClient) -> None:
        r = client.get("/metrics")
        assert "text/plain" in r.headers["content-type"]

    def test_all_metric_names_present(self, client: TestClient) -> None:
        text = client.get("/metrics").text
        assert "search_requests_total" in text
        assert "search_latency_p50_ms" in text
        assert "search_latency_p95_ms" in text
        assert "zero_result_queries_total" in text
        assert "search_errors_total" in text


# ---------------------------------------------------------------------------
# /dashboard/*
# ---------------------------------------------------------------------------

class TestDashboardEndpoints:
    def test_kpi_has_required_fields(self, client: TestClient) -> None:
        client.post("/search", json={"query": "machine learning"})  # seed a log row
        data = client.get("/dashboard/kpi").json()
        assert "latency_p50_ms" in data
        assert "latency_p95_ms" in data
        assert "request_volume" in data
        assert "top_queries" in data
        assert "zero_result_queries" in data

    def test_logs_returns_list(self, client: TestClient) -> None:
        assert isinstance(client.get("/dashboard/logs").json(), list)

    def test_logs_severity_filter_accepted(self, client: TestClient) -> None:
        assert client.get("/dashboard/logs?severity=info").status_code == 200

    def test_experiments_returns_list(self, client: TestClient) -> None:
        assert isinstance(client.get("/dashboard/experiments").json(), list)
