# Break/Fix Log

Three intentional failure scenarios injected, diagnosed, and fixed to demonstrate
production-grade defensive engineering. Each scenario targets a real failure mode
in ML retrieval systems.

---

## Scenario A — Embedding Model Mismatch

### What was injected
In `backend/app/search/vector.py`, `MODEL_NAME` was changed from
`"BAAI/bge-small-en-v1.5"` to `"paraphrase-MiniLM-L3-v2"` without rebuilding
the FAISS index. The FAISS index on disk was built with BGE vectors.

**Git commit (break):** `40e4aa9` — `break(A): inject wrong embedding model`

### What broke
On server startup, `validate_metadata()` reads `data/index/vector/metadata.json`,
which records the model used at index build time (`BAAI/bge-small-en-v1.5`, 384-dim).
It compares this against the current `MODEL_NAME` constant in `vector.py`. Mismatch
detected → server raises `ValueError` and refuses to start:

```
ValueError: Index built with BAAI/bge-small-en-v1.5 (384-dim).
Current model is paraphrase-MiniLM-L3-v2 (384-dim).
Rebuild with: python -m app.index
```

The server never reaches the `yield` in the lifespan context — no traffic is served
with a mismatched index. The error appears in the uvicorn startup log.

### How it was fixed
Restored `MODEL_NAME = "BAAI/bge-small-en-v1.5"` in `vector.py`.

**Git commit (fix):** `83f75bd` — `fix(A): restore correct model name`

### Why this matters
In production ML systems, the serving code and the stored model artifact can drift
independently (e.g., a developer bumps a constant without triggering a re-index).
The `validate_metadata()` pattern — fail fast at startup with a clear rebuild
instruction — prevents silent degradation where queries return wrong-dimension
vectors and scores silently become garbage.

---

## Scenario B — Schema Migration Bug

### What was injected
In `backend/app/db/schema.py`, the `check_and_migrate()` function's `ALTER TABLE`
statement was changed from `ADD COLUMN alpha REAL DEFAULT 0.5` to
`ADD COLUMN alpha REAL NOT NULL` (no default value).

**Git commit (break + fix):** `85ec9e3` — `break+fix(B): schema migration`

### What broke
SQLite enforces that `ALTER TABLE ADD COLUMN` with `NOT NULL` requires a `DEFAULT`
value — it cannot backfill existing rows otherwise. On startup with a fresh database:

1. `init_db()` creates `query_logs` with the v1 schema (no `alpha` column)
2. `check_and_migrate()` detects `schema_version = 1` and runs the migration
3. `ALTER TABLE query_logs ADD COLUMN alpha REAL NOT NULL` → SQLite raises:
   `OperationalError: Cannot add a NOT NULL column with default value NULL`
4. Lifespan crashes before `yield` — server never starts

To reproduce: delete `data/search.db` (simulates a fresh clone where no database
exists), then start the server with the broken migration.

### How it was fixed
Changed `NOT NULL` back to `DEFAULT 0.5`:

```python
conn.execute("ALTER TABLE query_logs ADD COLUMN alpha REAL DEFAULT 0.5")
```

`DEFAULT 0.5` satisfies SQLite's requirement and backfills all existing rows.
The `schema_version` table ensures this migration runs exactly once — subsequent
startups see `version = 2` and skip the `ALTER TABLE`.

### Why this matters
Schema migrations without data loss are a core operational challenge. The
`schema_version` gate prevents double-migration. The `DEFAULT` requirement is a
SQLite-specific constraint (PostgreSQL handles this differently) — knowing the
difference matters when building portable database code.

---

## Scenario C — Normalization Divide-by-Zero

### What was injected
In `backend/app/search/hybrid.py`, the `max == min` guard was removed from
`minmax_normalize()`:

```python
# REMOVED:
if max_s == min_s:
    return [0.5] * len(scores)
```

**Git commit (break + fix):** `ef5e6c8` — `break+fix(C): divide-by-zero guard`

### What broke
When a query has no BM25 keyword overlap with any document (pure semantic query —
e.g., a long paraphrase with no shared tokens), all BM25 raw scores are `0.0`.
`minmax_normalize([0.0, 0.0, ..., 0.0])` then computes:

```python
span = max_s - min_s  # = 0.0 - 0.0 = 0.0
return [(s - min_s) / span for s in scores]  # ZeroDivisionError
```

The exception propagates through `HybridSearch.search()` → the `/search` endpoint
returns HTTP 500. During eval, this causes all nDCG/Recall/MRR metrics to collapse
to `NaN` across every query that hits this path.

### How it was fixed
Restored the guard with a clear explanation of why it must not be removed:

```python
if max_s == min_s:  # divide-by-zero guard — do not remove
    return [0.5] * len(scores)
```

Returns `0.5` (neutral score) for all candidates when all scores are equal — a
graceful fallback that lets vector scores dominate the hybrid blend instead of
crashing.

### Regression test
`test_hybrid.py::TestHybridNormalization::test_minmax_nan_guard` covers both
the all-ones and all-zeros cases, permanently locking this fix:

```python
assert minmax_normalize([1.0, 1.0, 1.0]) == [0.5, 0.5, 0.5]
assert minmax_normalize([0.0, 0.0, 0.0]) == [0.5, 0.5, 0.5]
```

### Why this matters
Normalization edge cases in retrieval systems are subtle — they only surface on
specific query patterns (pure semantic queries with no lexical overlap), making
them hard to catch in basic testing. Writing the regression test before the fix
is merged ensures this path can never silently regress.
