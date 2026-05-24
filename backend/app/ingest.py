"""
Ingestion pipeline: data/raw/*.txt → data/processed/docs.jsonl

Usage:
    python -m app.ingest --input data/raw --out data/processed
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SOURCE = "simple_wikipedia"
CREATED_AT = "2022-03-01"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest raw .txt/.md files → docs.jsonl")
    parser.add_argument("--input", required=True, help="Directory containing raw .txt/.md files")
    parser.add_argument("--out", required=True, help="Output directory for docs.jsonl")
    return parser.parse_args()


def _parse_file(path: Path) -> tuple[str, str] | None:
    """
    Parse a raw article file.
    Expected format: Line 1 = 'TITLE: <title>', Lines 2+ = body text.
    Returns (title, body_text) or None if file is malformed.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return None

    if not lines or not lines[0].startswith("TITLE:"):
        return None

    title = lines[0][len("TITLE:"):].strip()
    body = " ".join(line.strip() for line in lines[1:] if line.strip())
    if not title or not body:
        return None
    return title, body


def _make_doc_id(index: int) -> str:
    return f"doc_{index:03d}"


def ingest(input_dir: Path, out_dir: Path) -> int:
    """
    Read all .txt and .md files from input_dir, normalize, write docs.jsonl.
    Returns count of documents written.
    """
    from app.utils.preprocessing import assign_category, clean_text, truncate_long_doc

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "docs.jsonl"

    raw_files = sorted(input_dir.glob("*.txt")) + sorted(input_dir.glob("*.md"))
    if not raw_files:
        print(f"ERROR: No .txt or .md files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    written = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for path in raw_files:
            parsed = _parse_file(path)
            if parsed is None:
                continue

            title, raw_body = parsed
            text = truncate_long_doc(clean_text(raw_body))
            category = assign_category(title)
            doc_id = _make_doc_id(written + 1)

            record = {
                "doc_id": doc_id,
                "title": title,
                "text": text,
                "source": SOURCE,
                "created_at": CREATED_AT,
                "category": category,
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"Ingested {written} documents -> {out_path}", flush=True)
    return written


def main() -> None:
    args = _parse_args()
    input_dir = Path(args.input)
    out_dir = Path(args.out)

    if not input_dir.exists():
        print(f"ERROR: Input directory '{input_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    ingest(input_dir, out_dir)


if __name__ == "__main__":
    main()
