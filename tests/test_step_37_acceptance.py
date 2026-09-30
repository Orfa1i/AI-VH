"""
Acceptance criteria tests for STEP 37 (P6.2):
Review API with overlap sampling.

Criteria (from plan/prompts/phase-6-feedback/STEP-37_P6.2_review-api.md):
1. Contract and authorisation tests (non-reviewers blocked; an overlap
   reviewer cannot see the other review).
2. Overlap fraction within tolerance over 1,000 simulated assignments.
Plus: flagged-first queue, full decision lifecycle, taxonomy validation.
"""

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from vh.feedback.api import OVERLAP_TOLERANCE, create_app
from vh.feedback.models import FeedbackStore


def _headers(token: str) -> Dict[str, str]:
    return {"X-Reviewer-Token": token}


def _register(client: TestClient, name: str, role: str = "attending") -> Dict[str, Any]:
    resp = client.post("/reviewers/register", json={"name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _sample_report() -> Dict[str, Any]:
    return {
        "patient_summary": "62yo male with acute substernal pressure.",
        "differential": [{"dx": "Acute Anterior STEMI", "likelihood": "high"}],
        "recommendations": [{"text": "Aspirin 325 mg."}],
        "claims": [{"claim_id": "CLM-DX-01", "text": "ACS confirmed."}],
    }


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "api.db"))
    with TestClient(app) as test_client:
        yield test_client


def test_non_reviewers_blocked(client: TestClient):
    """Criterion 1: missing/unknown tokens -> 401; non-reviewer role -> 403."""
    # No token at all.
    assert client.get("/reviews/queue").status_code == 401
    # Unknown token.
    assert client.get("/reviews/queue", headers=_headers("nope")).status_code == 401
    # Valid token but non-reviewer role.
    viewer = _register(client, "Victor Viewer", role="viewer")
    assert client.get("/reviews/queue", headers=_headers(viewer["token"])).status_code == 403
    assert (
        client.post(
            "/reviews/sessions/ses_x/decision",
            json={"decision": "approve"},
            headers=_headers(viewer["token"]),
        ).status_code
        == 403
    )


def test_overlap_reviewer_cannot_see_other_review(client: TestClient):
    """Criterion 1: overlap reviewers are blind to each other's reviews."""
    rev_a = _register(client, "Dr. A")
    rev_b = _register(client, "Dr. B")
    ha = _headers(rev_a["token"])
    hb = _headers(rev_b["token"])

    # Seed one original directly through the app store and force overlap below
    # via the endpoint by requesting assignments for both reviewers.
    store: FeedbackStore = client.app.state.store
    original_id = store.store_original("CASE-OVL-001", _sample_report(), "m", "p@1")

    qa = client.get("/reviews/queue", headers=ha).json()
    qb = client.get("/reviews/queue", headers=hb).json()
    assert qa
    # Both reviewers land on the same single original. When the deterministic
    # overlap draw does not select this original, B's queue is legitimately
    # empty and overlap is forced explicitly for the blindness assertions below.
    if not qb or qa[0]["original_id"] != qb[0]["original_id"]:
        assignment = store.assign_review(original_id, rev_b["reviewer_id"])
        session_b_direct = store.start_session(assignment)
    else:
        started = client.post(f"/reviews/assignments/{qb[0]['assignment_id']}/start", headers=hb)
        assert started.status_code == 200, started.text
        session_b_direct = started.json()["session_id"]

    started_a = client.post(f"/reviews/assignments/{qa[0]['assignment_id']}/start", headers=ha)
    assert started_a.status_code == 200, started_a.text
    session_a = started_a.json()["session_id"]

    # Reviewer A works: edit + rating + comment + decision.
    assert client.post(
        f"/reviews/sessions/{session_a}/edits",
        json={"op": "replace", "path": ["patient_summary"], "value": "Updated summary."},
        headers=ha,
    ).status_code == 200
    assert client.post(
        f"/reviews/sessions/{session_a}/claims/CLM-DX-01/rating",
        json={"rating": "incorrect", "taxonomy_code": "wrong_diagnosis"},
        headers=ha,
    ).status_code == 200
    assert client.post(
        f"/reviews/sessions/{session_a}/comments",
        json={"text": "A's private note."},
        headers=ha,
    ).status_code == 200

    # Reviewer B must not see A's session, edits, ratings, or comments.
    assert client.get(f"/reviews/sessions/{session_a}", headers=hb).status_code == 404
    assert client.get(f"/reviews/sessions/{session_a}/edits", headers=hb).status_code == 404
    assert client.get(f"/reviews/sessions/{session_a}/comments", headers=hb).status_code == 404

    # B's own report view contains no trace of A's content.
    report_b = client.get(f"/reviews/reports/{original_id}", headers=hb)
    assert report_b.status_code == 200, report_b.text
    assert "Updated summary." not in report_b.text
    assert "A's private note." not in report_b.text

    # A's session is fully visible to A.
    assert client.get(f"/reviews/sessions/{session_a}", headers=ha).status_code == 200
    assert isinstance(session_b_direct, str)


