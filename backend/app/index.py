"""Build BM25 and FAISS vector indexes from docs.jsonl.

Usage:
    python -m app.index --input data/processed/docs.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex, compute_corpus_hash

_BM25_SUBDIR = "bm25"
_VECTOR_SUBDIR = "vector"


def _load_docs(jsonl_path: Path) -> list[dict]:
    docs: list[dict] = []
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def _corpus_texts(docs: list[dict]) -> list[str]:
    return [f"{d['title']} {d['text']}" for d in docs]


def build_bm25(docs: list[dict], index_dir: Path) -> None:
    texts = _corpus_texts(docs)
    doc_ids = [d["doc_id"] for d in docs]
    idx = BM25Index()
    print(f"Building BM25 index over {len(docs)} documents...")
    idx.build(texts, doc_ids)
    idx.save(index_dir / _BM25_SUBDIR)
    print(f"  BM25 saved -> {index_dir / _BM25_SUBDIR}")


def build_vector(docs: list[dict], index_dir: Path, jsonl_path: Path) -> None:
    texts = _corpus_texts(docs)
    doc_ids = [d["doc_id"] for d in docs]
    corpus_hash = compute_corpus_hash(jsonl_path)
    idx = VectorIndex()
    print(f"Building vector index over {len(docs)} documents (CPU encoding)...")
    idx.build(texts, doc_ids)
    idx.save(index_dir / _VECTOR_SUBDIR, corpus_hash=corpus_hash)
    print(f"  Vector index saved -> {index_dir / _VECTOR_SUBDIR}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build search indexes from docs.jsonl")
    parser.add_argument("--input", required=True, help="Path to docs.jsonl")
    args = parser.parse_args(argv)

    jsonl_path = Path(args.input).resolve()
    if not jsonl_path.exists():
        print(f"ERROR: input file not found: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    # data/index/ lives two levels up from data/processed/docs.jsonl
    index_dir = jsonl_path.parent.parent / "index"

    docs = _load_docs(jsonl_path)
    print(f"Loaded {len(docs)} documents from {jsonl_path}")

    build_bm25(docs, index_dir)
    build_vector(docs, index_dir, jsonl_path)

    print("\nIndex build complete.")
    print(f"  BM25 : {index_dir / _BM25_SUBDIR / 'bm25_index.pkl'}")
    print(f"  FAISS: {index_dir / _VECTOR_SUBDIR / 'faiss.index'}")
    print(f"  Meta : {index_dir / _VECTOR_SUBDIR / 'metadata.json'}")


if __name__ == "__main__":
    main()
