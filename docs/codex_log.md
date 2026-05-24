# Codex Log

Granular log of every AI-assisted prompt used in this project. One entry per commit.
Each prompt targets a single file/function/test — no blanket prompts.

---

## Commit 1 — `init: project structure, requirements.txt, README skeleton`

**Prompt:**
> Create the folder structure for a hybrid-search-kpi project. Required directories: backend/app/search/, backend/app/api/, backend/app/db/, backend/app/utils/, backend/tests/, frontend/src/pages/, data/raw/, data/processed/, data/index/bm25/, data/index/vector/, data/eval/, data/metrics/, docs/. Create empty `__init__.py` in each Python package. Write `requirements.txt` with pinned versions for: fastapi, uvicorn, rank-bm25, sentence-transformers, faiss-cpu, joblib, slowapi, datasets, pytest, httpx, numpy, torch (CPU-only). Write `.gitignore` for Python + Node. Write README.md skeleton with architecture diagram, 1-minute quickstart, test/eval commands, tech stack table.

**Output used:** Full folder structure, requirements.txt pinned versions, README skeleton structure, decision_log.md seeded with D01–D20, codex_log.md with commit stubs.

**Edits made:**
- Added `python-multipart` to requirements (FastAPI form parsing)
- Added `python-dotenv` for env var loading
- `.gitignore` verified: excludes data/index/ + data/processed/ (rebuilt by up.sh), keeps data/raw/ + data/eval/ (committed corpus)

**Document section satisfied:** Section 7 (README + requirements.txt), Section 3 (reproducibility, no hard-coded paths)

---

## Commit 2 — `feat: Wikipedia download script → data/raw/`

**Prompt:**
> In `backend/app/download_data.py`, write a script that downloads exactly 400 Simple English Wikipedia science/tech articles from HuggingFace `datasets` (`20220301.simple`). Requirements: (1) write each article as `doc_NNN.txt` with format "TITLE: <title>\n<text body>"; (2) filter for science/tech articles using title+text keywords; (3) assign a category (computer_science/physics/biology/mathematics/chemistry/general_science) from title keywords; (4) write manifest.json; (5) be idempotent — skip entirely if ≥400 doc_*.txt files exist; (6) CPU-only, no hard-coded paths, use `Path(__file__).parent` for RAW_DIR.

**Output used:** Full download_data.py with _is_science_tech(), _write_article(), download(), CORPUS_SIZE=400, fallback loop.

**Edits made:**
- Removed CATEGORY_RULES and assign_category from this file — moved to preprocessing.py (DRY). Now imports `assign_category` from `app.utils.preprocessing`.
- Fixed _write_article() to write `TITLE: <title>\n<text>` only (no CATEGORY: line in .txt — spec says line 1 = TITLE, lines 2+ = body).

**Document section satisfied:** Section 6.1 (300+ docs, open license CC BY-SA, idempotent download)

---

## Commit 3 — `feat: data ingestion pipeline → data/processed/docs.jsonl`

**Prompt:**
> In `backend/app/utils/preprocessing.py`, write: (1) `MAX_DOC_WORDS = 256` module constant; (2) `clean_text(text: str) -> str` — collapses whitespace; (3) `truncate_long_doc(text: str, max_words: int = MAX_DOC_WORDS) -> str` — hard cap at max_words; (4) `highlight_snippet(text: str, query: str, context_words: int = 20) -> str` — wraps query tokens in `<em>`; (5) `assign_category(title: str) -> str` — maps title to 6 categories. Type hints on all signatures. No global mutable state.

**Output used:** Full preprocessing.py with all 5 functions + CATEGORY_RULES constant.

> In `backend/app/ingest.py`, write the ingestion pipeline: globs `*.txt` AND `*.md` from --input, parses TITLE: from line 1, body from lines 2+, calls clean_text→truncate_long_doc→assign_category, writes one JSON line per doc to docs.jsonl: {doc_id, title, text, source, created_at, category}. CLI: `python -m app.ingest --input data/raw --out data/processed`.

**Output used:** Full ingest.py with _parse_file(), _make_doc_id(), ingest(), main().

**Edits made:**
- Confirmed source = "simple_wikipedia" and created_at = "2022-03-01" are module-level constants (not inline strings)
- Verified _parse_file() returns None for malformed files (no crash on bad input)

**Document section satisfied:** Section 6.1 (python -m app.ingest CLI, JSONL with all required fields, preprocessing safeguards)

