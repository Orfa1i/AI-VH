"""
Accumulation bridge for the approved automated-review track: encounter
reports flow into the feedback store as immutable originals, are evaluated
by the independent evaluator, and countable decisions persist with full
provenance. Rejects persist as reviews without targets and never count.
"""

from typing import Any, Dict

from vh.agents.orchestrator import EncounterState, EncounterStatus
from vh.cases.spec import CaseSpec
from vh.feedback.models import FeedbackStore
from vh.training.auto_review import AutomatedEvaluator
from vh.training.curation import COUNTABLE_DECISIONS


def ingest_encounter_report(
    store: FeedbackStore, state: EncounterState, case_spec: CaseSpec
) -> str:
    """Store a terminal COMPLETED encounter report as an immutable original.

    Raw report is preserved byte-faithfully (including any generator
    self-assessment fields); sanitization happens at evaluation time.
    """
    if state.status != EncounterStatus.COMPLETED:
        raise ValueError(
            f"Only COMPLETED encounters enter the store, got {state.status}."
        )
    report = state.report
    if not isinstance(report, dict) or not report:
        raise ValueError("Encounter carries no report to ingest.")
    provenance = report.get("provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}
    verification = state.verification
    if not isinstance(verification, dict):
        verification = {}
    return store.store_original(
        case_id=state.case_id,
        report=report,
        model_id=str(provenance.get("model_id", "unknown")),
        prompt_version=str(provenance.get("prompt_name_version", "unknown")),
        verification=verification,
    )


def evaluate_and_persist(
    store: FeedbackStore,
    evaluator: AutomatedEvaluator,
    original_id: str,
    state: EncounterState,
    case_spec: CaseSpec,
    evidence: Dict[str, str],
    ground_truth_source: str = "physician-verified-golden-v1",
    ground_truth_version: str = "v1",
    reviewer_id: str = "auto-validator/v1",
) -> str:
    """Evaluate one ingested encounter and persist review (+target on pass)."""
    _ = original_id  # linkage: state.case_id identifies the original row.
    review = evaluator.evaluate(
        state,
        case_spec,
        evidence,
        ground_truth_source=ground_truth_source,
        ground_truth_version=ground_truth_version,
        reviewer_id=reviewer_id,
    )
    record = {
        "case_id": state.case_id,
        "patient_ref": case_spec.patient_ref,
        "original_report": state.report or {},
        "ground_truth_source": ground_truth_source,
        "ground_truth_version": ground_truth_version,
        "validator_versions": review.provenance.get("validator_versions", {}),
        "metrics": review.provenance.get("metrics", {}),
        "decision": review.decision,
        "reasons": review.reasons,
        "sanitized_removed": review.sanitized_removed,
        "reviewer_id": reviewer_id,
        "evaluated_at": review.evaluated_at,
    }
    review_id = store.create_automated_review(record)
    if review.decision in COUNTABLE_DECISIONS and review.target is not None:
        store.create_automated_target(
            review_id,
            review.target,
            "as-is" if review.decision == "approve" else "repaired",
            review.repair_ops,
            review.revalidation_pass,
            reviewer_id,
        )
    return review_id


def count_live_patients(store: FeedbackStore) -> int:
    """Distinct patients with a passing decision and a revalidated target."""
    targets = {t["review_id"]: t for t in store.list_automated_targets()}
    seen = set()
    for review in store.list_automated_reviews():
        if review.get("decision") not in COUNTABLE_DECISIONS:
            continue
        target = targets.get(review["id"])
        if target is None or not target.get("revalidation_pass"):
            continue
        patient_ref = str(review.get("patient_ref", "") or "").strip()
        if not patient_ref:
            continue
        seen.add(patient_ref)
    return len(seen)
