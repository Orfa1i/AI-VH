"""
Acceptance criteria tests for STEP 36 (P6.1):
Feedback data model (append-only).

Criteria (from plan/prompts/phase-6-feedback/STEP-36_P6.1_feedback-data-model.md):
1. A direct SQL update of an original report fails.
2. Applying the stored edits to the original reproduces the final report
   exactly (property test).
3. Every write produces an audit_log row.
Plus: taxonomy config carries all required codes; migrations apply cleanly.
"""

import copy
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from hypothesis import HealthCheck, given, settings, strategies as st

from vh.feedback.migrations import MIGRATIONS, apply_migrations
from vh.feedback.models import FeedbackStore, apply_edits

REPO_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = REPO_ROOT / "configs" / "feedback" / "taxonomy.yaml"

REQUIRED_TAXONOMY_CODES = {
    "wrong_diagnosis",
    "missed_diagnosis",
    "missed_red_flag",
    "bad_citation",
    "unsupported_claim",
    "unsafe_recommendation",
    "dosing_error",
    "formatting",
    "other",
}

TABLES = {
    "reports_original",
    "review_assignments",
    "review_sessions",
    "edits",
    "claim_ratings",
    "final_reports",
    "comments",
    "reviewers",
    "audit_log",
}


@pytest.fixture
def store(tmp_path: Path) -> FeedbackStore:
    db = FeedbackStore(db_path=str(tmp_path / "feedback.db"))
    yield db
    db.close()


def _sample_original() -> Dict[str, Any]:
    return {
        "patient_summary": "62yo male with acute substernal pressure.",
        "differential": [
            {"dx": "Non-ST-Elevation Myocardial Infarction", "likelihood": "high"},
            {"dx": "Unstable Angina Pectoris", "likelihood": "moderate"},
        ],
        "recommendations": [{"text": "Aspirin 325 mg."}],
        "claims": [{"claim_id": "CLM-DX-01", "text": "ACS confirmed."}],
    }


def _sample_edits() -> List[Dict[str, Any]]:
    return [
        {
            "op": "replace",
            "path": ["differential", 0, "dx"],
            "value": "Acute Anterior STEMI",
        },
        {
            "op": "add",
            "path": ["recommendations", 1],
            "value": {"text": "Emergent angiography."},
        },
        {"op": "remove", "path": ["claims", 0]},
    ]


def _expected_final() -> Dict[str, Any]:
    final = _sample_original()
    final["differential"][0]["dx"] = "Acute Anterior STEMI"
    final["recommendations"].append({"text": "Emergent angiography."})
    final["claims"] = []
    return final


def test_direct_sql_update_of_original_fails(store: FeedbackStore, tmp_path: Path):
    """Criterion 1: DB-level triggers deny UPDATE/DELETE on immutable tables."""
    original_id = store.store_original(
        case_id="CASE-FB-001",
        report=_sample_original(),
        model_id="google/medgemma-4b",
        prompt_version="clinical_report@1.0.0",
    )

    conn = sqlite3.connect(str(tmp_path / "feedback.db"))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE reports_original SET report_json = '{}' WHERE id = ?",
                (original_id,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM reports_original WHERE id = ?", (original_id,))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE audit_log SET action = 'tampered' WHERE id = 1")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM audit_log WHERE id = 1")
    finally:
        conn.close()

    # Original row is untouched.
    assert json.loads(store.get_original(original_id)["report_json"]) == _sample_original()


def test_edits_reproduce_final_exactly(store: FeedbackStore):
    """Criterion 2 (hand-built): stored edits applied to the original equal final."""
    assert apply_edits(_sample_original(), _sample_edits()) == _expected_final()

    reviewer = store.add_reviewer("rev-001", "Dr. Reviewer", "attending")
    original_id = store.store_original("CASE-FB-001", _sample_original(), "m", "p@1")
    assignment = store.assign_review(original_id, reviewer)
    session = store.start_session(assignment)
    for edit in _sample_edits():
        store.add_edit(session, edit["op"], edit["path"], edit.get("value"))
    final_id = store.finalize_report(session)

    stored_final = json.loads(store.get_final(final_id)["report_json"])
    assert stored_final == _expected_final()
    # Original remains pristine.
    assert json.loads(store.get_original(original_id)["report_json"]) == _sample_original()


def _collect_paths(doc: Any, prefix: List[Any] = []) -> List[List[Any]]:
    paths = [list(prefix)]
    if isinstance(doc, dict):
        for key, val in doc.items():
            paths.extend(_collect_paths(val, prefix + [key]))
    elif isinstance(doc, list):
        for idx, val in enumerate(doc):
            paths.extend(_collect_paths(val, prefix + [idx]))
    return paths


def _test_side_set(doc: Dict[str, Any], path: List[Any], value: Any) -> None:
    """Independent test-side setter (separate code path from apply_edits)."""
    node = doc
    for key in path[:-1]:
        node = node[key]
    last = path[-1]
    node[last] = value