---

## Commit 4 — `feat: BM25 index builder with joblib persistence`

**Prompt:**
> In `backend/app/search/bm25.py`, implement `BM25Index` class using `rank-bm25` (BM25Okapi). Methods: `build(docs: list[str], doc_ids: list[str]) -> None` — tokenizes on whitespace, fits BM25Okapi; `query(q: str, top_k: int) -> list[tuple[str, float]]` — returns (doc_id, score) descending; `save(path: Path) -> None` — joblib.dump to path/bm25_index.pkl; `load(path: Path) -> None` — joblib.load. Type hints required. No global mutable state. `INDEX_FILENAME = "bm25_index.pkl"` as module constant. Raise RuntimeError if query() called before build(). Raise ValueError if len(docs) != len(doc_ids).

**Output used:** Full BM25Index class as specified.

**Edits made:** None — output matched spec exactly.

**Document section satisfied:** Section 6.2 (BM25 index, artifacts under data/index/bm25/)

---

## Commit 5 — `test: BM25 unit tests — 3-doc toy corpus, deterministic ordering`

**Prompt:**
> In `backend/tests/test_bm25.py`, write pytest tests for BM25Index using a 3-doc toy corpus: ["machine learning is a subset of artificial intelligence", "deep learning uses neural networks with many layers", "natural language processing handles text and speech"]. Tests: (1) build: num_docs=3, mismatched lengths raise ValueError, query-before-build raises RuntimeError; (2) query: top result for "machine learning" is doc_001, top result for "natural language text" is doc_003, scores descending, blank query returns [], top_k>corpus gracefully handled; (3) persistence: save/load round-trip returns identical results.

> In `backend/tests/test_preprocessing.py`, write pytest tests for all 5 functions in preprocessing.py: clean_text (3 cases), truncate_long_doc (4 cases including MAX_DOC_WORDS constant), highlight_snippet (4 cases), assign_category (6 categories + fallback).

**Output used:** Both test files as specified.

**Edits made:** None — all 27 tests passed on first run.

**Document section satisfied:** Section 6.6 (unit tests for preprocessing, BM25 scoring)

---

## Commit 6 — `feat: vector index builder — sentence-transformers + FAISS CPU + metadata.json`

**Prompt:**
> In `backend/app/search/vector.py`, implement `VectorIndex` class. Constants: `MODEL_NAME = "all-MiniLM-L6-v2"`, `DIMENSION = 384`. Methods: `build(docs, doc_ids)` — encodes with sentence-transformers, L2-normalize, `faiss.IndexFlatIP`; `query(q, top_k)` — encodes query, FAISS search → [(doc_id, cosine_score)]; `save(path, corpus_hash)` — faiss.write_index + doc_ids.json + metadata.json {model_name, dimension, corpus_hash, build_timestamp, num_docs}; `load(path)` — faiss.read_index + doc_ids.json; `validate_metadata(path)` — static method, reads metadata.json, raises ValueError if model_name or dimension don't match current constants (message must include "Rebuild with: python -m app.index"). CPU-only — no .to(device) or device='cuda'. Lazy model loading.

**Output used:** Full VectorIndex class + compute_corpus_hash() helper.

**Edits made:**
- Confirmed `normalize_embeddings=True` in model.encode() (L2-normalize in one call, not separate step)
- Added `convert_to_numpy=True` for guaranteed ndarray output to FAISS

**Document section satisfied:** Section 6.2 (vector index, startup metadata validation, Scenario A break/fix groundwork)

---

## Commit 7 — `test: vector index unit tests — encode + query + nearest neighbor check`

**Prompt:**
> In `backend/tests/test_vector.py`, write pytest tests for VectorIndex. Use scope="module" fixture to avoid re-encoding. 3-doc corpus: ML doc, photosynthesis doc, French Revolution doc (deliberately diverse topics for semantic separation). Tests: (1) build: num_docs, length guard, build-before-query guard; (2) query: nearest-neighbor for "supervised learning algorithm" → doc_001, "chlorophyll and sunlight" → doc_002, scores descending, top_k respected, cosine range [-1,1]; (3) persistence: save/load round-trip, metadata.json has all required fields; (4) validate_metadata: valid passes, wrong model raises ValueError with "Rebuild", missing file raises FileNotFoundError.

**Output used:** Full test_vector.py.

