"""
Downloads 400 arXiv CS paper abstracts to data/raw/.
Distribution: 16 papers x 5 years (2017-2021) x 5 categories = 400 total
Categories: cs.LG, cs.CL, cs.CV, cs.AI, cs.IR
Skips download if data/raw/ already has >= 400 .txt files (idempotent).

Run: python -m app.download_data
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CORPUS_SIZE = 400
TARGET_CATS = ["cs.LG", "cs.CL", "cs.CV", "cs.AI", "cs.IR"]
TARGET_YEARS = ["2017", "2018", "2019", "2020", "2021"]
PER_SLOT = CORPUS_SIZE // (len(TARGET_CATS) * len(TARGET_YEARS))  # 16
RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def _parse_year(arxiv_id: str) -> str | None:
    m = re.match(r"^(\d{2})\d{2}\.", arxiv_id)
    if not m:
        return None
    yy = int(m.group(1))
    return f"20{yy:02d}" if 17 <= yy <= 21 else None


def _parse_date(arxiv_id: str) -> str:
    m = re.match(r"^(\d{2})(\d{2})\.", arxiv_id)
    if not m:
        return "2017-01-01"
    yy, mm = m.group(1), m.group(2)
    return f"20{yy}-{mm}-01"


def _is_english(text: str) -> bool:
    return sum(1 for c in text if ord(c) < 128) / max(len(text), 1) > 0.92


def download(out_dir: Path = RAW_DIR, corpus_size: int = CORPUS_SIZE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [f for f in out_dir.glob("doc_*.txt")]
    if len(existing) >= corpus_size:
        print(f"data/raw/ already has {len(existing)} files -- skipping download.", flush=True)
        return

    print("Loading arXiv dataset from HuggingFace (streaming) ...", flush=True)
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: 'datasets' package not installed. Run: pip install datasets", file=sys.stderr)
        sys.exit(1)

    slots: dict[tuple[str, str], int] = {
        (cat, yr): 0 for cat in TARGET_CATS for yr in TARGET_YEARS
    }
    manifest: list[dict] = []
    doc_num = 1

    ds = load_dataset("gfissore/arxiv-abstracts-2021", split="train", streaming=True)
    total_seen = 0

    for record in ds:
        total_seen += 1
        arxiv_id: str = record.get("id", "")
        year = _parse_year(arxiv_id)
        if year is None:
            continue

        cats: list[str] = record.get("categories", [])
        title: str = record.get("title", "").replace("\n", " ").strip()
        abstract: str = record.get("abstract", "").replace("\n", " ").strip()
        words = len(abstract.split())

        if not _is_english(title) or not _is_english(abstract):
            continue
        if words < 100 or words > 260 or not title or len(title) < 15:
            continue

        matched_cat = None
        for cat in TARGET_CATS:
            if cat in cats and slots[(cat, year)] < PER_SLOT:
                matched_cat = cat
                break
        if matched_cat is None:
            continue

        slots[(matched_cat, year)] += 1
        doc_id = f"doc_{doc_num:03d}"
        created_at = _parse_date(arxiv_id)

        (out_dir / f"{doc_id}.txt").write_text(
            f"TITLE: {title}\n{abstract}", encoding="utf-8"
        )
        manifest.append({
            "doc_id": doc_id,
            "title": title,
            "category": matched_cat,
            "year": year,
            "created_at": created_at,
            "arxiv_id": arxiv_id,
            "abstract_words": words,
        })
        doc_num += 1

        if doc_num % 40 == 1:
            filled = sum(1 for v in slots.values() if v >= PER_SLOT)
            print(f"  {doc_num-1}/{corpus_size} docs | {filled}/25 slots full | scanned {total_seen:,}", flush=True)

        if all(v >= PER_SLOT for v in slots.values()):
            break

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Done. {doc_num-1} articles -> {out_dir} | manifest -> {out_dir}/manifest.json", flush=True)


if __name__ == "__main__":
    download()
