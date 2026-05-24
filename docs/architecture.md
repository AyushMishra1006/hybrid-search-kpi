# Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         hybrid-search-kpi                            │
│                                                                      │
│   data/raw/*.txt (400 articles, committed)                           │
│        │                                                             │
│        ▼  python -m app.ingest                                       │
│   data/processed/docs.jsonl  ──────────────────────────────────┐    │
│        │                                                        │    │
│        ▼  python -m app.index                                   │    │
│   ┌────────────┐    ┌─────────────────┐                        │    │
│   │  BM25 idx  │    │   Vector idx    │                        │    │
│   │ (joblib)   │    │ (FAISS+metadata)│                        │    │
│   └─────┬──────┘    └────────┬────────┘                        │    │
│         │                    │                                  │    │
│         └─────────┬──────────┘                                  │    │
│                   ▼                                             │    │
│           HybridSearch.search()                                 │    │
│           alpha*norm_bm25 + (1-alpha)*norm_vector               │    │
│                   │                                             │    │
│                   ▼                                             │    │
│           FastAPI (uvicorn :8000)                               │    │
│           ├── GET  /health                                      │    │
│           ├── POST /search  ←── rate limit 30/min              │    │
│           ├── POST /feedback                                    │    │
│           ├── GET  /metrics (Prometheus plain text)             │    │
│           ├── GET  /dashboard/kpi                               │    │
│           ├── GET  /dashboard/logs                              │    │
│           └── GET  /dashboard/experiments                       │    │
│                   │                              ◄──────────────┘    │
│                   ▼                                                  │
│           data/search.db (SQLite)                                    │
│           data/metrics/experiments.csv                               │
│                   │                                                  │
│                   ▼                                                  │
│           React + Vite (Vite dev :5173)                              │
│           ├── SearchPage   — query box + alpha slider + score bars   │
│           ├── KPIPage      — latency cards + volume chart            │
│           ├── EvalPage     — experiments table + nDCG trend          │
│           └── DebugPage    — log table (filter by time + severity)   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

1. **Ingest** — `python -m app.ingest --input data/raw --out data/processed`
   - Globs `*.txt` and `*.md` from `data/raw/`
   - Parses `TITLE:` line → `title`; rest → `text`
   - Calls `clean_text()` + `truncate_long_doc(MAX_DOC_WORDS=256)`
   - Assigns `category` from title keywords (`assign_category()`)
   - Writes one JSON line per doc to `data/processed/docs.jsonl`:
     `{doc_id, title, text, source, created_at, category}`

2. **Index** — `python -m app.index --input data/processed/docs.jsonl`
   - BM25: tokenizes `title + text`, fits `BM25Okapi`, serializes with `joblib`
   - Vector: encodes `title + text` with `all-MiniLM-L6-v2` (384-dim), L2-normalizes,
     stores in `faiss.IndexFlatIP`, writes `metadata.json`

3. **API Startup** (FastAPI lifespan)
   - `VectorIndex.validate_metadata()` — checks model/dim against `metadata.json`
   - Loads BM25 + FAISS indexes into memory
   - Loads `docs.jsonl` into doc_store dict
   - `init_db()` + `check_and_migrate()` — creates/upgrades SQLite schema

4. **Search Request**
   - POST `/search {query, top_k, alpha, filters}`
   - BM25.query(top_k×3) + VectorIndex.query(top_k×3) → union
   - min-max normalize each score list → fuse with alpha weight
   - Post-filter by `filters` dict → sort → return top_k with 3 scores + snippet
   - Structured JSON log to stdout + INSERT into `query_logs`

5. **Evaluation** — `python -m app.eval --queries ... --qrels ... --alpha 0.5 --normalization minmax`
   - Runs HybridSearch directly (no HTTP) for 25 queries
   - Computes nDCG@10, Recall@10, MRR@10
   - Appends one row to `data/metrics/experiments.csv`

---

## SQLite Schema

### v1 (initial — created by `init_db()`)

```sql
CREATE TABLE IF NOT EXISTS query_logs (
    id           TEXT PRIMARY KEY,
    timestamp    TEXT NOT NULL,
    query        TEXT NOT NULL,
    latency_ms   REAL NOT NULL,
    top_k        INTEGER NOT NULL,
    result_count INTEGER NOT NULL,
    severity     TEXT NOT NULL DEFAULT 'info',
    error        TEXT
);

CREATE TABLE IF NOT EXISTS relevance_feedback (
    id        TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    query     TEXT NOT NULL,
    doc_id    TEXT NOT NULL,
    relevant  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
-- Seeded: INSERT INTO schema_version VALUES (1, '<timestamp>');
```

### v2 (Scenario B migration — added by `check_and_migrate()`)

```sql
ALTER TABLE query_logs ADD COLUMN alpha REAL DEFAULT 0.5;
-- Then: INSERT INTO schema_version VALUES (2, '<timestamp>');
```

The `alpha` column is added without data loss (DEFAULT 0.5 backfills existing rows).
Every subsequent INSERT includes alpha explicitly.

---

## Vector Index Metadata (`data/index/vector/metadata.json`)

```json
{
  "model_name": "all-MiniLM-L6-v2",
  "dimension": 384,
  "corpus_hash": "<sha256 of docs.jsonl>",
  "build_timestamp": "<ISO 8601>",
  "num_docs": 400
}
```

`validate_metadata()` compares `model_name` and `dimension` against module constants on startup.
Mismatch → `ValueError` with rebuild instruction (Scenario A break/fix).

---

## Hybrid Scoring Formula

```
hybrid_score = alpha × minmax(bm25_score) + (1 − alpha) × minmax(vector_score)
```

- `alpha = 1.0` → pure BM25 (keyword)
- `alpha = 0.0` → pure vector (semantic)
- `alpha = 0.5` → equal blend (default)

Guard: if all scores are equal → normalize to `[0.5, 0.5, ...]` (prevents ZeroDivisionError — Scenario C).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| API | FastAPI + Uvicorn |
| BM25 | rank-bm25 (BM25Okapi) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384-dim, CPU) |
| Vector index | faiss-cpu `IndexFlatIP` + L2-normalize = cosine similarity |
| Index persistence | joblib (BM25), FAISS binary + JSON (vector) |
| Database | SQLite (WAL mode) |
| Rate limiting | slowapi (30 req/min on /search) |
| Frontend | React + Vite |
| Tests | pytest + FastAPI TestClient |
| Packaging | requirements.txt + up.sh (bash/WSL) |