def test_overlap_fraction_within_tolerance(tmp_path):
    """Criterion 2: ~overlap_fraction of 1,000 reports get two reviewers."""
    from vh.feedback.api import simulate_overlap_assignments

    result = simulate_overlap_assignments(
        db_path=str(tmp_path / "overlap.db"),
        n_reports=1000,
        n_reviewers=10,
        overlap_fraction=0.15,
        seed=7,
    )
    assert result["n_reports"] == 1000
    assert abs(result["overlap_fraction"] - 0.15) <= OVERLAP_TOLERANCE
    assert result["double_assigned"] > 0
    assert result["single_assigned"] > 0


def test_flagged_reports_first(client: TestClient):
    """Flagged reports head the review queue."""
    rev = _register(client, "Dr. Queue")
    headers = _headers(rev["token"])
    store: FeedbackStore = client.app.state.store

    plain_id = store.store_original("CASE-Q-PLAIN", _sample_report(), "m", "p@1")
    flagged_id = store.store_original(
        "CASE-Q-FLAGGED",
        _sample_report(),
        "m",
        "p@1",
        verification={"status": "flagged", "critical_count": 2},
    )

    queue = client.get("/reviews/queue", headers=headers).json()
    ids = [item["original_id"] for item in queue]
    assert flagged_id in ids and plain_id in ids
    assert ids.index(flagged_id) < ids.index(plain_id)


def _start_session_for(client: TestClient, headers: Dict[str, str], original_id: str) -> str:
    queue = client.get("/reviews/queue", headers=headers).json()
    item = next(i for i in queue if i["original_id"] == original_id)
    resp = client.post(f"/reviews/assignments/{item['assignment_id']}/start", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["session_id"]


def test_review_lifecycle_approve_correct_reject(client: TestClient):
    """Decisions: approve finalizes as-is; correct applies edits; reject closes."""
    rev = _register(client, "Dr. Life")
    headers = _headers(rev["token"])
    store: FeedbackStore = client.app.state.store

    # APPROVE path.
    oid_approve = store.store_original("CASE-L-APPROVE", _sample_report(), "m", "p@1")
    session = _start_session_for(client, headers, oid_approve)
    # Report view carries evidence (claims) and verification flags.
    report = client.get(f"/reviews/reports/{oid_approve}", headers=headers).json()
    assert report["claims"] and "verification" in report
    decision = client.post(
        f"/reviews/sessions/{session}/decision", json={"decision": "approve"}, headers=headers
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["final_report"] == _sample_report()

    # CORRECT path with edits.
    oid_correct = store.store_original("CASE-L-CORRECT", _sample_report(), "m", "p@1")
    session = _start_session_for(client, headers, oid_correct)
    decision = client.post(
        f"/reviews/sessions/{session}/decision",
        json={
            "decision": "correct",
            "edits": [{"op": "replace", "path": ["patient_summary"], "value": "Corrected."}],
        },
        headers=headers,
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["final_report"]["patient_summary"] == "Corrected."

    # REJECT path closes without a final report.
    oid_reject = store.store_original("CASE-L-REJECT", _sample_report(), "m", "p@1")
    session = _start_session_for(client, headers, oid_reject)
    decision = client.post(
        f"/reviews/sessions/{session}/decision",
        json={"decision": "reject", "comment": "Unsafe."},
        headers=headers,
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["final_report"] is None


def test_taxonomy_validation_on_ratings(client: TestClient):
    """Ratings validate rating value and taxonomy code (422 on violations)."""
    rev = _register(client, "Dr. Tax")
    headers = _headers(rev["token"])
    store: FeedbackStore = client.app.state.store
    oid = store.store_original("CASE-TAX-001", _sample_report(), "m", "p@1")
    session = _start_session_for(client, headers, oid)

    bad_code = client.post(
        f"/reviews/sessions/{session}/claims/CLM-DX-01/rating",
        json={"rating": "incorrect", "taxonomy_code": "not_a_code"},
        headers=headers,
    )
    assert bad_code.status_code == 422, bad_code.text

    bad_rating = client.post(
        f"/reviews/sessions/{session}/claims/CLM-DX-01/rating",
        json={"rating": "sort_of", "taxonomy_code": "wrong_diagnosis"},
        headers=headers,
    )
    assert bad_rating.status_code == 422, bad_rating.text

    good = client.post(
        f"/reviews/sessions/{session}/claims/CLM-DX-01/rating",
        json={"rating": "partially_correct", "taxonomy_code": "unsupported_claim"},
        headers=headers,
    )
    assert good.status_code == 200, good.text
