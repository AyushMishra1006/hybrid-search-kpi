"""Write one structured log row to query_logs table."""
from __future__ import annotations

import sqlite3
from typing import Optional


def log_query(
    conn: sqlite3.Connection,
    req_id: str,
    timestamp: str,
    query: str,
    latency_ms: float,
    top_k: int,
    alpha: float,
    result_count: int,
    severity: str = "info",
    error: Optional[str] = None,
) -> None:
    """Insert one query log row. Uses INSERT OR IGNORE to be idempotent on req_id."""
    conn.execute(
        """
        INSERT OR IGNORE INTO query_logs
            (id, timestamp, query, latency_ms, top_k, result_count, severity, error, alpha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (req_id, timestamp, query, latency_ms, top_k, result_count, severity, error, alpha),
    )
    conn.commit()


def log_feedback(
    conn: sqlite3.Connection,
    req_id: str,
    timestamp: str,
    query: str,
    doc_id: str,
    relevant: bool,
) -> None:
    """Insert one relevance feedback row."""
    conn.execute(
        """
        INSERT OR IGNORE INTO relevance_feedback (id, timestamp, query, doc_id, relevant)
        VALUES (?, ?, ?, ?, ?)
        """,
        (req_id, timestamp, query, doc_id, int(relevant)),
    )
    conn.commit()
