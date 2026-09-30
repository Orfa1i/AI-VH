"""
Tests for the accumulation bridge (encounter -> feedback store -> automated
evaluation -> countable reviews). No fabrication: every persisted row carries
its provenance; evidence gaps fail closed to reject.
"""

from typing import Any, Dict

import pytest

from vh.agents.orchestrator import EncounterState, EncounterStatus, EncounterStep
from vh.cases.spec import CaseSpec, GroundTruth, HiddenResult, VisiblePresentation
from vh.feedback.models import FeedbackStore
from vh.training.accumulate import (
    count_live_patients,
    evaluate_and_persist,
    ingest_encounter_report,
)
from vh.training.auto_review import AutomatedEvaluator


def _make_case() -> CaseSpec:
    visible = VisiblePresentation(
        presentation="62-year-old male with acute substernal pressure.",
        demographics={"age": 62, "gender": "male"},
        history="Hypertension.",
        current_medications=["Aspirin"],
        allergies=["Penicillin"],
        initial_vitals={"bp": "136/84", "hr": 88},
        exam="Diaphoretic.",
    )
    return CaseSpec(
        case_id="CASE-ACC-001",
        specialty="Cardiology",
        patient_ref="PAT-ACC-001",
        visible=visible,
        hidden=[
            HiddenResult(
                order_code="DX-ECG",
                order_name="12-Lead ECG",
                result="ST elevation.",
                turnaround_time_minutes=10,
                category="imaging",
            )
        ],
        ground_truth=GroundTruth(
            primary_dx="Acute Anterior STEMI",
            acceptable_differential=["NSTEMI"],
            expected_workup=["12-Lead ECG"],
            red_flags=["Cardiogenic shock"],
        ),
        status="verified",
        version="1.0.0",
    )


def _passing_report() -> Dict[str, Any]:
    return {
        "patient_summary": "62yo male with acute substernal pressure.",
        "differential": [
            {
                "dx": "Acute Anterior STEMI",
                "likelihood": "high",
                "claim_ids": ["CLM-DX-01"],
            }
        ],
        "recommendations": [
            {
                "text": "Aspirin and angiography. Monitor for cardiogenic shock.",
                "claim_ids": ["CLM-RX-01"],
            }
        ],
        "claims": [
            {
                "claim_id": "CLM-DX-01",
                "text": "Troponin rise confirms anterior infarction.",
                "type": "diagnostic",
                "evidence_ids": ["CHUNK-001"],
            },
            {
                "claim_id": "CLM-RX-01",
                "text": "Troponin rise confirms anterior infarction.",
                "type": "therapeutic",
                "evidence_ids": ["CHUNK-001"],
            },
        ],
        "provenance": {
            "run_id": "run-acc",
            "model_id": "google/medgemma-4b",
            "prompt_name_version": "clinical_report@1.0.0",
            "index_version": "idx-v1",
            "case_id": "CASE-ACC-001",
        },
    }


def _make_state(report: Dict[str, Any]) -> EncounterState:
    return EncounterState(
        encounter_id="enc_acc",
        case_id="CASE-ACC-001",
        status=EncounterStatus.COMPLETED,
        termination_reason="report_submitted_and_verified",
        step_count=2,
        token_count=100,
        cost=0.01,
        sim_time_minutes=30,
        report=report,
        verification={"status": "verified", "passed": True, "critical_count": 0},
        history=[
            EncounterStep(
                step_number=1,
                actor="doctor",
                action="order_workup",
                payload={"ordered_tests": ["DX-ECG"]},
                sim_time_minutes=0,
            ),
            EncounterStep(
                step_number=2,
                actor="doctor",
                action="submit_report",
                payload={"report": report},
                sim_time_minutes=30,
            ),
        ],
    )


@pytest.fixture
def store(tmp_path):
    db = FeedbackStore(db_path=str(tmp_path / "acc.db"))
    yield db
    db.close()


@pytest.fixture
def evaluator():
    return AutomatedEvaluator(t_approve=0.50)


def _evidence() -> Dict[str, str]:
    return {"CHUNK-001": "Troponin rise confirms anterior infarction. Monitor for cardiogenic shock."}


def test_ingest_stores_original_with_verification_and_model_info(store):
    """Encounter ingestion preserves verification flags and model provenance."""
    original_id = ingest_encounter_report(store, _make_state(_passing_report()), _make_case())
    row = store.get_original(original_id)
    assert row["case_id"] == "CASE-ACC-001"
    assert row["model_id"] == "google/medgemma-4b"
    assert row["prompt_version"] == "clinical_report@1.0.0"
    import json

    assert json.loads(row["verification_json"])["status"] == "verified"


def test_ingest_rejects_non_completed_encounters(store):
    """Only terminal COMPLETED encounters enter the store."""
    state = _make_state(_passing_report())
    state.status = EncounterStatus.BUDGET_EXCEEDED
    with pytest.raises(ValueError):
        ingest_encounter_report(store, state, _make_case())


def test_evaluate_and_persist_approve_is_countable(store, evaluator):
    """Approve path persists review + target and counts the patient."""
    original_id = ingest_encounter_report(store, _make_state(_passing_report()), _make_case())
    review_id = evaluate_and_persist(
        store, evaluator, original_id, _make_state(_passing_report()), _make_case(), _evidence()
    )
    assert count_live_patients(store) == 1
    target = store.get_automated_target_by_review(review_id)
    assert target["derivation"] == "as-is"
    assert target["revalidation_pass"] == 1


def test_evaluate_missing_evidence_rejects_and_not_counted(store, evaluator):
    """Evidence gaps fail closed: rejected reviews never count."""
    original_id = ingest_encounter_report(store, _make_state(_passing_report()), _make_case())
    review_id = evaluate_and_persist(
        store, evaluator, original_id, _make_state(_passing_report()), _make_case(), {}
    )
    assert count_live_patients(store) == 0
    reviews = {r["id"]: r for r in store.list_automated_reviews()}
    assert reviews[review_id]["decision"] == "reject"


def _auto_record(patient_ref: str, decision: str) -> Dict[str, Any]:
    return {
        "case_id": f"CASE-{patient_ref}",
        "patient_ref": patient_ref,
        "original_report": {"patient_summary": "S."},
        "ground_truth_source": "physician-verified-golden-v1",
        "ground_truth_version": "v1",
        "validator_versions": {},
        "metrics": {"composite": 0.9},
        "decision": decision,
        "reasons": [],
        "sanitized_removed": [],
        "reviewer_id": "auto-validator/v1",
    }


def test_mixed_decisions_count_only_approve_correct_distinct(store):
    """Approve + correct count once per patient; rejects never count."""
    assert count_live_patients(store) == 0
    r1 = store.create_automated_review(_auto_record("PAT-A", "approve"))
    store.create_automated_target(r1, {"a": 1}, "as-is", [], True)
    r2 = store.create_automated_review(_auto_record("PAT-B", "correct"))
    store.create_automated_target(r2, {"b": 1}, "repaired", [], True)
    r3 = store.create_automated_review(_auto_record("PAT-C", "reject"))
    assert r3 is not None
    assert count_live_patients(store) == 2
    # Re-evaluating the same patient does not double-count.
    r4 = store.create_automated_review(_auto_record("PAT-A", "approve"))
    store.create_automated_target(r4, {"a": 2}, "as-is", [], True)
    assert count_live_patients(store) == 2
