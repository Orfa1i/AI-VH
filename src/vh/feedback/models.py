"""
Append-only doctor-review feedback data model for AI-VH (STEP 36 / P6.1).

The AI's original report is immutable: stored once in `reports_original`
(UPDATE/DELETE denied by database triggers) and never overwritten. Doctor
corrections are stored as structured edit operations; the final report is
reproduced deterministically by applying those edits to the original.
Every write appends exactly one `audit_log` row.
"""

import copy
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field

from vh.feedback.migrations import apply_migrations

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TAXONOMY_PATH = REPO_ROOT / "configs" / "feedback" / "taxonomy.yaml"

VALID_OPS = {"replace", "add", "remove"}
VALID_RATINGS = {"correct", "partially_correct", "incorrect"}

PathLike = Union[str, int]
EditPath = List[PathLike]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _taxonomy_codes() -> set[str]:
    data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    return {str(item["code"]) for item in data.get("error_types", [])}


class Reviewer(BaseModel):
    id: str
    name: str
    role: str
    created_at: str


class OriginalReport(BaseModel):
    id: str
    case_id: str
    report: Dict[str, Any]
    model_id: str
    prompt_version: str
    created_at: str


class EditOperation(BaseModel):
    op: str
    path: EditPath
    value: Optional[Any] = None


class ClaimRating(BaseModel):
    id: int
    session_id: str
    claim_id: str
    rating: str
    taxonomy_code: str
    created_at: str


class AuditEntry(BaseModel):
    id: int
    action: str
    actor: str
    entity: str
    entity_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


def _navigate(doc: Any, path: EditPath) -> Any:
    node = doc
    for key in path:
        if isinstance(node, dict) and isinstance(key, str):
            if key not in node:
                raise KeyError(f"Edit path not found: {path}")
            node = node[key]
        elif isinstance(node, list) and isinstance(key, int):
            if key < 0 or key >= len(node):
                raise IndexError(f"Edit path index out of range: {path}")
            node = node[key]
        else:
            raise TypeError(f"Edit path traverses a scalar at {key!r} in {path}")
    return node