**Edits made:** None — all 13 tests passed on first run.

**Document section satisfied:** Section 6.6 (unit tests for vector search), Section 9.1 (Scenario A groundwork)

---

## Commit 8 — `feat: hybrid search — min-max + z-score normalization, alpha weighting`

**Prompt:**
> In `backend/app/search/hybrid.py`, implement: (1) `minmax_normalize(scores: list[float]) -> list[float]` — scales to [0,1], guard: max==min → [0.5]*len (prevents Scenario C divide-by-zero); (2) `zscore_normalize(scores: list[float]) -> list[float]` — z-score, guard: std==0 → [0.5]*len; (3) `SearchResult` dataclass with fields: doc_id, title, snippet, bm25_score, vector_score, hybrid_score; (4) `HybridSearch` class with `search(query, top_k, alpha, filters, normalization)` — retrieves top_k*3 from each index, unions doc_ids, fills missing scores with 0.0, normalizes both score lists, computes hybrid=alpha*norm_bm25+(1-alpha)*norm_vector, post-filters on doc metadata, sorts descending, returns top_k SearchResults with highlight_snippet. Import BM25Index, VectorIndex, highlight_snippet. No global state.

**Output used:** Full hybrid.py with all components.

**Edits made:**
- `candidate_k = max(top_k * 3, 30)` ensures minimum 30 candidates even for top_k=1
- `round(..., 6)` on all 3 scores for clean JSON output
- filters default to `{}` not `None` in dataclass to match Pydantic model default

**Document section satisfied:** Section 6.3 (hybrid scoring explicit, alpha configurable, 2 normalization strategies, score breakdown)

---

## Commit 9 — `test: hybrid unit tests — alpha extremes, normalization math, NaN guard`

**Prompt:**
> In `backend/tests/test_hybrid.py`, write pytest tests for HybridSearch using a 5-doc corpus (ML, photosynthesis, quantum physics, neural networks, DNA) with category field for filter testing. Tests: (1) alpha=1.0 → hybrid_score == bm25_score; (2) alpha=0.0 → hybrid_score == vector_score; (3) alpha=0.5 → hybrid is average; (4) minmax output in [0,1], math [0.0, 0.5, 1.0] correct, NaN guard [1.0,1.0,1.0]→[0.5,0.5,0.5] (Scenario C regression), single-element; (5) zscore zero-mean, std=0 guard, sign test; (6) category filter restricts results, empty filter passes all, nonexistent filter returns []; (7) SearchResult fields present, top_k respected, scores descending.

**Output used:** Full test_hybrid.py.

**Edits made:** None — all 16 tests passed on first run.

**Document section satisfied:** Section 6.3, Section 6.6 (hybrid combination tests), Section 9.3 (Scenario C regression test)

---

## Commit 10 — `feat: FastAPI app — /health /search /metrics /feedback endpoints`

**Prompt:**
> In `backend/app/api/limiter.py`, create a single shared `Limiter` instance using slowapi with `get_remote_address` key function.
> In `backend/app/db/schema.py`, implement `init_db(db_path) -> sqlite3.Connection` (creates query_logs v1 + relevance_feedback + schema_version tables, seeds version=1) and `check_and_migrate(conn)` (v1→v2: ALTER TABLE adds alpha REAL DEFAULT 0.5, inserts version=2). WAL mode, row_factory=sqlite3.Row.
> In `backend/app/db/logger.py`, implement `log_query(conn, req_id, timestamp, query, latency_ms, top_k, alpha, result_count, severity, error)` and `log_feedback(conn, ...)` using INSERT OR IGNORE.
> In `backend/app/api/routes.py`, implement all endpoints with Pydantic models. SearchRequest: query(min=1,max=1000), top_k(1-50), alpha(0.0-1.0), filters(dict). Endpoints: GET /health → {status,version,commit}; POST /search (rate-limited 30/min) → {results:[{doc_id,title,snippet,bm25_score,vector_score,hybrid_score}], query,latency_ms,result_count,filters_applied}; POST /feedback → 204; GET /metrics → Prometheus plain text; GET /dashboard/kpi → {latency_p50_ms,latency_p95_ms,request_volume,top_queries,zero_result_queries}; GET /dashboard/logs (query params: since,until,severity); GET /dashboard/experiments (reads experiments.csv). Each /search call: structured stdout JSON log + SQLite INSERT. Helpers: _percentile(), _emit_stdout_log(), _fetch_latencies(), _fetch_request_volume(), _fetch_top_queries(), _fetch_zero_result_queries(), _read_experiments(). All functions ≤ 40 lines, type hints on all signatures.
> In `backend/app/api/main.py`, create FastAPI app with lifespan context: (1) VectorIndex.validate_metadata (Scenario A), (2) BM25Index.load, (3) VectorIndex.load, (4) _load_doc_store from docs.jsonl, (5) init_db + check_and_migrate (Scenario B), (6) HybridSearch wired into app.state. CORS allow_origins=*, slowapi rate limiter exception handler, include router from routes.py.

