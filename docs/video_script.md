# Video Script — Hybrid Search + KPI Dashboard
# Ayush Mishra | Target: 7 minutes

---

## PART 1 — INTRO & SETUP
### Show: GitHub repo → README → docs folder
### Time: ~1.5 min

Hi, I'm Ayush Mishra, and this is my submission for the End-to-End Hybrid Search
and KPI Dashboard assignment.

Before I walk you through what I built, let me quickly show you how easy it is
to get this running from scratch.

Here's the GitHub repository — AyushMishra1006/hybrid-search-kpi. Everything is
here — the backend, the frontend, 400 arXiv research papers as the dataset,
pre-built search indexes, all documentation, and 28 commits showing the full
build history.

[Show docs folder on GitHub]

Inside docs you'll find four files the assignment specifically requires —
architecture.md with the full system design, decision_log.md where every design
choice is justified, codex_log.md which is the granular AI prompt log with one
entry per commit, and break_fix_log.md documenting all three failure scenarios.

To run this yourself, open WSL on Windows and follow three steps from the README.
First, install Python and Node.js — one command each. Then clone the repo, give
execute permission to the boot script, and run ./up.sh. That's it.

The first run takes about 7 minutes — it installs all Python and Node
dependencies and downloads the BGE embedding model. Every run after that boots
in under 10 seconds.

The script is fully idempotent — you can run it twice without breaking anything.
It checks what's already done and skips it. When finished, you get two URLs —
backend on port 8000, frontend on port 5173.

---

## PART 2 — WHAT WE BUILT
### Show: Frontend landing page
### Time: ~30 sec

So what did I actually build? This is a mini knowledge search engine over 400
arXiv computer science papers — covering machine learning, NLP, computer vision,
AI, and information retrieval.

The core idea is hybrid search — combining BM25 keyword matching with vector
search using the BGE-small sentence transformer model. You get the best of both.

Every query is logged to SQLite, latency is tracked, and everything is
visualised across four pages — Search, KPI, Evaluation, and Debug.

---

## PART 3 — SEARCH PAGE
### Show: Search page — type query, show score bars, adjust alpha, filter category
### Time: ~1.5 min

Starting with Search. I'll type a query — "attention mechanisms in transformers".

Results come back instantly. Each result shows the paper title, the arXiv
category as a pill tag, a highlighted snippet from the abstract, and three score
bars — BM25 score, vector score, and the combined hybrid score. That per-result
score breakdown is explicit so you can see exactly why each document was ranked
where it is.

Now the alpha slider. Alpha controls the blend between BM25 and vector search.
At 1.0 — pure BM25, results are keyword-driven. At 0.0 — pure vector, results
are ranked by semantic meaning. At 0.3 — our evaluation found this is the
optimal point on this corpus — the system leans slightly semantic, understanding
what you mean, not just what you typed.

You can also filter by category. Selecting cs.CL shows only Natural Language
Processing papers. Combined with alpha control, this gives precise flexibility
over retrieval behaviour.

---

## PART 4 — KPI PAGE
### Show: KPI page — latency cards, volume chart, top queries, zero-result queries
### Time: ~1 min

Now the KPI dashboard. Every search is logged to SQLite in real time and this
page visualises it.

The latency cards show P50 and P95. P50 is the median response time. P95 means
95% of all queries finished within this time — if P95 is 80 milliseconds, only
1 in 20 queries was slower. These are standard production reliability metrics.

The request volume chart shows query count per hour — you can see usage patterns
over time.

Below that are two more panels — Top Queries, which shows the most frequently
searched terms, and Zero-Result Queries, which shows searches where the system
found nothing. Zero results is a quality signal — it tells you where the corpus
has gaps or where the search is failing to surface relevant documents.

---

## PART 5 — EVALUATION PAGE
### Show: Evaluation page — experiment table, nDCG trend chart
### Time: ~1 min

The Evaluation page shows the results of five formal retrieval experiments run
against 25 hand-labelled queries with ground-truth relevance judgements.

The three metrics are nDCG@10 — ranking quality, Recall@10 — how many relevant
documents appeared in the top 10, and MRR — Mean Reciprocal Rank, which
measures how high the first correct result appears.

Best configuration: alpha = 0.3, min-max normalisation — nDCG of 0.8657,
Recall of 0.90, MRR of 0.86.

The chart shows nDCG across all five runs. You can see pure BM25 and pure vector
both underperform. The hybrid at the right alpha wins every time. That's the
core finding of the project.

We also compared two normalisation strategies — min-max versus z-score. Min-max
won and the reasoning is documented in docs/decision_log.md.

---

## PART 6 — DEBUG PAGE
### Show: Debug page — log table, point out severity filter and fields
### Time: ~30 sec

The Debug page is a structured query log. Every request is recorded with these
exact fields — request_id, query text, latency in milliseconds, top_k, alpha
value, result count, and a severity flag.

Severity is "info" for normal queries and "error" if something went wrong. You
can filter the log by severity and time range to narrow down problems quickly.

This is production-style observability — if a query starts failing or taking too
long, you trace it here.

---

## PART 7 — BREAK/FIX SCENARIOS
### Show: GitHub commit history — point to commits 19-22
### Time: ~1.5 min

The assignment required three intentional failure scenarios. All three are fully
documented in docs/break_fix_log.md. Let me walk through them using the commit
history on GitHub.

[Show commit list, point to commits 19, 20, 21, 22]

Scenario A — Semantic index mismatch. Commit 19 deliberately changed the
embedding model name in vector.py to a wrong value. On startup, our system runs
validate_metadata() which reads the metadata.json saved when the FAISS index was
built and checks that the model name and embedding dimensions match. With the
wrong name, the server refuses to start — clear error, no silent corruption.
Commit 20 restores the correct model name. Server starts cleanly. Fail loudly,
fail early.

Scenario B — Schema migration break. Commit 21 added a NOT NULL column to the
SQLite query_logs table without a DEFAULT value. SQLite forbids this on existing
tables, so the API failed to write any logs and the dashboard broke. The fix was
a proper v1 to v2 schema migration with a DEFAULT value. Also in commit 21.

Scenario C — Divide-by-zero in normalisation. If all BM25 scores in a result
set are identical, min-max normalisation divides by zero, producing NaN scores
and completely wrong ranking. Commit 22 adds a zero-division guard and a
regression test that locks this behaviour permanently so it can never silently
break again.

All three scenarios are in the log — what was injected, what failed, what the
fix was, and what test prevents regression.

---

## CLOSE
### Time: ~15 sec

That's the full system — hybrid retrieval with configurable alpha, a KPI
dashboard with real-time observability, formal evaluation across five experiments,
structured debug logging, and three validated failure scenarios. Thanks for
watching.
