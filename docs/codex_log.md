# Codex Log

Granular log of every AI-assisted prompt used in this project. One entry per commit.
Each prompt targets a single file/function/test — no blanket prompts.

---

## Commit 1 — `init: project structure, requirements.txt, README skeleton`

**Prompt:**
> Create the folder structure for a hybrid-search-kpi project under `hybrid-search-kpi/`. Required directories: backend/app/search/, backend/app/api/, backend/app/db/, backend/app/utils/, backend/tests/, frontend/src/pages/, data/raw/, data/processed/, data/index/bm25/, data/index/vector/, data/eval/, data/metrics/, docs/. Create empty `__init__.py` in each Python package. Write `requirements.txt` with pinned versions for: fastapi, uvicorn, rank-bm25, sentence-transformers, faiss-cpu, joblib, slowapi, datasets, pytest, httpx, numpy, torch (CPU). Write `.gitignore` for Python + Node. Write README.md skeleton with architecture diagram, 1-minute quickstart, test/eval commands, tech stack table. CPU-only constraint throughout.

**Output used:** Full folder structure, requirements.txt pinned versions, README skeleton structure.

**Edits made:**
- Verified torch version is CPU-only (`torch==2.5.1+cpu`)
- Added `python-multipart` to requirements (FastAPI form parsing dependency)
- Added `python-dotenv` for env var loading
- Confirmed `.gitignore` excludes `data/index/` and `data/processed/` (rebuilt by up.sh) but keeps `data/raw/` and `data/eval/` (committed to repo)

**Document section satisfied:** Section 7 (README, requirements.txt), Section 3 (no hard-coded paths, reproducibility)

---

## Commit 2 — `feat: Wikipedia download script → data/raw/`

*(fill when committed)*

---

## Commit 3 — `feat: data ingestion pipeline → data/processed/docs.jsonl`

*(fill when committed)*

---

## Commit 4 — `feat: BM25 index builder with joblib persistence`

*(fill when committed)*

---

## Commit 5 — `test: BM25 unit tests — 3-doc toy corpus, deterministic ordering`

*(fill when committed)*

---

## Commit 6 — `feat: vector index builder — sentence-transformers + FAISS CPU + metadata.json`

*(fill when committed)*

---

## Commit 7 — `test: vector index unit tests — encode + query + nearest neighbor check`

*(fill when committed)*

---

## Commit 8 — `feat: hybrid search — min-max + z-score normalization, alpha weighting`

*(fill when committed)*

---

## Commit 9 — `test: hybrid unit tests — alpha extremes, normalization math, NaN guard`

*(fill when committed)*

---

## Commit 10 — `feat: FastAPI app — /health /search /metrics /feedback endpoints`

*(fill when committed)*

---

## Commit 11 — `test: API contract tests — TestClient, verify score breakdown in response`

*(fill when committed)*

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
