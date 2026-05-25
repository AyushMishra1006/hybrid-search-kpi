"""SQLite schema: create tables, seed schema_version=1, run v1→v2 migration."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_V1_DDL = """
CREATE TABLE IF NOT EXISTS query_logs (
    id           TEXT PRIMARY KEY,
    timestamp    TEXT NOT NULL,
    query        TEXT NOT NULL,
    latency_ms   REAL NOT NULL,
    top_k        INTEGER NOT NULL,
    result_count INTEGER NOT NULL,
    severity     TEXT NOT NULL DEFAULT 'info',
    error        TEXT
);

CREATE TABLE IF NOT EXISTS relevance_feedback (
    id        TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    query     TEXT NOT NULL,
    doc_id    TEXT NOT NULL,
    relevant  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""

_NOW = lambda: datetime.now(timezone.utc).isoformat()  # noqa: E731


def init_db(db_path: Path | str) -> sqlite3.Connection:
    """Create tables and seed schema_version=1 if not present. Return connection."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    conn.executescript(_V1_DDL)
    if not conn.execute("SELECT 1 FROM schema_version WHERE version=1").fetchone():
        conn.execute("INSERT INTO schema_version VALUES (1, ?)", (_NOW(),))
        conn.commit()
    return conn


def check_and_migrate(conn: sqlite3.Connection) -> None:
    """Upgrade v1 → v2: add alpha column to query_logs (Scenario B fix)."""
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current = row[0] if row[0] is not None else 1
    if current < 2:
        # BREAK(B): NOT NULL without DEFAULT — SQLite rejects this at ALTER TABLE time.
        # Every log write fails: "Cannot add a NOT NULL column with default value NULL."
        # FIX: always supply DEFAULT when adding a NOT NULL column via ALTER TABLE.
        conn.execute("ALTER TABLE query_logs ADD COLUMN alpha REAL DEFAULT 0.5")
        conn.execute("INSERT INTO schema_version VALUES (2, ?)", (_NOW(),))
        conn.commit()
