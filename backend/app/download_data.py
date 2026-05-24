"""
Downloads 400 Simple English Wikipedia articles to data/raw/.
Skips all downloads if files already exist (idempotent).
Run: python -m app.download_data
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from app.utils.preprocessing import assign_category  # single source of truth for category rules

CORPUS_SIZE = 400
SOURCE_NAME = "simple_wikipedia"
CREATED_AT = "2022-03-01"
RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

def _write_article(doc_id: str, title: str, text: str, out_dir: Path) -> str:
    """Write doc as TITLE: <title>\n<text body>. Returns derived category."""
    category = assign_category(title)
    path = out_dir / f"{doc_id}.txt"
    path.write_text(f"TITLE: {title}\n{text}", encoding="utf-8")
    return category


def _is_science_tech(title: str, text: str) -> bool:
    sci_keywords = [
        "science", "biology", "chemistry", "physics", "math", "computer",
        "technology", "energy", "atom", "cell", "gene", "evolution",
        "algorithm", "internet", "software", "robot", "quantum", "planet",
        "star", "element", "molecule", "force", "motion", "electricity",
        "light", "heat", "sound", "gravity", "theory", "experiment",
        "medicine", "brain", "body", "disease", "virus", "bacteria",
        "plant", "animal", "ecology", "climate", "geology", "space",
    ]
    combined = (title + " " + text[:200]).lower()
    return any(kw in combined for kw in sci_keywords)


def download(out_dir: Path = RAW_DIR, corpus_size: int = CORPUS_SIZE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = list(out_dir.glob("doc_*.txt"))
    if len(existing) >= corpus_size:
        print(f"data/raw/ already has {len(existing)} files — skipping download.", flush=True)
        return

    print("Loading Simple English Wikipedia dataset from HuggingFace ...", flush=True)
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        print("ERROR: 'datasets' package not installed. Run: pip install datasets", file=sys.stderr)
        sys.exit(1)

    dataset = load_dataset("wikimedia/wikipedia", "20231101.simple", split="train")

    written = 0
    manifest: list[dict] = []

    for record in dataset:
        if written >= corpus_size:
            break
        title: str = record["title"].strip()
        text: str = re.sub(r"\s+", " ", record["text"]).strip()
        if not title or not text or len(text.split()) < 30:
            continue
        if not _is_science_tech(title, text):
            continue

        doc_id = f"doc_{written + 1:03d}"
        category = _write_article(doc_id, title, text, out_dir)
        manifest.append({"doc_id": doc_id, "title": title, "category": category})
        written += 1

        if written % 50 == 0:
            print(f"  {written}/{corpus_size} articles written ...", flush=True)

    if written < corpus_size:
        print(
            f"WARNING: Only {written} science/tech articles found. "
            f"Relaxing filter for remaining {corpus_size - written} slots.",
            flush=True,
        )
        for record in dataset:
            if written >= corpus_size:
                break
            title = record["title"].strip()
            text = re.sub(r"\s+", " ", record["text"]).strip()
            if not title or not text or len(text.split()) < 30:
                continue
            doc_id = f"doc_{written + 1:03d}"
            if (out_dir / f"{doc_id}.txt").exists():
                written += 1
                continue
            category = _write_article(doc_id, title, text, out_dir)
            manifest.append({"doc_id": doc_id, "title": title, "category": category})
            written += 1

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Done. {written} articles -> {out_dir}  |  manifest -> {manifest_path}", flush=True)


if __name__ == "__main__":
    download()
