"""
Doctor review API with overlap sampling for AI-VH (STEP 37 / P6.2).

Reviewer-role authentication via per-reviewer tokens; flagged reports head the
queue; `review.overlap_fraction` of reports receive two independent reviewers
who cannot see each other's sessions, edits, ratings, or comments. All writes
land in the append-only `FeedbackStore` (STEP 36).
"""

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from vh.feedback.models import FeedbackStore, _taxonomy_codes

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

REVIEWER_ROLES = {"attending", "reviewer", "resident", "fellow"}

OVERLAP_TOLERANCE = 0.05
OVERLAP_SALT = "overlap-v1"


def selected_for_overlap(original_id: str, overlap_fraction: float) -> bool:
    """Deterministic overlap selection: stable hash draw per report."""
    if overlap_fraction <= 0.0:
        return False
    if overlap_fraction >= 1.0:
        return True
    draw = int(hashlib.sha256(f"{OVERLAP_SALT}:{original_id}".encode("utf-8")).hexdigest(), 16)
    return (draw % 10000) < int(overlap_fraction * 10000)


def required_reviewers(original_id: str, overlap_fraction: float) -> int:
    return 2 if selected_for_overlap(original_id, overlap_fraction) else 1


# --- Request / response models ---


class RegisterReviewerRequest(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)


class StartSessionResponse(BaseModel):
    session_id: str


class AddEditRequest(BaseModel):
    op: Literal["replace", "add", "remove"]
    path: List[Any]
    value: Optional[Any] = None


class RateClaimRequest(BaseModel):
    rating: Literal["correct", "partially_correct", "incorrect"]
    taxonomy_code: str

    @field_validator("taxonomy_code")
    @classmethod
    def _known_taxonomy_code(cls, value: str) -> str:
        if value not in _taxonomy_codes():
            raise ValueError(f"Unknown taxonomy code: {value!r}")
        return value


class AddCommentRequest(BaseModel):
    text: str = Field(min_length=1)


class DecisionRequest(BaseModel):
    decision: Literal["approve", "correct", "reject"]
    edits: List[AddEditRequest] = Field(default_factory=list)
    comment: Optional[str] = None


# --- Application factory ---


