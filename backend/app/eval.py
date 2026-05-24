"""Evaluation harness: nDCG@10, Recall@10, MRR@10 over 25 labeled queries.

Usage:
    python -m app.eval --queries data/eval/queries.jsonl \\
                       --qrels data/eval/qrels.json \\
                       --alpha 0.5 --normalization minmax
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.search.bm25 import BM25Index
from app.search.hybrid import HybridSearch
from app.search.vector import VectorIndex

_REPO_ROOT: Path = Path(__file__).resolve().parents[2]
_BM25_DIR: Path = _REPO_ROOT / "data" / "index" / "bm25"
_VECTOR_DIR: Path = _REPO_ROOT / "data" / "index" / "vector"
_DOCS_JSONL: Path = _REPO_ROOT / "data" / "processed" / "docs.jsonl"
_METRICS_CSV: Path = _REPO_ROOT / "data" / "metrics" / "experiments.csv"
_CSV_HEADER: list[str] = [
    "timestamp", "git_commit", "alpha", "normalization",
    "model", "nDCG@10", "Recall@10", "MRR@10",
]
_TOP_K: int = 10
_MODEL_NAME: str = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _dcg(relevances: list[int], k: int) -> float:
    return sum(
        rel / math.log2(rank + 2)
        for rank, rel in enumerate(relevances[:k])
    )


def ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    rels = [1 if did in relevant_ids else 0 for did in ranked_ids[:k]]
    dcg = _dcg(rels, k)
    ideal = _dcg(sorted(rels, reverse=True), k)
    return dcg / ideal if ideal > 0 else 0.0


def recall_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    hits = sum(1 for did in ranked_ids[:k] if did in relevant_ids)
    return hits / len(relevant_ids)


def mrr_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    for rank, did in enumerate(ranked_ids[:k], start=1):
        if did in relevant_ids:
            return 1.0 / rank
    return 0.0


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_queries(path: Path) -> list[dict]:
    queries = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def _load_qrels(path: Path) -> dict[str, list[str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_doc_store(path: Path) -> dict[str, dict]:
    docs: dict[str, dict] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                doc = json.loads(line)
                docs[doc["doc_id"]] = doc
    return docs


def _git_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(_REPO_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _append_csv(row: dict) -> None:
    _METRICS_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not _METRICS_CSV.exists()
    with _METRICS_CSV.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def run_eval(alpha: float, normalization: str, queries_path: Path, qrels_path: Path) -> None:
    print(f"Loading indexes...")
    bm25 = BM25Index()
    bm25.load(_BM25_DIR)

    vector = VectorIndex()
    vector.load(_VECTOR_DIR)

    doc_store = _load_doc_store(_DOCS_JSONL)
    searcher = HybridSearch(bm25, vector, doc_store)

    queries = _load_queries(queries_path)
    qrels = _load_qrels(qrels_path)

    print(f"Running eval: alpha={alpha}, normalization={normalization}, queries={len(queries)}")

    ndcg_scores: list[float] = []
    recall_scores: list[float] = []
    mrr_scores: list[float] = []

    for q in queries:
        qid = q["query_id"]
        query_text = q["query"]
        relevant = set(qrels.get(qid, []))

        results = searcher.search(
            query=query_text,
            top_k=_TOP_K,
            alpha=alpha,
            normalization=normalization,
        )
        ranked_ids = [r.doc_id for r in results]

        ndcg_scores.append(ndcg_at_k(ranked_ids, relevant, _TOP_K))
        recall_scores.append(recall_at_k(ranked_ids, relevant, _TOP_K))
        mrr_scores.append(mrr_at_k(ranked_ids, relevant, _TOP_K))

    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
    avg_recall = sum(recall_scores) / len(recall_scores)
    avg_mrr = sum(mrr_scores) / len(mrr_scores)

    print(f"  nDCG@10   = {avg_ndcg:.4f}")
    print(f"  Recall@10 = {avg_recall:.4f}")
    print(f"  MRR@10    = {avg_mrr:.4f}")

    row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "git_commit": _git_commit_hash(),
        "alpha": alpha,
        "normalization": normalization,
        "model": _MODEL_NAME,
        "nDCG@10": round(avg_ndcg, 4),
        "Recall@10": round(avg_recall, 4),
        "MRR@10": round(avg_mrr, 4),
    }
    _append_csv(row)
    print(f"  Appended to {_METRICS_CSV}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate hybrid search on labeled queries")
    parser.add_argument("--queries", required=True, help="Path to queries.jsonl")
    parser.add_argument("--qrels", required=True, help="Path to qrels.json")
    parser.add_argument("--alpha", type=float, default=0.5, help="BM25 weight [0,1]")
    parser.add_argument(
        "--normalization",
        choices=["minmax", "zscore"],
        default="minmax",
        help="Score normalization strategy",
    )
    args = parser.parse_args(argv)

    queries_path = Path(args.queries).resolve()
    qrels_path = Path(args.qrels).resolve()

    for p in (queries_path, qrels_path):
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)

    run_eval(args.alpha, args.normalization, queries_path, qrels_path)


if __name__ == "__main__":
    main()
