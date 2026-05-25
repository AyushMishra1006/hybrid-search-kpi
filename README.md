# Hybrid Search + KPI Dashboard

End-to-end Knowledge Search system with BM25 + semantic vector retrieval, a FastAPI backend, and a React+Vite analytics dashboard.

---

## Architecture

```
data/raw/ (400 arXiv CS paper abstracts — cs.LG/cs.CL/cs.CV/cs.AI/cs.IR)
    └── app.ingest → data/processed/docs.jsonl
    └── app.index  → data/index/bm25/ + data/index/vector/
                         │
                    FastAPI (port 8000)
                    ├── POST /search   → BM25 + vector hybrid scoring
                    ├── GET  /health
                    ├── GET  /metrics
                    ├── GET  /dashboard/kpi
                    ├── GET  /dashboard/logs
                    └── GET  /dashboard/experiments
                         │
                    React+Vite (port 5173)
                    ├── /search   — query box, alpha slider, score breakdown
                    ├── /kpi      — latency cards, request volume chart
                    ├── /eval     — experiment table + nDCG trend
                    └── /debug    — structured log viewer
```

SQLite (`data/search.db`) stores every query: `request_id`, `query`, `latency_ms`, `top_k`, `alpha`, `result_count`, `severity`, `error`.

---

## 1-Minute Quickstart

```bash
# Prerequisites: bash, python 3.11+, node 18+
git clone <repo-url>
cd hybrid-search-kpi
chmod +x up.sh
./up.sh
# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
```

---

## How to Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## How to Run Evaluation

```bash
# Single run (alpha=0.5, minmax normalization)
python -m app.eval \
  --queries data/eval/queries.jsonl \
  --qrels   data/eval/qrels.json \
  --alpha   0.5 \
  --normalization minmax

# All 5 experiments
python -m app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.5  --normalization minmax
python -m app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.5  --normalization zscore
python -m app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.3  --normalization minmax
python -m app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.7  --normalization minmax
python -m app.eval --queries data/eval/queries.jsonl --qrels data/eval/qrels.json --alpha 0.9  --normalization minmax
```

Results append to `data/metrics/experiments.csv`.

---

## CLI Commands

```bash
# Ingest raw .txt files → JSONL
python -m app.ingest --input data/raw --out data/processed

# Build BM25 + FAISS indexes
python -m app.index --input data/processed/docs.jsonl

# Start backend
uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Stop all services
./down.sh
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| BM25 | rank-bm25 (BM25Okapi) |
| Embeddings | sentence-transformers `BAAI/bge-small-en-v1.5` (384-dim, asymmetric retrieval) |
| Vector index | faiss-cpu, IndexFlatIP + L2-normalize = cosine similarity |
| Storage | SQLite + local filesystem |
| Frontend | React + Vite |
| Testing | pytest + httpx TestClient |
| Rate limiting | slowapi (30 req/min on /search) |

---

## Dataset

400 arXiv CS paper abstracts sourced from `gfissore/arxiv-abstracts-2021` (HuggingFace), CC BY license.
80 papers each from: `cs.LG` (ML), `cs.CL` (NLP), `cs.CV` (Vision), `cs.AI` (AI), `cs.IR` (IR).
Committed to `data/raw/` — fully deterministic corpus, no internet download required at run time.
Filterable by `category` (arXiv subcategory) and `year` via POST /search `filters` field.

---

## Docs

- [`docs/architecture.md`](docs/architecture.md) — full system diagram + SQLite schema
- [`docs/decision_log.md`](docs/decision_log.md) — all design decisions with rationale
- [`docs/codex_log.md`](docs/codex_log.md) — granular AI prompt log per commit
- [`docs/break_fix_log.md`](docs/break_fix_log.md) — 3 induced failure scenarios + fixes
