"""
Versioned migration runner for the AI-VH feedback store (STEP 36 / P6.1).
Applies SQL migrations in filename order, tracking progress in
schema_migrations so re-runs are idempotent.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

MIGRATIONS_DIR = Path(__file__).resolve().parent


def _discover_migrations() -> List[Tuple[str, Path]]:
    found: List[Tuple[str, Path]] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        found.append((path.stem, path))
    return found


MIGRATIONS: List[Tuple[str, Path]] = _discover_migrations()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_migrations(db_path: str) -> List[str]:
    """Apply pending migrations to the SQLite database. Returns applied versions."""
    if not MIGRATIONS:
        raise RuntimeError("No feedback migrations discovered.")
    applied: List[str] = []
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        for version, path in MIGRATIONS:
            if version in done:
                continue
            sql = path.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, _utcnow()),
            )
            conn.commit()
            applied.append(version)
        return applied
    finally:
        conn.close()
