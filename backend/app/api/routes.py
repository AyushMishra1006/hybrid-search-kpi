"""All API route handlers and Pydantic request/response models."""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.api.limiter import limiter
from app.db.logger import log_feedback, log_query

router = APIRouter()

_REPO_ROOT: Path = Path(__file__).resolve().parents[3]
_EXPERIMENTS_CSV: Path = _REPO_ROOT / "data" / "metrics" / "experiments.csv"
_SEARCH_RATE: str = "30/minute"

_NOW = lambda: datetime.now(timezone.utc).isoformat()  # noqa: E731


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(10, ge=1, le=50)
    alpha: float = Field(0.5, ge=0.0, le=1.0)
    filters: dict = Field(default_factory=dict)


class SearchResultItem(BaseModel):
    doc_id: str
    title: str
    snippet: str
    bm25_score: float
    vector_score: float
    hybrid_score: float
    category: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    query: str
    latency_ms: float
    result_count: int
    filters_applied: dict


class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    doc_id: str
    relevant: bool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(len(ordered) * pct / 100)
    return round(ordered[min(idx, len(ordered) - 1)], 2)


def _emit_stdout_log(payload: dict[str, Any]) -> None:
    print(json.dumps(payload), file=sys.stdout, flush=True)


def _build_log_payload(
    req_id: str,
    query: str,
    latency_ms: float,
    top_k: int,
    alpha: float,
    result_count: int,
    severity: str,
    error: Optional[str],
) -> dict[str, Any]:
    return {
        "request_id": req_id,
        "query": query,
        "latency_ms": round(latency_ms, 2),
        "top_k": top_k,
        "alpha": alpha,
        "result_count": result_count,
        "severity": severity,
        "error": error,
    }


def _fetch_latencies(conn: sqlite3.Connection) -> list[float]:
    rows = conn.execute("SELECT latency_ms FROM query_logs").fetchall()
    return [r["latency_ms"] for r in rows]


def _fetch_request_volume(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m-%dT%H:00:00', timestamp) AS bucket, COUNT(*) AS count
        FROM query_logs GROUP BY bucket ORDER BY bucket
        """
    ).fetchall()
    return [{"timestamp": r["bucket"], "count": r["count"]} for r in rows]


def _fetch_top_queries(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        "SELECT query, COUNT(*) AS count FROM query_logs GROUP BY query ORDER BY count DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [{"query": r["query"], "count": r["count"]} for r in rows]


def _fetch_zero_result_queries(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        """
        SELECT query, COUNT(*) AS count FROM query_logs
        WHERE result_count = 0 GROUP BY query ORDER BY count DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [{"query": r["query"], "count": r["count"]} for r in rows]


def _read_experiments() -> list[dict]:
    if not _EXPERIMENTS_CSV.exists():
        return []
    with _EXPERIMENTS_CSV.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health(request: Request) -> dict:
    return {
        "status": "OK",
        "version": request.app.state.version,
        "commit": request.app.state.commit,
    }


@router.post("/search", response_model=SearchResponse)
@limiter.limit(_SEARCH_RATE)
def search(request: Request, body: SearchRequest) -> SearchResponse:
    req_id = str(uuid.uuid4())
    timestamp = _NOW()
    conn: sqlite3.Connection = request.app.state.db
    severity = "info"
    error_msg: Optional[str] = None
    results = []

    start = time.perf_counter()
    try:
        raw = request.app.state.hybrid.search(
            body.query, top_k=body.top_k, alpha=body.alpha, filters=body.filters
        )
        results = raw
    except Exception as exc:  # noqa: BLE001
        severity = "error"
        error_msg = str(exc)
    finally:
        latency_ms = (time.perf_counter() - start) * 1000

    result_count = len(results)
    payload = _build_log_payload(req_id, body.query, latency_ms, body.top_k, body.alpha, result_count, severity, error_msg)
    _emit_stdout_log(payload)
    log_query(conn, req_id, timestamp, body.query, round(latency_ms, 2), body.top_k, body.alpha, result_count, severity, error_msg)

    if severity == "error":
        raise HTTPException(status_code=500, detail=error_msg)

    return SearchResponse(
        results=[SearchResultItem(**r.__dict__) for r in results],
        query=body.query,
        latency_ms=round(latency_ms, 2),
        result_count=result_count,
        filters_applied=body.filters,
    )


@router.post("/feedback", status_code=204, response_model=None)
def feedback(request: Request, body: FeedbackRequest) -> None:
    conn: sqlite3.Connection = request.app.state.db
    log_feedback(conn, str(uuid.uuid4()), _NOW(), body.query, body.doc_id, body.relevant)


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(request: Request) -> str:
    conn: sqlite3.Connection = request.app.state.db
    latencies = _fetch_latencies(conn)
    total = len(latencies)
    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    zero = conn.execute("SELECT COUNT(*) FROM query_logs WHERE result_count=0").fetchone()[0]
    errors = conn.execute("SELECT COUNT(*) FROM query_logs WHERE severity='error'").fetchone()[0]
    return (
        f"search_requests_total {total}\n"
        f"search_latency_p50_ms {p50}\n"
        f"search_latency_p95_ms {p95}\n"
        f"zero_result_queries_total {zero}\n"
        f"search_errors_total {errors}\n"
    )


@router.get("/dashboard/kpi")
def dashboard_kpi(request: Request) -> dict:
    conn: sqlite3.Connection = request.app.state.db
    latencies = _fetch_latencies(conn)
    return {
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p95_ms": _percentile(latencies, 95),
        "request_volume": _fetch_request_volume(conn),
        "top_queries": _fetch_top_queries(conn),
        "zero_result_queries": _fetch_zero_result_queries(conn),
    }


@router.get("/dashboard/logs")
def dashboard_logs(
    request: Request,
    since: Optional[str] = None,
    until: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[dict]:
    conn: sqlite3.Connection = request.app.state.db
    conditions, params = [], []
    if since:
        conditions.append("timestamp >= ?")
        params.append(since)
    if until:
        conditions.append("timestamp <= ?")
        params.append(until)
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = conn.execute(
        f"SELECT * FROM query_logs {where} ORDER BY timestamp DESC LIMIT 500",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/dashboard/experiments")
def dashboard_experiments() -> list[dict]:
    return _read_experiments()
