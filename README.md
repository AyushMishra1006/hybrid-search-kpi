# Hybrid Search + KPI Dashboard

A production-style knowledge search engine that combines BM25 lexical retrieval and
semantic vector search into a configurable hybrid pipeline, backed by a FastAPI service
and a React analytics dashboard.

---

## Pipeline

```
 data/raw/  (400 arXiv CS abstracts · cs.LG · cs.CL · cs.CV · cs.AI · cs.IR)
      │
      │  python -m app.ingest
      ▼
 data/processed/docs.jsonl
      │
      │  python -m app.index
      ▼
 ┌────────────────────────────────────────┐
 │  BM25 index        Vector index        │
 │  rank-bm25         BAAI/bge-small-en   │
 │  data/index/bm25/  + FAISS CPU         │
 │                    data/index/vector/  │
 └─────────────────┬──────────────────────┘
                   │
                   │  FastAPI  ·  port 8000
                   ▼
        POST /search  { query, alpha, top_k, filters }
               │
               │  score = alpha · norm_bm25 + (1-alpha) · norm_vector
               ▼
        ranked results  { bm25_score, vector_score, hybrid_score, snippet }
               │
               │  React + Vite  ·  port 5173
               ▼
        ┌──────────────────────────────────┐
        │  Search   results + score bars   │
        │  KPI      latency · p50/p95      │
        │  Eval     nDCG trend · 5 runs    │
        │  Debug    structured log viewer  │
        └──────────────────────────────────┘
               │
               ▼
        SQLite  data/search.db
        (every query logged: latency, alpha, result_count, severity)
```

---

## Quickstart

**Prerequisites:** bash (or WSL on Windows), Python 3.11+, Node 18+

```bash
git clone <repo-url>
cd hybrid-search-kpi
chmod +x up.sh
./up.sh
```

`up.sh` is fully idempotent — safe to run twice. It creates the venv, installs
dependencies, builds indexes (only if missing), and starts both servers.

```
Backend  → http://localhost:8000
Frontend → http://localhost:5173
```

To stop:

```bash
./down.sh
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Lexical search | rank-bm25 (BM25Okapi) |
| Semantic search | sentence-transformers `BAAI/bge-small-en-v1.5` · 384-dim · asymmetric retrieval |
| Vector index | faiss-cpu · IndexFlatIP + L2-normalize → cosine similarity |
| Hybrid scoring | configurable alpha · min-max or z-score normalization |
| Storage | SQLite (query logs) · local filesystem (indexes) |
| Frontend | React 18 · Vite 5 · Recharts |
| Testing | pytest · FastAPI TestClient |
| Rate limiting | slowapi · 30 req/min on POST /search |

---

## Hybrid Scoring

```
hybrid = alpha · minmax(bm25_scores) + (1 - alpha) · minmax(vector_scores)

alpha = 1.0  →  pure BM25   (keyword match dominates)
alpha = 0.0  →  pure vector  (semantic similarity dominates)
alpha = 0.3  →  best nDCG@10 on this corpus (leans semantic)
```

Two normalization strategies available: `minmax` (default) and `zscore`.
Comparison and rationale in [`docs/decision_log.md`](docs/decision_log.md).

---

## Evaluation

```bash
cd backend

# Single run
python -m app.eval \
  --queries data/eval/queries.jsonl \
  --qrels   data/eval/qrels.json \
  --alpha   0.3 \
  --normalization minmax

# Reproduce all 5 experiments
for alpha in 0.5 0.5 0.3 0.7 0.9; do
  python -m app.eval --queries data/eval/queries.jsonl \
    --qrels data/eval/qrels.json --alpha $alpha --normalization minmax
done
```

Results append to `data/metrics/experiments.csv`. Visualised on the Eval page.

**Best result:** alpha=0.3 · minmax → nDCG@10=0.8657 · Recall@10=0.9000 · MRR@10=0.8600

---

## Tests

```bash
cd backend
python -m pytest tests/ -v
# 76 tests · 0 failures
```

---

## CLI Reference

```bash
# Rebuild corpus index from scratch
python -m app.ingest --input data/raw --out data/processed
python -m app.index  --input data/processed/docs.jsonl

# Start backend only
cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

---

## Dataset

400 arXiv CS paper abstracts from `gfissore/arxiv-abstracts-2021` (HuggingFace · CC BY).
Committed to `data/raw/` — no download required at run time.

| Category | Papers | Domain |
|---|---|---|
| cs.LG | 80 | Machine Learning |
| cs.CL | 80 | Natural Language Processing |
| cs.CV | 80 | Computer Vision |
| cs.AI | 80 | Artificial Intelligence |
| cs.IR | 80 | Information Retrieval |

---

## Docs

| File | Contents |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Full system diagram · SQLite schema · metadata format |
| [`docs/decision_log.md`](docs/decision_log.md) | Every design decision with rationale (D01–D25) |
| [`docs/codex_log.md`](docs/codex_log.md) | Granular AI prompt log · one entry per commit |
| [`docs/break_fix_log.md`](docs/break_fix_log.md) | 3 induced failure scenarios · root cause · fix |
