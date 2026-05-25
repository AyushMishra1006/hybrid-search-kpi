"""FastAPI application — lifespan, middleware, app factory."""
from __future__ import annotations

import json
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.limiter import limiter
from app.api.routes import router
from app.db.schema import check_and_migrate, init_db
from app.search.bm25 import BM25Index
from app.search.hybrid import HybridSearch
from app.search.vector import VectorIndex

APP_VERSION: str = "1.0.0"
_REPO_ROOT: Path = Path(__file__).resolve().parents[3]
_BM25_DIR: Path = _REPO_ROOT / "data" / "index" / "bm25"
_VECTOR_DIR: Path = _REPO_ROOT / "data" / "index" / "vector"
_DOCS_JSONL: Path = _REPO_ROOT / "data" / "processed" / "docs.jsonl"
_DB_PATH: Path = _REPO_ROOT / "data" / "search.db"


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


def _load_doc_store(jsonl_path: Path) -> dict[str, dict]:
    docs: dict[str, dict] = {}
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped:
                doc = json.loads(stripped)
                docs[doc["doc_id"]] = doc
    return docs


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    VectorIndex.validate_metadata(_VECTOR_DIR)      # raises if model/dim mismatch (Scenario A)

    bm25 = BM25Index()
    bm25.load(_BM25_DIR)

    vector = VectorIndex()
    vector.load(_VECTOR_DIR)
    vector.query("warmup", top_k=1)          # pre-loads model weights into RAM

    doc_store = _load_doc_store(_DOCS_JSONL)

    conn = init_db(_DB_PATH)
    check_and_migrate(conn)                         # runs v1→v2 migration if needed (Scenario B)

    app.state.hybrid = HybridSearch(bm25, vector, doc_store)
    app.state.db = conn
    app.state.version = APP_VERSION
    app.state.commit = _git_commit_hash()

    yield

    conn.close()


app = FastAPI(title="Hybrid Search KPI", version=APP_VERSION, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