def create_app(db_path: str, overlap_fraction: float = 0.15) -> FastAPI:
    store = FeedbackStore(db_path=db_path)
    app = FastAPI(title="AI-VH Doctor Review API")
    app.state.store = store
    app.state.overlap_fraction = overlap_fraction

    def get_store() -> FeedbackStore:
        return app.state.store

    def current_reviewer(
        x_reviewer_token: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        if not x_reviewer_token:
            raise HTTPException(status_code=401, detail="Missing reviewer token.")
        reviewer = get_store().authenticate(x_reviewer_token)
        if reviewer is None:
            raise HTTPException(status_code=401, detail="Unknown reviewer token.")
        if reviewer.get("role") not in REVIEWER_ROLES:
            raise HTTPException(status_code=403, detail="Reviewer role required.")
        return reviewer

    def own_session_or_404(session_id: str, reviewer_id: str) -> Dict[str, Any]:
        store = get_store()
        try:
            session = store.get_session(session_id)
            assignment = store.get_assignment(session["assignment_id"])
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found.")
        if assignment["reviewer_id"] != reviewer_id:
            # Blindness: another reviewer's session is indistinguishable from nonexistent.
            raise HTTPException(status_code=404, detail="Session not found.")
        return session

    @app.post("/reviewers/register")
    def register_reviewer(body: RegisterReviewerRequest) -> Dict[str, str]:
        reviewer_id, token = get_store().register_reviewer(body.name, body.role)
        return {"reviewer_id": reviewer_id, "token": token}

    @app.get("/reviews/queue")
    def review_queue(reviewer: Dict[str, Any] = Depends(current_reviewer)) -> List[Dict[str, Any]]:
        """Open assignments first (flagged first), then claim newly assignable reports."""
        store = get_store()
        seen = {a["original_id"] for a in store.open_assignments_for(reviewer["id"])}
        for original in _assignable_originals(store, reviewer["id"], app.state.overlap_fraction):
            if original["id"] in seen:
                continue
            store.assign_review(original["id"], reviewer["id"])
            seen.add(original["id"])
        return [
            {
                "assignment_id": a["id"],
                "original_id": a["original_id"],
                "case_id": a["case_id"],
                "flagged": bool(a["flagged"]),
                "status": a["status"],
            }
            for a in store.open_assignments_for(reviewer["id"])
        ]

    @app.post("/reviews/assignments/{assignment_id}/start", response_model=StartSessionResponse)
    def start_assignment_session(
        assignment_id: str, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> StartSessionResponse:
        store = get_store()
        try:
            assignment = store.get_assignment(assignment_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Assignment not found.")
        if assignment["reviewer_id"] != reviewer["id"]:
            raise HTTPException(status_code=404, detail="Assignment not found.")
        existing = [
            dict(r)
            for r in store._conn.execute(
                "SELECT * FROM review_sessions WHERE assignment_id = ? AND decision IS NULL",
                (assignment_id,),
            ).fetchall()
        ]
        if existing:
            return StartSessionResponse(session_id=existing[0]["id"])
        return StartSessionResponse(session_id=store.start_session(assignment_id))

    @app.get("/reviews/reports/{original_id}")
    def get_report(
        original_id: str, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> Dict[str, Any]:
        store = get_store()
        if not store.reviewer_has_assignment(reviewer["id"], original_id):
            raise HTTPException(status_code=403, detail="No assignment for this report.")
        try:
            original = store.get_original(original_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Report not found.")
        report = json.loads(original["report_json"])
        verification = json.loads(original.get("verification_json") or "{}")
        return {
            "original_id": original_id,
            "case_id": original["case_id"],
            "report": report,
            "claims": report.get("claims", []),
            "verification": verification,
            "flagged": bool(original.get("flagged")),
        }

    @app.get("/reviews/sessions/{session_id}")
    def get_session(
        session_id: str, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> Dict[str, Any]:
        session = own_session_or_404(session_id, reviewer["id"])
        store = get_store()
        return {
            "session": session,
            "edits": store.get_edits(session_id),
            "claim_ratings": store.claim_ratings_for(session_id),
            "comments": store.comments_for(session_id),
        }

    @app.get("/reviews/sessions/{session_id}/edits")
    def get_session_edits(
        session_id: str, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> List[Dict[str, Any]]:
        own_session_or_404(session_id, reviewer["id"])
        return get_store().get_edits(session_id)

    @app.get("/reviews/sessions/{session_id}/comments")
    def get_session_comments(
        session_id: str, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> List[Dict[str, Any]]:
        own_session_or_404(session_id, reviewer["id"])
        return get_store().comments_for(session_id)

    @app.post("/reviews/sessions/{session_id}/edits")
    def add_session_edit(
        session_id: str, body: AddEditRequest, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> Dict[str, int]:
        own_session_or_404(session_id, reviewer["id"])
        edit_id = get_store().add_edit(
            session_id, body.op, body.path, body.value, actor=reviewer["id"]
        )
        return {"edit_id": edit_id}

    @app.post("/reviews/sessions/{session_id}/claims/{claim_id}/rating")
    def rate_session_claim(
        session_id: str,
        claim_id: str,
        body: RateClaimRequest,
        reviewer: Dict[str, Any] = Depends(current_reviewer),
    ) -> Dict[str, int]:
        own_session_or_404(session_id, reviewer["id"])
        rating_id = get_store().rate_claim(
            session_id, claim_id, body.rating, body.taxonomy_code, actor=reviewer["id"]
        )
        return {"rating_id": rating_id}

    @app.post("/reviews/sessions/{session_id}/comments")
    def add_session_comment(
        session_id: str, body: AddCommentRequest, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> Dict[str, int]:
        own_session_or_404(session_id, reviewer["id"])
        comment_id = get_store().add_comment(session_id, reviewer["id"], body.text)
        return {"comment_id": comment_id}

    @app.post("/reviews/sessions/{session_id}/decision")
    def submit_decision(
        session_id: str, body: DecisionRequest, reviewer: Dict[str, Any] = Depends(current_reviewer)
    ) -> Dict[str, Any]:
        own_session_or_404(session_id, reviewer["id"])
        store = get_store()
        try:
            if body.decision == "reject":
                if body.comment:
                    store.add_comment(session_id, reviewer["id"], body.comment)
                store.record_decision(session_id, "reject", actor=reviewer["id"])
                return {"decision": "reject", "final_report": None}
            for edit in body.edits:
                store.add_edit(session_id, edit.op, edit.path, edit.value, actor=reviewer["id"])
            final_id = store.finalize_report(
                session_id, actor=reviewer["id"], decision=body.decision
            )
            final_report = json.loads(store.get_final(final_id)["report_json"])
            return {"decision": body.decision, "final_report": final_report}
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    return app


def _assignable_originals(
    store: FeedbackStore, reviewer_id: str, overlap_fraction: float
) -> List[Dict[str, Any]]:
    """Originals the reviewer may newly claim: quota unmet, flagged first."""
    rows = store._conn.execute(
        "SELECT o.*, COUNT(a.id) AS assigned_count FROM reports_original o"
        " LEFT JOIN review_assignments a ON a.original_id = o.id"
        " GROUP BY o.id ORDER BY o.flagged DESC, o.created_at ASC"
    ).fetchall()
    eligible: List[Dict[str, Any]] = []
    for row in rows:
        original = dict(row)
        if store.reviewer_has_assignment(reviewer_id, original["id"]):
            continue
        if int(original["assigned_count"]) >= required_reviewers(original["id"], overlap_fraction):
            continue
        eligible.append(original)
    return eligible


def simulate_overlap_assignments(
    db_path: str,
    n_reports: int = 1000,
    n_reviewers: int = 10,
    overlap_fraction: float = 0.15,
    seed: int = 7,
) -> Dict[str, Any]:
    """Simulate queue assignment over many reports; measure the overlap fraction."""
    store = FeedbackStore(db_path=db_path)
    try:
        reviewer_ids = [
            store.register_reviewer(f"Sim Reviewer {i}", "attending")[0] for i in range(n_reviewers)
        ]
        original_ids = [
            store.store_original(
                f"CASE-SIM-{i:04d}", {"summary": f"report {i}"}, "m", "p@1"
            )
            for i in range(n_reports)
        ]
        rng = random.Random(seed)
        order = reviewer_ids[:]
        progress = True
        while progress:
            progress = False
            rng.shuffle(order)
            for reviewer_id in order:
                for original in _assignable_originals(store, reviewer_id, overlap_fraction):
                    store.assign_review(original["id"], reviewer_id)
                    progress = True
                    break
        double = sum(1 for oid in original_ids if len(store.assignments_for_original(oid)) >= 2)
        single = sum(1 for oid in original_ids if len(store.assignments_for_original(oid)) == 1)
        return {
            "n_reports": n_reports,
            "double_assigned": double,
            "single_assigned": single,
            "overlap_fraction": (double / n_reports) if n_reports else 0.0,
        }
    finally:
        store.close()
