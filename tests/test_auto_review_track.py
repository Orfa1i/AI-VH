"""
Acceptance tests for the Automated-Reviewed Case Track (approved design +
mandatory evaluator independence).

Covers: predicate approve/correct/reject branches, deletion-only repair with
mandatory revalidation, generator-independence (self-assessment can neither
pass nor fail a report), fail-closed errors, counter 0/499/500 with duplicate
collapse, splits, contamination, honest labeling, and human-track separation.
"""

import copy
from typing import Any, Dict, List

import pytest

from vh.agents.orchestrator import EncounterState, EncounterStatus, EncounterStep
from vh.cases.spec import CaseSpec, GroundTruth, HiddenResult, VisiblePresentation
from vh.training.auto_review import (
    SELF_ASSESSMENT_FIELDS,
    AutomatedEvaluator,
    sanitize_for_evaluation,
)


def _make_case() -> CaseSpec:
    visible = VisiblePresentation(
        presentation="62-year-old male with acute substernal pressure and diaphoresis.",
        demographics={"age": 62, "gender": "male"},
        history="Hypertension, hyperlipidemia.",
        current_medications=["Aspirin"],
        allergies=["Penicillin"],
        initial_vitals={"bp": "136/84", "hr": 88, "rr": 18, "spo2": 96, "temp": 37.0},
        exam="Diaphoretic, chest discomfort.",
    )
    hidden = [
        HiddenResult(
            order_code="DX-ECG",
            order_name="12-Lead ECG",
            result="ST elevation in anterior leads.",
            turnaround_time_minutes=10,
            category="imaging",
        ),
        HiddenResult(
            order_code="LAB-TROP",
            order_name="Troponin I",
            result="Elevated high-sensitivity troponin.",
            turnaround_time_minutes=20,
            category="laboratory",
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Acute Anterior STEMI",
        acceptable_differential=["NSTEMI", "Pericarditis"],
        expected_workup=["12-Lead ECG", "Troponin I"],
        red_flags=["Cardiogenic shock"],
    )
    return CaseSpec(
        case_id="CASE-AUTO-001",
        specialty="Cardiology",
        patient_ref="PAT-AUTO-001",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
        status="verified",
        version="1.0.0",
    )


def _passing_report() -> Dict[str, Any]:
    return {
        "patient_summary": "62yo male with acute substernal pressure.",
        "findings": ["ST elevation in anterior leads", "Elevated troponin"],
        "differential": [
            {
                "dx": "Acute Anterior STEMI",
                "likelihood": "high",
                "claim_ids": ["CLM-DX-01"],
            },
            {"dx": "NSTEMI", "likelihood": "moderate", "claim_ids": ["CLM-DX-01"]},
        ],
        "recommendations": [
            {
                "text": "Aspirin 325 mg and emergent angiography. Monitor for cardiogenic shock.",
                "claim_ids": ["CLM-RX-01"],
            }
        ],
        "claims": [
            {
                "claim_id": "CLM-DX-01",
                "text": "Troponin rise confirms acute anterior myocardial infarction.",
                "type": "diagnostic",
                "evidence_ids": ["CHUNK-001"],
            },
            {
                "claim_id": "CLM-RX-01",
                "text": "Troponin rise confirms acute anterior myocardial infarction.",
                "type": "therapeutic",
                "evidence_ids": ["CHUNK-001"],
            },
        ],
        "provenance": {
            "run_id": "run-auto-test",
            "model_id": "google/medgemma-4b",
            "prompt_name_version": "clinical_report@1.0.0",
            "index_version": "idx-v1",
            "case_id": "CASE-AUTO-001",
        },
    }


def _evidence() -> Dict[str, str]:
    return {
        "CHUNK-001": (
            "Troponin rise confirms acute anterior myocardial infarction "
            "with ST elevation. Aspirin and emergent angiography indicated. "
            "Monitor for cardiogenic shock."
        )
    }


def _make_state(report: Dict[str, Any]) -> EncounterState:
    history = [
        EncounterStep(
            step_number=1,
            actor="doctor",
            action="order_workup",
            payload={"ordered_tests": ["DX-ECG", "LAB-TROP"]},
            sim_time_minutes=0,
        ),
        EncounterStep(
            step_number=2,
            actor="diagnostics",
            action="report_findings",
            payload={"findings": {"DX-ECG": "ST elevation", "LAB-TROP": "Elevated"}},
            sim_time_minutes=30,
        ),
        EncounterStep(
            step_number=3,
            actor="doctor",
            action="submit_report",
            payload={"report": report},
            sim_time_minutes=45,
            result_summary="Clinical report submitted and verified",
        ),
    ]
    return EncounterState(
        encounter_id="enc_auto_test",
        case_id="CASE-AUTO-001",
        status=EncounterStatus.COMPLETED,
        termination_reason="report_submitted_and_verified",
        step_count=3,
        token_count=500,
        cost=0.05,
        sim_time_minutes=45,
        report=report,
        verification={"status": "verified", "passed": True, "critical_count": 0},
        history=history,
    )


@pytest.fixture
def evaluator() -> AutomatedEvaluator:
    return AutomatedEvaluator(t_approve=0.50)


def test_approve_path(evaluator: AutomatedEvaluator):
    """Fully passing encounter yields approve with complete provenance."""
    review = evaluator.evaluate(_make_state(_passing_report()), _make_case(), _evidence())
    assert review.decision == "approve"
    assert review.reasons == []
    assert review.target is not None
    assert review.target == _passing_report()
    provenance = review.provenance
    for key in (
        "case_id",
        "patient_ref",
        "ground_truth_version",
        "validator_versions",
        "metrics",
        "decision",
        "model_versions",
    ):
        assert key in provenance, f"missing provenance: {key}"
    assert provenance["reviewer_type"] == "automated"
    assert provenance["patient_ref"] == "PAT-AUTO-001"


def test_reject_on_critical_safety(evaluator: AutomatedEvaluator):
    """Allergen-ordered report fails closed with a critical_safety reason."""
    report = _passing_report()
    report["recommendations"] = [
        {"text": "Amoxicillin 500 mg twice daily.", "claim_ids": ["CLM-RX-01"]}
    ]
    review = evaluator.evaluate(_make_state(report), _make_case(), _evidence())
    assert review.decision == "reject"
    assert "critical_safety" in review.reasons
    assert review.target is None


def test_reject_on_dx_miss(evaluator: AutomatedEvaluator):
    """Wrong primary diagnosis rejects; no repair is attempted."""
    report = _passing_report()
    report["differential"] = [{"dx": "Gastroesophageal Reflux", "likelihood": "high", "claim_ids": ["CLM-DX-01"]}]
    review = evaluator.evaluate(_make_state(report), _make_case(), _evidence())
    assert review.decision == "reject"
    assert "dx_miss" in review.reasons
    assert review.repair_ops == []


def test_correct_single_unsupported_claim(evaluator: AutomatedEvaluator):
    """One unresolvable claim is deleted (never rewritten) + abstention added."""
    report = _passing_report()
    report["claims"] = list(report["claims"]) + [
        {
            "claim_id": "CLM-BAD-01",
            "text": "The hospital cafeteria serves lunch at noon.",
            "type": "factual",
            "evidence_ids": ["CHUNK-001"],
        }
    ]
    report["differential"][0] = dict(report["differential"][0], claim_ids=["CLM-DX-01"])
    review = evaluator.evaluate(_make_state(report), _make_case(), _evidence())
    assert review.decision == "correct"
    assert len(review.repair_ops) >= 1
    assert all(op["op"] == "remove" for op in review.repair_ops if op["op"] != "add")
    assert review.target is not None
    remaining_ids = {c["claim_id"] for c in review.target["claims"]}
    assert "CLM-BAD-01" not in remaining_ids
    assert len(review.target.get("abstentions", [])) >= 1
    assert review.revalidation_pass is True


def test_reject_unfixable_multi_defect(evaluator: AutomatedEvaluator):
    """Dx miss plus unsupported claim rejects without repair."""
    report = _passing_report()
    report["differential"] = [{"dx": "Costochondritis", "likelihood": "high", "claim_ids": ["CLM-DX-01"]}]
    report["claims"] = list(report["claims"]) + [
        {
            "claim_id": "CLM-BAD-01",
            "text": "The hospital cafeteria serves lunch at noon.",
            "type": "factual",
            "evidence_ids": ["CHUNK-001"],
        }
    ]
    review = evaluator.evaluate(_make_state(report), _make_case(), _evidence())
    assert review.decision == "reject"
    assert "dx_miss" in review.reasons
    assert review.repair_ops == []
    assert review.target is None


def test_gray_zone_rejects_despite_passing_gates():
    """Composite below bar with gates green rejects as ambiguous (unit-level)."""
    from vh.training.auto_review import decide_from_metrics

    decision, reasons = decide_from_metrics(
        {
            "schema_ok": True,
            "critical_count": 0,
            "unsupported_count": 0,
            "dx_top1": 1.0,
            "red_flags": 1.0,
            "composite": 0.40,
            "verification_passed": True,
            "router_verified": True,
        },
        t_approve=0.50,
    )
    assert decision == "reject"
    assert "ambiguous_composite" in reasons


def test_flattering_self_assessment_cannot_approve(evaluator: AutomatedEvaluator):
    """Generator confidence 0.99 + glowing self-review cannot rescue a reject."""
    report = _passing_report()
    report["differential"] = [{"dx": "Anxiety", "likelihood": "high", "claim_ids": ["CLM-DX-01"]}]
    report["confidence"] = 0.99
    report["self_evaluation"] = "This report is certainly correct in all respects."
    report["reasoning_trace"] = "I carefully verified everything twice."
    review = evaluator.evaluate(_make_state(report), _make_case(), _evidence())
    assert review.decision == "reject"
    assert "dx_miss" in review.reasons
    removed = review.sanitized_removed
    assert any("confidence" in path for path in removed)
    assert any("self_evaluation" in path for path in removed)


def test_self_doubt_cannot_fail(evaluator: AutomatedEvaluator):
    """Generator self-doubt cannot fail an otherwise passing report."""
    report = _passing_report()
    report["confidence"] = 0.01
    report["self_evaluation"] = "I am unsure about all of this."
    review = evaluator.evaluate(_make_state(report), _make_case(), _evidence())
    assert review.decision == "approve"


def test_sanitizer_strips_nested_fields():
    """Denylist fields are removed at any depth; input untouched; paths logged."""
    original = {
        "patient_summary": "S.",
        "notes": {"chain_of_thought": "secret", "dx": "X"},
        "reasoning": {"chain_of_thought": "whole trace must go"},
        "confidence": 0.5,
    }
    snapshot = copy.deepcopy(original)
    cleaned, removed = sanitize_for_evaluation(original)
    assert original == snapshot
    assert "confidence" not in cleaned
    # Denylisted parent removes the whole subtree.
    assert "reasoning" not in cleaned
    # Non-denylisted parent survives with only the denylisted leaf removed.
    assert cleaned["notes"]["dx"] == "X"
    assert "chain_of_thought" not in cleaned["notes"]
    assert len(removed) == 3
    assert all(isinstance(path, str) for path in removed)


def test_evaluator_source_has_no_generator_references():
    """Tripwire: the evaluator must not touch generation adapters or LLM calls.

    The report *schema* import (vh.generation.report) is explicitly allowed:
    it is types only, already imported by the verification layer itself.
    """
    from pathlib import Path

    source = (
        Path("src") / "vh" / "training" / "auto_review.py"
    ).read_text(encoding="utf-8")
    for symbol in (
        "MedGemmaAdapter",
        "llm_call",
        "generate_clinical_assessment",
        "generation.medgemma",
        "generation.pipeline",
        "generation.baseline",
    ):
        assert symbol not in source, f"forbidden generator reference: {symbol}"
    assert "SELF_ASSESSMENT_FIELDS" in source


def test_fail_closed_on_router_error(evaluator: AutomatedEvaluator, tmp_path):
    """Validator exceptions reject with eval_error and persist nothing."""
    from vh.feedback.models import FeedbackStore

    class ExplodingRouter:
        def verify(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("validator exploded")

    strict = AutomatedEvaluator(t_approve=0.50, router=ExplodingRouter())
    review = strict.evaluate(_make_state(_passing_report()), _make_case(), _evidence())
    assert review.decision == "reject"
    assert "eval_error" in review.reasons

    store = FeedbackStore(db_path=str(tmp_path / "fb.db"))
    try:
        assert store.automated_review_count() == 0
    finally:
        store.close()


def test_self_assessment_field_denylist_covers_known_vectors():
    for field in (
        "confidence",
        "self_evaluation",
        "self_assessment",
        "reasoning_trace",
        "justification",
        "certainty",
        "model_confidence",
    ):
        assert field in SELF_ASSESSMENT_FIELDS


def _auto_review_row(patient_ref: str, decision: str = "approve", complete: bool = True) -> dict:
    return {
        "case_id": f"CASE-{patient_ref}",
        "patient_ref": patient_ref,
        "decision": decision,
        "revalidation_pass": True,
        "reviewer_type": "automated",
        "provenance_complete": complete,
    }


def test_counter_zero_cases():
    from vh.training.curation import count_distinct_patients

    assert count_distinct_patients([]) == 0


def test_counter_499_500():
    from vh.training.curation import count_distinct_patients

    reviews_499 = [_auto_review_row(f"PAT-{i:04d}") for i in range(499)]
    reviews_500 = [_auto_review_row(f"PAT-{i:04d}") for i in range(500)]
    assert count_distinct_patients(reviews_499) == 499
    assert count_distinct_patients(reviews_500) == 500


def test_counter_collapses_duplicate_patients_and_excludes_rejects():
    from vh.training.curation import count_distinct_patients

    reviews = [
        _auto_review_row("PAT-001"),
        _auto_review_row("PAT-001"),
        _auto_review_row("PAT-002", decision="reject"),
        _auto_review_row("PAT-003", complete=False),
        _auto_review_row("PAT-004", decision="correct"),
    ]
    assert count_distinct_patients(reviews) == 2


def test_split_by_patient_no_overlap_stratified_deterministic():
    from vh.training.curation import split_by_patient

    reviews = [_auto_review_row(f"PAT-{i:04d}", decision=("correct" if i % 3 == 0 else "approve")) for i in range(60)]
    first = split_by_patient(reviews, seed=42)
    second = split_by_patient(reviews, seed=42)
    assert first == second
    train_ids = {r["patient_ref"] for r in first["train"]}
    val_ids = {r["patient_ref"] for r in first["val"]}
    test_ids = {r["patient_ref"] for r in first["test"]}
    assert not (train_ids & val_ids) and not (train_ids & test_ids) and not (val_ids & test_ids)
    assert len(train_ids) + len(val_ids) + len(test_ids) == 60
    for split in ("train", "val", "test"):
        decisions = {r["decision"] for r in first[split]}
        assert decisions <= {"approve", "correct"}


def test_contamination_id_and_neardup():
    from vh.training.curation import contamination_check

    golden = [
        {"case_id": "GOLDEN-001", "patient_summary": "acute chest pain with troponin rise"},
        {"case_id": "GOLDEN-002", "patient_summary": "fever cough infiltrate present"},
    ]
    reviews = [
        {"case_id": "GOLDEN-001", "patient_ref": "PAT-A", "report_text": "unrelated text here"},
        {"case_id": "CASE-X", "patient_ref": "PAT-B", "report_text": "acute chest pain with troponin rise!!"},
        {"case_id": "CASE-Y", "patient_ref": "PAT-C", "report_text": "completely different presentation entirely"},
    ]
    excluded = contamination_check(reviews, golden_cases=golden, similarity_threshold=0.8)
    assert "PAT-A" in excluded  # id match
    assert "PAT-B" in excluded  # near-duplicate text
    assert "PAT-C" not in excluded


def test_exported_rows_honestly_labeled():
    """Auto artifacts carry reviewer_type=automated and no doctor-final language."""
    from vh.training.curation import HONESTY_BANNED_PHRASES, label_export_rows

    rows = label_export_rows([_auto_review_row("PAT-001"), _auto_review_row("PAT-002")])
    assert all(r["reviewer_type"] == "automated" for r in rows)
    blob = str(rows).lower()
    for phrase in HONESTY_BANNED_PHRASES:
        assert phrase not in blob, f"banned phrase present: {phrase}"


def test_automated_actor_blocked_from_human_tables(tmp_path):
    """Automated identities cannot write human review rows; human path intact."""
    from vh.feedback.models import FeedbackStore

    store = FeedbackStore(db_path=str(tmp_path / "fb.db"))
    try:
        auto_id, _ = store.register_reviewer("auto-validator/v1", "system", reviewer_type="automated")
        assert store.automated_review_count() == 0
        with pytest.raises(ValueError):
            store.assign_review("rep_x", auto_id)
        with pytest.raises(ValueError):
            store.add_edit("ses_x", "replace", ["a"], "b", actor=auto_id)
        with pytest.raises(ValueError):
            store.rate_claim("ses_x", "CLM-1", "correct", "formatting", actor=auto_id)
        with pytest.raises(ValueError):
            store.finalize_report("ses_x", actor=auto_id)
        # Human path unaffected.
        human = store.add_reviewer("rev-h", "Dr. Human", "attending")
        assert human == "rev-h"
    finally:
        store.close()
