"""
AI Virtual Hospital - Database Connection Manager
Provides dual-mode engine:
1. Production PostgreSQL with pgvector extension (when DATABASE_URL is set or localhost:5432 is live)
2. Local persistent SQLite (data/aivh.db) with JSON serialization fallback
"""

import os
import sqlite3
import logging
from typing import Optional, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger("DatabaseConnection")

# Default PostgreSQL connection URL if environment variable is not explicitly provided
DEFAULT_PG_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/aivh"
)
DEFAULT_SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "aivh.db"
)


class DatabaseConnectionManager:
    def __init__(self, pg_url: Optional[str] = None, sqlite_path: Optional[str] = None):
        self.pg_url = pg_url or DEFAULT_PG_URL
        self.sqlite_path = sqlite_path or DEFAULT_SQLITE_PATH
        self.engine_type = "sqlite"  # Default fallback
        self.pgvector_enabled = False
        self._initialize_engine()

    def _initialize_engine(self):
        """Attempts to connect to PostgreSQL; if unavailable, falls back to persistent SQLite."""
        # Ensure data directory exists for SQLite
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)

        # Attempt PostgreSQL connection
        try:
            import psycopg2
            conn = psycopg2.connect(self.pg_url, connect_timeout=2)
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            
            # Check for pgvector extension
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                self.pgvector_enabled = True
                logger.info("PostgreSQL connected successfully with pgvector extension enabled.")
            except Exception as e:
                conn.rollback()
                logger.warning(f"pgvector extension could not be activated: {e}. Falling back to standard vector storage.")

            cur.close()
            conn.close()
            self.engine_type = "postgresql"
            logger.info(f"Using PostgreSQL database at {self.pg_url}")
            return
        except Exception as pg_err:
            logger.info(f"PostgreSQL not reachable ({pg_err}). Falling back to persistent local SQLite at {self.sqlite_path}")
            self.engine_type = "sqlite"
            self.pgvector_enabled = False

    @contextmanager
    def get_connection(self):
        """Yields a database connection context manager."""
        if self.engine_type == "postgresql":
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(self.pg_url, cursor_factory=RealDictCursor)
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.sqlite_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

    def get_status(self) -> dict:
        return {
            "engine": self.engine_type,
            "pgvector_enabled": self.pgvector_enabled,
            "storage_path": self.pg_url if self.engine_type == "postgresql" else self.sqlite_path,
        }


# Global singleton connection manager
db_manager = DatabaseConnectionManager()