def _test_side_walk(doc: Any, path: List[Any]) -> None:
    """Strict test-side path validation with dict-str / list-int discipline."""
    node = doc
    for key in path:
        if isinstance(node, dict) and isinstance(key, str) and key in node:
            node = node[key]
        elif isinstance(node, list) and isinstance(key, int) and 0 <= key < len(node):
            node = node[key]
        else:
            raise KeyError(f"invalid at {key!r} in {path}")
    return node


json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(max_size=8),
    lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=6), children, max_size=3),
    max_leaves=8,
)


@given(doc=json_values)
@settings(max_examples=50, suppress_health_check=list(HealthCheck), deadline=None)
def test_edits_property_based(doc: Any):
    """Criterion 2 (property): replace-ops applied by apply_edits match an
    independent reference application, deterministically, on any JSON doc."""
    if not isinstance(doc, (dict, list)):
        doc = {"root": doc}
    original = copy.deepcopy(doc)
    existing = [p for p in _collect_paths(doc) if len(p) > 0][:5]
    if not existing:
        assert apply_edits(copy.deepcopy(doc), []) == doc
        return

    ops = []
    expected = copy.deepcopy(doc)
    for path in existing:
        value = {"edited": True}
        # Validate against the CURRENT expected doc: earlier ops may have
        # reshaped it, invalidating later paths on both code paths alike.
        try:
            _test_side_walk(expected, path)
        except (KeyError, IndexError, TypeError):
            continue
        ops.append({"op": "replace", "path": path, "value": value})
        _test_side_set(expected, path, copy.deepcopy(value))

    result = apply_edits(copy.deepcopy(doc), ops)
    assert result == expected
    # Pure function: original input untouched, repeated application identical.
    assert doc == original
    assert apply_edits(copy.deepcopy(doc), ops) == expected


def test_invalid_edit_raises_without_partial_application():
    """Invalid edit paths fail closed with no partial mutation."""
    original = _sample_original()
    snapshot = copy.deepcopy(original)
    with pytest.raises((KeyError, IndexError, TypeError, ValueError)):
        apply_edits(original, [{"op": "replace", "path": ["nope", 99], "value": 1}])
    assert original == snapshot


def test_every_write_produces_audit_row(store: FeedbackStore):
    """Criterion 3: each store write appends exactly one audit_log row."""
    assert store.audit_count() == 0

    reviewer = store.add_reviewer("rev-001", "Dr. Reviewer", "attending")
    assert store.audit_count() == 1
    original_id = store.store_original("CASE-FB-001", _sample_original(), "m", "p@1")
    assert store.audit_count() == 2
    assignment = store.assign_review(original_id, reviewer)
    assert store.audit_count() == 3
    session = store.start_session(assignment)
    assert store.audit_count() == 4
    store.add_edit(session, "replace", ["differential", 0, "dx"], "X")
    assert store.audit_count() == 5
    store.rate_claim(session, "CLM-DX-01", "incorrect", "wrong_diagnosis")
    assert store.audit_count() == 6
    store.add_comment(session, reviewer, "Needs rework.")
    assert store.audit_count() == 7
    store.finalize_report(session)
    assert store.audit_count() == 8

    actions = [row["action"] for row in store.list_audit()]
    assert actions == [
        "reviewer_added",
        "original_stored",
        "review_assigned",
        "session_started",
        "edit_added",
        "claim_rated",
        "comment_added",
        "report_finalized",
    ]


def test_taxonomy_has_required_codes():
    """Taxonomy config carries every required error code."""
    data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    codes = {item["code"] for item in data.get("error_types", [])}
    assert REQUIRED_TAXONOMY_CODES.issubset(codes), f"Missing: {REQUIRED_TAXONOMY_CODES - codes}"
    assert str(data.get("version", "")).strip() != ""


def test_claim_rating_rejects_unknown_taxonomy(store: FeedbackStore):
    """Ratings with codes outside the taxonomy are refused."""
    reviewer = store.add_reviewer("rev-001", "Dr. Reviewer", "attending")
    original_id = store.store_original("CASE-FB-001", _sample_original(), "m", "p@1")
    session = store.start_session(store.assign_review(original_id, reviewer))
    with pytest.raises(ValueError):
        store.rate_claim(session, "CLM-DX-01", "incorrect", "not_a_real_code")


def test_migrations_apply_cleanly(tmp_path: Path):
    """Migrations build all tables + immutability triggers, idempotently."""
    assert len(MIGRATIONS) >= 1
    db_path = str(tmp_path / "mig.db")
    apply_migrations(db_path)
    apply_migrations(db_path)  # idempotent re-run

    conn = sqlite3.connect(db_path)
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert TABLES.issubset(tables), f"Missing tables: {TABLES - tables}"
        triggers = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        assert triggers, "Immutability triggers must exist"
    finally:
        conn.close()
