# Video Script — Hybrid Search + KPI Dashboard
# Ayush Mishra | Target: 7 minutes

---

## PART 1 — INTRO & SETUP
### Show: GitHub repo + README
### Time: ~1.5 min

Hi, I'm Ayush Mishra, and this is my submission for the End-to-End Hybrid Search
and KPI Dashboard assignment.

Before I walk you through what I built, let me quickly show you how easy it is
to get this running from scratch.

Here's the GitHub repository — AyushMishra1006/hybrid-search-kpi. Everything is
here — the backend, the frontend, 400 arXiv research papers as our dataset,
pre-built search indexes, all documentation, and 28 commits showing the full
build history.

To run this yourself, you open WSL on Windows and follow three steps from the
README. First, install Python and Node.js — one command each. Then clone the
repo, give execute permission to the boot script, and run ./up.sh. That's it.

The first run takes about 7 minutes — it installs all Python and Node
dependencies and downloads the embedding model. Every run after that boots in
under 10 seconds.

The script is fully idempotent — you can run it twice, it won't break anything.
It checks what's already done and skips it. When it's finished, you get two URLs
— backend on port 8000, frontend on port 5173.

---

## PART 2 — WHAT WE BUILT
### Show: Frontend landing page
### Time: ~30 sec

So what did I actually build? This is a mini knowledge search engine over 400
arXiv computer science papers — covering machine learning, NLP, computer vision,
AI, and information retrieval.

The core idea is hybrid search — combining two retrieval techniques: BM25, which
is classic keyword matching, and vector search, which is semantic similarity
using a sentence transformer model called BGE-small. You get the best of both
worlds.

There are four pages — Search, KPI, Evaluation, and Debug. Let me go through
each one.

---

## PART 3 — SEARCH PAGE
### Show: Search page, type query, adjust alpha, filter by category
### Time: ~1.5 min

Starting with Search. I'll type a query — let's go with "attention mechanisms in
transformers".

You can see the results come back instantly — each result shows the paper title,
the arXiv category as a pill tag, a snippet from the abstract, and three score
bars — BM25 score, vector score, and the combined hybrid score.

Now here's the interesting part — this alpha slider. Alpha controls the blend
between BM25 and vector search. Right now it's at 0.5, equal weight. Watch what
happens when I push it all the way to 1.0 — pure BM25. The results shift toward
exact keyword matches.

Now pull it to 0.0 — pure vector search. Completely different ordering — now
it's ranking by semantic meaning, not keywords.

Our evaluation found that alpha = 0.3 gives the best results on this corpus —
slightly leaning semantic. So the system is tuned to understand what you mean,
not just what you typed.

You can also filter by category — if I select cs.CL, I only see Natural Language
Processing papers. Combined with the alpha control, this gives a lot of
flexibility.

---

## PART 4 — KPI PAGE
### Show: KPI page — latency cards, volume chart
### Time: ~1 min

Now the KPI dashboard. This is the observability layer — every search query is
logged to SQLite, and this page visualises that data in real time.

The cards at the top show latency metrics. P50 is the median response time. P95
means 95% of all queries finished within this time — so if P95 is 80
milliseconds, only 1 in 20 queries was slower than that. These are the standard
metrics used in production systems to measure reliability.

Below that is the request volume chart — each bar is one hour, showing how many
searches happened. You can spot usage patterns here.

The total request count and zero-result rate are also tracked. A high zero-result
rate is a signal that the search isn't finding relevant documents — useful for
improving the corpus over time.

---

## PART 5 — EVALUATION PAGE
### Show: Evaluation page — experiment table, nDCG chart
### Time: ~1 min

The Evaluation page shows the results of our formal retrieval experiments. I ran
5 experiments with 25 hand-labelled queries and ground-truth relevance
judgements.

The three metrics are nDCG@10 — which measures ranking quality, Recall@10 — how
many relevant documents we actually retrieved in the top 10, and MRR — Mean
Reciprocal Rank, which tells you how high the first relevant result appears.

The best configuration was alpha = 0.3 with min-max normalisation — nDCG of
0.8657, Recall of 0.90, MRR of 0.86. That's strong performance.

The chart shows how nDCG changes across experiments. You can see that pure BM25
and pure vector search both underperform — the hybrid combination at the right
alpha wins every time. That's the whole point of the project.

---

## PART 6 — DEBUG PAGE
### Show: Debug page — query log table
### Time: ~30 sec

The Debug page is a structured query log. Every single search is recorded — the
query text, timestamp, latency, alpha value, how many results came back, and a
severity flag — info for normal queries, error if something went wrong.

This is what observability looks like in a real system. If a query starts
returning errors or taking too long, you can trace it here exactly.

---

## PART 7 — BREAK/FIX SCENARIO A
### Show: GitHub commit history — commits 19 and 20
### Time: ~1.5 min

Finally, the assignment required us to intentionally introduce and then fix real
engineering failures. Let me show one — Scenario A.

Here on GitHub in the commit history — you can see commit 19 is labelled
break(A) and commit 20 is fix(A).

In commit 19, I deliberately changed the model name in our vector search code
from the correct BAAI/bge-small-en-v1.5 to a wrong name. The idea was — what
happens if someone misconfigures the embedding model?

What actually happens is this — on startup, our system runs a validation check
called validate_metadata(). It reads the metadata.json file that was saved when
the FAISS index was originally built — which contains the model name and
embedding dimensions that were used. If the model name in the config doesn't
match what was used to build the index, the server refuses to start. You would
see a clear error: model mismatch detected.

If we were running commit 19 right now, the backend would not start at all.
Commit 20 restores the correct model name. Validation passes, server starts
cleanly.

This is intentional defensive design — a silent mismatch would give completely
wrong search results with no warning. A hard startup failure forces you to fix
the root cause immediately. Fail loudly, fail early.

---

## CLOSE
### Time: ~15 sec

That's the full system — hybrid retrieval, a KPI dashboard, formal evaluation,
structured observability, and validated failure handling. Thanks for watching.
