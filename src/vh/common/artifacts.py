"""
Artifact registry for AI Virtual Hospital (AI-VH).
Manages versioned, content-hashed artifacts (datasets, indexes, prompts, models, golden sets, faults)
with strict lineage tracking and persistent metadata storage.
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class ArtifactKind(str, Enum):
    DATASET = "dataset"
    INDEX = "index"
    PROMPT_TEMPLATE = "prompt_template"
    MODEL = "model"
    GOLDEN_SET = "golden_set"
    FAULT_SET = "fault_set"


class ArtifactRecord(BaseModel):
    id: str
    kind: ArtifactKind
    name: str
    version: str
    sha256: str
    created_at: str
    parent_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storage_path: str


class ArtifactRegistry:
    """Registry managing versioned artifacts, content hashing, and lineage."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        storage_dir: Optional[str] = None
    ):
        self.db_path = Path(db_path) if db_path else (REPO_ROOT / "data" / "artifacts.db")
        self.storage_dir = Path(storage_dir) if storage_dir else (REPO_ROOT / "data" / "artifact_store")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create artifacts schema if not already initialized."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    parent_ids TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    storage_path TEXT NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_kind_name ON artifacts(kind, name);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_sha256 ON artifacts(sha256);")

    def register_artifact(
        self,
        kind: Union[ArtifactKind, str],
        name: str,
        version: str,
        content: Union[bytes, str, Path],
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArtifactRecord:
        """
        Store content, compute sha256 hash, record lineage, and register metadata.
        """
        kind_enum = ArtifactKind(kind) if isinstance(kind, str) else kind
        parent_ids_list = parent_ids or []
        metadata_dict = metadata or {}

        # Resolve raw bytes and calculate sha256 hash
        if isinstance(content, Path):
            with open(content, "rb") as f:
                content_bytes = f.read()
        elif isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            raise TypeError(f"Unsupported content type: {type(content)}")

        sha256_hash = hashlib.sha256(content_bytes).hexdigest()
        artifact_id = f"{kind_enum.value}_{name}_{version}_{sha256_hash[:8]}"

        # Write to disk in structured directory
        dest_dir = self.storage_dir / kind_enum.value / name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{version}_{sha256_hash[:12]}.bin"
        dest_file.write_bytes(content_bytes)

        created_at = datetime.now(timezone.utc).isoformat()

        record = ArtifactRecord(
            id=artifact_id,
            kind=kind_enum,
            name=name,
            version=version,
            sha256=sha256_hash,
            created_at=created_at,
            parent_ids=parent_ids_list,
            metadata=metadata_dict,
            storage_path=str(dest_file)
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts (
                    id, kind, name, version, sha256, created_at, parent_ids, metadata, storage_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.id,
                    record.kind.value,
                    record.name,
                    record.version,
                    record.sha256,
                    record.created_at,
                    json.dumps(record.parent_ids),
                    json.dumps(record.metadata),
                    record.storage_path
                )
            )

        return record

    def load_artifact(self, kind: Union[ArtifactKind, str], name: str, version: str) -> Optional[ArtifactRecord]:
        """Load artifact metadata by kind, name, and version."""
        kind_str = kind.value if isinstance(kind, ArtifactKind) else str(kind)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM artifacts WHERE kind = ? AND name = ? AND version = ? ORDER BY created_at DESC LIMIT 1;",
                (kind_str, name, version)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def load_artifact_by_id(self, artifact_id: str) -> Optional[ArtifactRecord]:
        """Load artifact metadata by artifact ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM artifacts WHERE id = ?;", (artifact_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def load_content(self, artifact: ArtifactRecord) -> bytes:
        """Load the exact raw bytes for an artifact from disk storage."""
        path = Path(artifact.storage_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifact content file missing at: {path}")
        return path.read_bytes()

    def get_lineage(self, artifact_id: str) -> List[ArtifactRecord]:
        """
        Retrieve complete ancestral lineage for an artifact ordered from oldest ancestor to target.
        """
        target = self.load_artifact_by_id(artifact_id)
        if not target:
            return []

        lineage: List[ArtifactRecord] = []
        visited = set()
        queue = [target]

        while queue:
            current = queue.pop(0)
            if current.id in visited:
                continue
            visited.add(current.id)
            lineage.append(current)

            for parent_id in current.parent_ids:
                if parent_id not in visited:
                    parent = self.load_artifact_by_id(parent_id)
                    if parent:
                        queue.append(parent)

        # Return ancestor-first order
        lineage.reverse()
        return lineage

    def _row_to_record(self, row: sqlite3.Row) -> ArtifactRecord:
        return ArtifactRecord(
            id=row["id"],
            kind=ArtifactKind(row["kind"]),
            name=row["name"],
            version=row["version"],
            sha256=row["sha256"],
            created_at=row["created_at"],
            parent_ids=json.loads(row["parent_ids"]),
            metadata=json.loads(row["metadata"]),
            storage_path=row["storage_path"]
        )


_default_registry: Optional[ArtifactRegistry] = None


def get_artifact_registry() -> ArtifactRegistry:
    """Singleton getter for default artifact registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ArtifactRegistry()
    return _default_registry
