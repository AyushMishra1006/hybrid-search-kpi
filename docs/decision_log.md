# Decision Log

## D01 — Dataset: Simple English Wikipedia
**Decision:** Use Simple English Wikipedia (`20220301.simple` via HuggingFace `datasets`), science/tech articles, exactly 400 articles committed to repo.
**Why:** Open license (CC BY-SA), CPU-friendly size, short clean articles (avg 150–350 words), title = topic (reliable for qrel labeling), fully reproducible.
**Rejected:** SciFact (BEIR) — only 1–3 relevant docs/query. MS MARCO — passage-level not document-level.
**Document section:** 6.1 (300+ docs, open license)

## D02 — Corpus Selection: 400 Files Committed to Repo
**Decision:** The 400 Wikipedia .txt files are committed directly to `data/raw/`. `download_data.py` runs only if `data/raw/` is empty. `up.sh` checks for existing files before downloading.
**Why:** Deterministic corpus — same 400 articles on every clone. qrels permanently valid. No internet dependency. Satisfies ≤30 min reviewer reproduction constraint.
**Document section:** 3 (≤30 min reproduction), 6.1 (300+ docs)

## D03 — Raw File Format
**Decision:** Each article saved as `doc_NNN.txt`. Line 1 = `TITLE: <title>`. Lines 2+ = full text body.
**Why:** Self-contained format — ingest.py needs only the .txt to extract title and text.
**Document section:** 6.1

## D04 — Ingest Handles .txt and .md
**Decision:** `ingest.py` globs for both `*.txt` and `*.md` in data/raw/.
**Why:** Assignment Section 6.1 explicitly requires "folder of .txt/.md". Single combined glob handles both.
**Document section:** 6.1

## D05 — Embedding Model: all-MiniLM-L6-v2
**Decision:** `sentence-transformers/all-MiniLM-L6-v2`, 384-dimensional vectors.
**Why:** CPU-friendly (~80MB), fast encode, good quality for general text, standard benchmark model.
**Document section:** 6.2 (small sentence-transformers model, CPU)

## D06 — Vector Index: FAISS CPU IndexFlatIP
**Decision:** `faiss-cpu`, `IndexFlatIP` with L2-normalized vectors = cosine similarity.
**Why:** Exact search correct at 400 docs. No approximation needed.
**Document section:** 6.2 (FAISS CPU)

## D07 — Indexed Content: title + text for Both BM25 and Vector
**Decision:** Both BM25 and vector receive `title + " " + text` as the document string.
**Why:** Document Section 6.2 explicitly requires BM25 over (title + text). Vector uses same for consistency — richer semantic content than title alone.
**Document section:** 6.2

## D08 — Truncation: MAX_DOC_WORDS = 256
**Decision:** `preprocessing.py` constant `MAX_DOC_WORDS = 256`. `truncate_long_doc()` caps all text before indexing.
**Why:** BM25 has no limit but long docs skew scoring. `all-MiniLM-L6-v2` has 256-token internal limit. 256 words ≈ model limit. Simple English Wikipedia avg 150–350 words — safeguard for edge cases.
**Document section:** 6.1 (safeguards for extremely long docs)

## D09 — Normalization: Two Strategies, Winner Empirically Chosen
**Decision:** Implement min-max and z-score. Winner decided by nDCG@10: Exp 1 (α=0.5, minmax) vs Exp 2 (α=0.5, zscore).
**Why:** Document requires ≥2 strategies and justification in this file. Actual nDCG numbers are the strongest justification.
**Theoretical note:** Min-max → bounded [0,1], intuitive with α weighting. Z-score → can go negative, harder to mix with α.
**Scenario C guard:** if max == min → return [0.5]*len to prevent divide-by-zero.
**Winner (fill after experiments):** TBD — see experiments.csv row 1 vs row 2.
**Document section:** 6.3

## D10 — BM25: rank-bm25, BM25Okapi
**Decision:** `rank-bm25` library, `BM25Okapi` class.
**Why:** Assignment tech stack specification.
**Document section:** 5

