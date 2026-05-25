"""
Vector index: sentence-transformers embeddings + FAISS IndexFlatIP (cosine similarity).
L2-normalized vectors + inner product = cosine similarity.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np

MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
DIMENSION: int = 384
# BGE v1.5 retrieval: queries use this prefix; documents are indexed without it
QUERY_PREFIX: str = "Represent this sentence for searching relevant passages: "

_FAISS_FILENAME = "faiss.index"
_IDS_FILENAME = "doc_ids.json"
_META_FILENAME = "metadata.json"


class VectorIndex:
    """Sentence-transformer embeddings stored in a FAISS IndexFlatIP index."""

    def __init__(self) -> None:
        self._index: faiss.IndexFlatIP | None = None
        self._doc_ids: list[str] = []
        self._model: Any = None  # SentenceTransformer loaded lazily

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def _encode(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        """Encode texts and return L2-normalised float32 vectors.
        Queries use QUERY_PREFIX for asymmetric retrieval; documents do not.
        """
        model = self._get_model()
        kwargs: dict = dict(
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        if is_query and QUERY_PREFIX:
            kwargs["prompt"] = QUERY_PREFIX
        vecs: np.ndarray = model.encode(texts, **kwargs).astype(np.float32)
        return vecs

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build(self, docs: list[str], doc_ids: list[str]) -> None:
        """Encode corpus and add to a fresh FAISS index."""
        if len(docs) != len(doc_ids):
            raise ValueError("docs and doc_ids must have equal length")
        vecs = self._encode(docs)
        self._index = faiss.IndexFlatIP(DIMENSION)
        self._index.add(vecs)
        self._doc_ids = list(doc_ids)

    def query(self, q: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Return top_k (doc_id, cosine_score) pairs, descending.
        Raises RuntimeError if index is not built.
        """
        if self._index is None:
            raise RuntimeError("VectorIndex is not built. Call build() or load() first.")
        vec = self._encode([q], is_query=True)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(vec, k)
        results = [
            (self._doc_ids[int(idx)], float(score))
            for idx, score in zip(indices[0], scores[0])
            if idx >= 0
        ]
        return sorted(results, key=lambda x: x[1], reverse=True)

    def save(self, path: Path, corpus_hash: str = "") -> None:
        """Write faiss.index, doc_ids.json, and metadata.json to path."""
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path / _FAISS_FILENAME))
        (path / _IDS_FILENAME).write_text(
            json.dumps(self._doc_ids, ensure_ascii=False), encoding="utf-8"
        )
        metadata = {
            "model_name": MODEL_NAME,
            "dimension": DIMENSION,
            "corpus_hash": corpus_hash,
            "build_timestamp": datetime.now(timezone.utc).isoformat(),
            "num_docs": len(self._doc_ids),
        }
        (path / _META_FILENAME).write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    def load(self, path: Path) -> None:
        """Load FAISS index, doc_ids, and metadata from path."""
        self._index = faiss.read_index(str(path / _FAISS_FILENAME))
        self._doc_ids = json.loads((path / _IDS_FILENAME).read_text(encoding="utf-8"))

    @staticmethod
    def validate_metadata(path: Path) -> None:
        """
        Read metadata.json and verify model_name + dimension match current constants.
        Raises ValueError with a rebuild instruction if they don't match.
        """
        meta_path = path / _META_FILENAME
        if not meta_path.exists():
            raise FileNotFoundError(f"metadata.json not found at {meta_path}")
        meta: dict = json.loads(meta_path.read_text(encoding="utf-8"))
        stored_model = meta.get("model_name", "")
        stored_dim = meta.get("dimension", 0)
        if stored_model != MODEL_NAME or stored_dim != DIMENSION:
            raise ValueError(
                f"Index built with {stored_model} ({stored_dim}-dim). "
                f"Current model is {MODEL_NAME} ({DIMENSION}-dim). "
                f"Rebuild with: python -m app.index"
            )

    @property
    def num_docs(self) -> int:
        return len(self._doc_ids)


def compute_corpus_hash(jsonl_path: Path) -> str:
    """SHA-256 of the docs.jsonl file contents for change detection."""
    content = jsonl_path.read_bytes()
    return hashlib.sha256(content).hexdigest()