**Output used:** All 5 files as described.

**Edits made:**
- DB layer (schema.py + logger.py) included in Commit 10 rather than deferred to Commit 12, because routes.py imports from db.logger — they are tightly coupled and separating would require stub placeholders. Commit 12 repurposed to docs/architecture.md.
- `_emit_stdout_log` writes to sys.stdout with flush=True so logs appear in real-time during screen recording.
- Used `INSERT OR IGNORE` on req_id (UUID primary key) so duplicate events on retry never corrupt the log.
- `_REPO_ROOT = Path(__file__).resolve().parents[3]` — goes up 3 levels from app/api/ to repo root; no hard-coded absolute paths.
- Added `_NOW = lambda` at module level in schema.py and routes.py as a DRY timestamp helper.
- `candidate_k = max(top_k * 3, 30)` already in HybridSearch — no change needed in routes.

**Document section satisfied:** Section 6.3 (all endpoints, hybrid scoring, rate limiting, input validation), Section 6.6 (structured logs, SQLite persistence, input validation), Section 9.2 (Scenario B check_and_migrate groundwork)

---

## Commit 11 — `test: API contract tests — TestClient, verify score breakdown in response`

**Prompt:**
> In `backend/tests/test_api.py`, write pytest contract tests for all API endpoints using FastAPI TestClient. Use a module-scoped fixture that: (1) builds a 5-doc toy BM25 + FAISS index in a tmp_path_factory temp dir; (2) writes docs.jsonl for those 5 docs; (3) patches the module-level path constants in app.api.main (_BM25_DIR, _VECTOR_DIR, _DOCS_JSONL, _DB_PATH) before the TestClient starts (which triggers lifespan). Tests: /health: 200, required fields {status,version,commit}, status=="OK". /search: 200, top-level fields {results,query,latency_ms,result_count,filters_applied}, each result has {bm25_score,vector_score,hybrid_score,doc_id,title,snippet}, result_count==len(results), query echoed, filters_applied echoed, top_k respected, latency_ms positive float, validation: empty query→422, top_k=0→422, top_k=51→422, alpha=1.5→422, alpha=1.0 works, alpha=0.0 works. /feedback: 204. /metrics: 200, content-type=text/plain, all 5 counter names present. /dashboard/kpi: required fields present. /dashboard/logs: returns list, severity filter accepted. /dashboard/experiments: returns list.

**Output used:** Full test_api.py with 26 tests across 5 test classes.

**Edits made:** None — all 26 tests passed on first run.

**Document section satisfied:** Section 6.6 (unit tests for API contracts), Section 13 (reviewer checklist: /health and /search verified, score breakdown confirmed)

---

## Commit 12 — `feat: SQLite schema v1 + structured JSON logging per request`

*(fill when committed)*

---

## Commit 13 — `feat: eval harness + 25 labeled queries + qrels`

*(fill when committed)*

---

## Commit 14 — `feat: React frontend — Search page + KPI page`

*(fill when committed)*

---

## Commit 15 — `feat: React frontend — Evaluation page + Debug page`

*(fill when committed)*

---

## Commit 16 — `feat: up.sh + down.sh — one-command boot, idempotent`

*(fill when committed)*

---

## Commit 17 — `break(A): inject embedding model mismatch — no index rebuild`

*(fill when committed)*

---

## Commit 18 — `fix(A): startup validation — check metadata.json dimension vs current model`

*(fill when committed)*

---

## Commit 19 — `break(B): add NOT NULL alpha column without migration`

*(fill when committed)*

---

## Commit 20 — `fix(B): schema migration v1→v2 — ALTER TABLE with DEFAULT on startup`

*(fill when committed)*

---

## Commit 21 — `fix(C): add divide-by-zero guard + regression test — eval metrics recover`

*(fill when committed)*