## D11 — Index Persistence
**Decision:** BM25 → `joblib.dump()` → `data/index/bm25/bm25_index.pkl`. FAISS → `faiss.write_index()` → `data/index/vector/faiss.index`. Metadata → `data/index/vector/metadata.json`.
**Why:** joblib = standard Python object serialization. FAISS native format = efficient binary. Metadata as JSON = human-readable, validatable.
**Document section:** 6.2

## D12 — SQLite Migrations: Manual via schema_version Table
**Decision:** Manual migration, no Alembic. `schema_version` table tracks current version. `check_and_migrate()` on startup runs ALTER TABLE if version=1.
**Why:** Assignment says "Alembic optional." Manual approach is simpler, no extra dependency, cleanly demonstrates v1→v2 concept.
**Document section:** 9.2

## D13 — 5 Experiments: Alpha + Normalization Comparison
**Decision:**
| Run | Alpha | Normalization | Purpose |
|-----|-------|--------------|---------|
| 1 | 0.5 | minmax | Baseline + normalization comparison |
| 2 | 0.5 | zscore | Direct normalization comparison (same α) |
| 3 | 0.3 | minmax (winner) | Lean semantic |
| 4 | 0.7 | minmax (winner) | Lean keyword |
| 5 | 0.9 | minmax (winner) | Heavy keyword |
**Why:** Exp 1 vs 2 answers "which normalization is better?" at fixed α. Exp 3–5 show α sensitivity with winning normalization.
**Document section:** 6.5 (≥5 experiments)

## D14 — Frontend: React + Vite, 4 Pages
**Decision:** React + Vite, pages: Search, KPI, Eval, Debug.
**Why:** Assignment explicitly prefers React + Vite over Streamlit.
**Document section:** 5, 6.4

## D15 — Rate Limiting: slowapi, 30 req/min on /search
**Decision:** `slowapi`, 30 requests/minute limit on POST /search.
**Why:** Purpose-built for FastAPI, minimal config, satisfies "simple rate limiting."
**Document section:** 6.6

## D16 — WSL for up.sh
**Decision:** `up.sh` is a bash script; developer runs via WSL on Windows 11.
**Why:** Assignment requires Linux/macOS compatible script. Developer has WSL installed.
**Document section:** 3, 7

## D17 — Dashboard Data Endpoints (not in assignment spec, added by us)
**Decision:** 3 extra endpoints: GET /dashboard/kpi, GET /dashboard/logs, GET /dashboard/experiments.
**Why:** Assignment requires 4 dashboard pages but doesn't specify data endpoints. Frontend needs data. These are builder's implementation choice.
**Document section:** 6.4

## D18 — Filters: category Field Derived from Article Titles
**Decision:** `filters: dict` in SearchRequest. `category` field in docs.jsonl derived from article titles using keyword rules. Post-retrieval filter on category after hybrid scoring.
**Categories:** computer_science | physics | biology | mathematics | chemistry | general_science
**Why:** Assignment includes `filters` in POST /search explicitly. source and created_at are corpus-level constants (useless as filters). `category` is derived from real content — defensible.
**Document section:** 6.3

## D19 — Input Validation: Pydantic SearchRequest
**Decision:**
```python
class SearchRequest(BaseModel):
    query:   str   = Field(..., min_length=1, max_length=1000)
    top_k:   int   = Field(10, ge=1, le=50)
    alpha:   float = Field(0.5, ge=0.0, le=1.0)
    filters: dict  = Field(default_factory=dict)
```
Bad input → HTTP 422. top_k > num_docs → `min(top_k, num_docs)` gracefully.
**Document section:** 6.6

## D20 — No Re-Ranking Loop / No LLM
**Decision:** Pure retrieval. No LLM. No feedback-driven re-ranking. /feedback logs human signals only.
**Why:** This is a retrieval system, not a generation system. Reviewer expects ranked documents.
**Document section:** 4 (system description)