def apply_edits(original: Dict[str, Any], edits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply structured edit operations to a copy of the original report.

    Ops: replace (path must exist), add (new dict key or list insert index),
    remove (path must exist). Atomic per call: any invalid op raises and the
    input is never partially mutated (callers pass copies; the original arg
    itself is never modified).
    """
    result = copy.deepcopy(original)
    for raw in edits:
        op = EditOperation.model_validate(raw)
        if op.op not in VALID_OPS:
            raise ValueError(f"Unknown edit op: {op.op!r}")
        if not op.path:
            raise ValueError("Edit path must not be empty.")
        parent = _navigate(result, op.path[:-1]) if len(op.path) > 1 else result
        last = op.path[-1]
        if op.op == "replace":
            if isinstance(parent, dict) and isinstance(last, str):
                if last not in parent:
                    raise KeyError(f"Replace target missing: {op.path}")
                parent[last] = copy.deepcopy(op.value)
            elif isinstance(parent, list) and isinstance(last, int):
                if last < 0 or last >= len(parent):
                    raise IndexError(f"Replace index out of range: {op.path}")
                parent[last] = copy.deepcopy(op.value)
            else:
                raise TypeError(f"Cannot replace at path: {op.path}")
        elif op.op == "add":
            if isinstance(parent, dict) and isinstance(last, str):
                parent[last] = copy.deepcopy(op.value)
            elif isinstance(parent, list) and isinstance(last, int):
                if last < 0 or last > len(parent):
                    raise IndexError(f"Add index out of range: {op.path}")
                parent.insert(last, copy.deepcopy(op.value))
            else:
                raise TypeError(f"Cannot add at path: {op.path}")
        else:  # remove
            if isinstance(parent, dict) and isinstance(last, str):
                if last not in parent:
                    raise KeyError(f"Remove target missing: {op.path}")
                del parent[last]
            elif isinstance(parent, list) and isinstance(last, int):
                if last < 0 or last >= len(parent):
                    raise IndexError(f"Remove index out of range: {op.path}")
                parent.pop(last)
            else:
                raise TypeError(f"Cannot remove at path: {op.path}")
    return result


class FeedbackStore:
    """SQLite-backed append-only feedback store with trigger-level immutability."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        apply_migrations(db_path)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def _audit(self, action: str, actor: str, entity: str, entity_id: str) -> None:
        self._conn.execute(
            "INSERT INTO audit_log (action, actor, entity, entity_id, details_json, created_at)"
            " VALUES (?, ?, ?, ?, '{}', ?)",
            (action, actor, entity, entity_id, _utcnow()),
        )
        self._conn.commit()

    def add_reviewer(self, reviewer_id: str, name: str, role: str) -> str:
        self._conn.execute(
            "INSERT INTO reviewers (id, name, role, created_at) VALUES (?, ?, ?, ?)",
            (reviewer_id, name, role, _utcnow()),
        )
        self._audit("reviewer_added", "system", "reviewers", reviewer_id)
        return reviewer_id

    def store_original(
        self,
        case_id: str,
        report: Dict[str, Any],
        model_id: str,
        prompt_version: str,
    ) -> str:
        original_id = _new_id("rep")
        self._conn.execute(
            "INSERT INTO reports_original (id, case_id, report_json, model_id,"
            " prompt_version, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                original_id,
                case_id,
                json.dumps(report, sort_keys=True),
                model_id,
                prompt_version,
                _utcnow(),
            ),
        )
        self._audit("original_stored", "system", "reports_original", original_id)
        return original_id

    def assign_review(self, original_id: str, reviewer_id: str) -> str:
        assignment_id = _new_id("asg")
        self._conn.execute(
            "INSERT INTO review_assignments (id, original_id, reviewer_id, status, created_at)"
            " VALUES (?, ?, ?, 'assigned', ?)",
            (assignment_id, original_id, reviewer_id, _utcnow()),
        )
        self._audit("review_assigned", "system", "review_assignments", assignment_id)
        return assignment_id

    def start_session(self, assignment_id: str) -> str:
        session_id = _new_id("ses")
        self._conn.execute(
            "INSERT INTO review_sessions (id, assignment_id, started_at, ended_at)"
            " VALUES (?, ?, ?, NULL)",
            (session_id, assignment_id, _utcnow()),
        )
        self._audit("session_started", "system", "review_sessions", session_id)
        return session_id

    def add_edit(
        self,
        session_id: str,
        op: str,
        path: EditPath,
        value: Optional[Any] = None,
        actor: str = "doctor",
    ) -> int:
        if op not in VALID_OPS:
            raise ValueError(f"Unknown edit op: {op!r}")
        row = self._conn.execute(
            "SELECT COALESCE(MAX(seq), -1) FROM edits WHERE session_id = ?", (session_id,)
        ).fetchone()
        seq = int(row[0]) + 1
        cursor = self._conn.execute(
            "INSERT INTO edits (session_id, seq, op, path_json, value_json, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                seq,
                op,
                json.dumps(list(path)),
                json.dumps(value) if value is not None else None,
                _utcnow(),
            ),
        )
        self._audit("edit_added", actor, "edits", str(cursor.lastrowid))
        return int(cursor.lastrowid or 0)

    def rate_claim(
        self,
        session_id: str,
        claim_id: str,
        rating: str,
        taxonomy_code: str,
        actor: str = "doctor",
    ) -> int:
        if rating not in VALID_RATINGS:
            raise ValueError(f"Unknown claim rating: {rating!r}")
        if taxonomy_code not in _taxonomy_codes():
            raise ValueError(f"Unknown taxonomy code: {taxonomy_code!r}")
        cursor = self._conn.execute(
            "INSERT INTO claim_ratings (session_id, claim_id, rating, taxonomy_code, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (session_id, claim_id, rating, taxonomy_code, _utcnow()),
        )
        self._audit("claim_rated", actor, "claim_ratings", str(cursor.lastrowid))
        return int(cursor.lastrowid or 0)

    def add_comment(self, session_id: str, author: str, text: str) -> int:
        cursor = self._conn.execute(
            "INSERT INTO comments (session_id, author, text, created_at) VALUES (?, ?, ?, ?)",
            (session_id, author, text, _utcnow()),
        )
        self._audit("comment_added", author, "comments", str(cursor.lastrowid))
        return int(cursor.lastrowid or 0)

    def get_edits(self, session_id: str) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT op, path_json, value_json FROM edits WHERE session_id = ? ORDER BY seq",
            (session_id,),
        ).fetchall()
        edits: List[Dict[str, Any]] = []
        for row in rows:
            edit: Dict[str, Any] = {"op": row["op"], "path": json.loads(row["path_json"])}
            if row["value_json"] is not None:
                edit["value"] = json.loads(row["value_json"])
            edits.append(edit)
        return edits

    def get_original(self, original_id: str) -> Dict[str, Any]:
        row = self._conn.execute(
            "SELECT * FROM reports_original WHERE id = ?", (original_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Original report not found: {original_id}")
        return dict(row)

    def get_final(self, final_id: str) -> Dict[str, Any]:
        row = self._conn.execute(
            "SELECT * FROM final_reports WHERE id = ?", (final_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Final report not found: {final_id}")
        return dict(row)

    def finalize_report(self, session_id: str, actor: str = "doctor") -> str:
        session = self._conn.execute(
            "SELECT assignment_id FROM review_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise KeyError(f"Review session not found: {session_id}")
        assignment = self._conn.execute(
            "SELECT original_id FROM review_assignments WHERE id = ?",
            (session["assignment_id"],),
        ).fetchone()
        if assignment is None:
            raise KeyError(f"Review assignment not found: {session['assignment_id']}")
        original = json.loads(self.get_original(assignment["original_id"])["report_json"])
        final_doc = apply_edits(original, self.get_edits(session_id))
        final_id = _new_id("fin")
        self._conn.execute(
            "INSERT INTO final_reports (id, session_id, report_json, created_at)"
            " VALUES (?, ?, ?, ?)",
            (final_id, session_id, json.dumps(final_doc, sort_keys=True), _utcnow()),
        )
        self._audit("report_finalized", actor, "final_reports", final_id)
        return final_id

    def audit_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()
        return int(row[0])

    def list_audit(self) -> List[Dict[str, Any]]:
        return [
            dict(r) for r in self._conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
        ]
