"""
Unit and Integration Tests for the 14-Gate Pre-Training Validation & Model Lifecycle Pipeline.
Tests individual gates, fail-closed enforcement, manifest generation, post-training evaluation,
promotion criteria, and API endpoints.
"""

import pytest
import os
import uuid
import json
from datetime import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.clinical.cases import BENCHMARK_CASES
from backend.rl.pre_training_validator import (
    PreTrainingValidator,
    pre_training_validator,
    GOLDEN_CASE_IDS,
)
from backend.rl.lifecycle import (
    ModelLifecycleManager,
    model_lifecycle_manager,
    MANIFESTS_DIR,
)
from backend.rl.train_dpo import DPOTrainingConfig
from backend.api.router import _training_state


@pytest.fixture(autouse=True)
def clean_state():
    _training_state["status"] = "IDLE"
    _training_state["last_run"] = None
    _training_state["last_error"] = None
    _training_state["failed_gates"] = []
    _training_state["blockers"] = []
    yield
    _training_state["status"] = "IDLE"
    _training_state["last_run"] = None
    _training_state["last_error"] = None
    _training_state["failed_gates"] = []
    _training_state["blockers"] = []


def _create_valid_record(
    case_id: str = "CASE-SYNTH-501",
    patient_id: str = "PAT-SYNTH-501",
    report_id: str = "RPT-VAL-501",
    specialty: str = "INTERNAL_MEDICINE",
    patient_name: str = "Valid Synthetic Patient",
) -> dict:
    """Helper to generate a 100% compliant, non-leaked training dataset record."""
    return {
        "id": f"TDR-{uuid.uuid4().hex[:8].upper()}",
        "case_id": case_id,
        "patient_id": patient_id,
        "report_id": report_id,
        "model_version": "google/medgemma-4b",
        "specialty": specialty,
        "original_input": {
            "patient_name": patient_name,
            "age": 55,
            "sex": "Female",
            "chief_complaint": "Acute epigastric discomfort after meals",
            "history_of_present_illness": "55yo female with 3 days of worsening epigastric pain.",
            "prompt": "Evaluate patient with epigastric discomfort, normal vitals, and elevated lipase.",
        },
        "original_ai_output": {
            "primary_diagnosis": "Acute Pancreatitis, Mild",
            "clinical_reasoning": "Elevated lipase >3x ULN with epigastric pain indicates pancreatitis.",
            "treatment_plan": ["IV hydration", "Bowel rest", "Analgesia"],
        },
        "reviewer_feedback": {
            "physician_name": "Dr. Validated Attending, MD",
            "reviewer_role": "ATTENDING_PHYSICIAN",
            "notes": "Clinically accurate and guideline-concordant.",
            "approved": True,
        },
        "corrected_output": {
            "primary_diagnosis": "Acute Pancreatitis, Mild",
            "clinical_reasoning": "Lipase elevation with clinical concordance confirms mild acute pancreatitis.",
            "corrections_applied": False,
        },
        "provenance": {
            "source": "CLINICAL_SIMULATION",
            "encounter_id": "ENC-VAL-001",
        },
        "review_status": "APPROVED",
        "dataset_eligibility": "ELIGIBLE",
        "timestamp": datetime.utcnow().isoformat(),
    }


def test_gate_1_minimum_eligible_cases():
    """Gate 1: Rejects when eligible cases count is below required threshold."""
    validator = PreTrainingValidator()
    # Provide only 2 records, while requiring 5
    records = [_create_valid_record(case_id=f"CASE-G1-{i}", patient_id=f"PAT-G1-{i}") for i in range(2)]
    res = validator.validate(records=records, min_cases_override=5)

    assert not res.passed
    assert "Minimum Required Eligible Cases" in res.failed_gates
    g1 = next(g for g in res.gate_results if g.gate_id == 1)
    assert not g1.passed
    assert g1.details["found"] == 2
    assert g1.details["required"] == 5


def test_gate_2_patient_deduplication():
    """Gate 2: Rejects when duplicate patients exist in the training cohort."""
    validator = PreTrainingValidator()
    rec1 = _create_valid_record(case_id="CASE-DEDUP-01", patient_id="PAT-SAME-01")
    rec2 = _create_valid_record(case_id="CASE-DEDUP-02", patient_id="PAT-SAME-01")  # Duplicate patient_id

    res = validator.validate(records=[rec1, rec2], min_cases_override=1)
    assert not res.passed
    assert "Patient-Level Deduplication" in res.failed_gates
    g2 = next(g for g in res.gate_results if g.gate_id == 2)
    assert not g2.passed
    assert "PAT-SAME-01" in g2.details["duplicate_patient_ids"]


def test_gate_3_and_12_golden_cases_isolation():
    """Gates 3 & 12: Blocks benchmark golden cases from contaminating training."""
    validator = PreTrainingValidator()
    golden_case = BENCHMARK_CASES[0]  # CASE-101 (Robert Miller)
    rec = _create_valid_record(
        case_id=golden_case.id,
        patient_id=golden_case.id,
        patient_name=golden_case.name,
    )

    res = validator.validate(records=[rec], min_cases_override=1)
    assert not res.passed
    assert "Train/Evaluation Split Isolation" in res.failed_gates or "Golden Cases Strict Isolation" in res.failed_gates
    g12 = next(g for g in res.gate_results if g.gate_id == 12)
    assert not g12.passed
    assert golden_case.id in g12.details["golden_case_ids"]


def test_gate_7_ground_truth_leakage_detection():
    """Gate 7: Scans input prompts and rejects if hidden benchmark ground truth keys are leaked."""
    validator = PreTrainingValidator()
    rec = _create_valid_record()
    # Inject hidden ground truth key into original_input
    rec["original_input"]["true_diagnosis"] = "Acute ST-Elevation Myocardial Infarction"

    res = validator.validate(records=[rec], min_cases_override=1)
    assert not res.passed
    assert "Zero Ground-Truth Leakage" in res.failed_gates
    g7 = next(g for g in res.gate_results if g.gate_id == 7)
    assert not g7.passed


def test_gate_8_evaluator_metadata_leakage():
    """Gate 8: Rejects when automated evaluator scores or judge tokens leak into training prompt."""
    validator = PreTrainingValidator()
    rec = _create_valid_record()
    rec["original_input"]["evaluator_score"] = 4.8

    res = validator.validate(records=[rec], min_cases_override=1)
    assert not res.passed
    assert "Zero Evaluator Metadata Leakage" in res.failed_gates
    g8 = next(g for g in res.gate_results if g.gate_id == 8)
    assert not g8.passed


def test_gate_9_future_event_leakage():
    """Gate 9: Rejects when post-encounter discharge events or future complications are in prompt."""
    validator = PreTrainingValidator()
    rec = _create_valid_record()
    rec["original_input"]["post_discharge_complication"] = "Patient readmitted 2 weeks later with re-infarction"

    res = validator.validate(records=[rec], min_cases_override=1)
    assert not res.passed
    assert "Zero Future-Event Leakage" in res.failed_gates
    g9 = next(g for g in res.gate_results if g.gate_id == 9)
    assert not g9.passed


def test_gate_14_record_completeness():
    """Gate 14: Rejects records with null or missing mandatory lifecycle fields."""
    validator = PreTrainingValidator()
    rec = _create_valid_record()
    del rec["specialty"]  # Missing 1 of 13 fields

    res = validator.validate(records=[rec], min_cases_override=1)
    assert not res.passed
    assert "Record Completeness & Schema Conformity" in res.failed_gates
    g14 = next(g for g in res.gate_results if g.gate_id == 14)
    assert not g14.passed


def test_all_14_gates_pass_clean_record():
    """Verifies that 100% clean synthetic records pass all 14 gates."""
    validator = PreTrainingValidator()
    records = [
        _create_valid_record(
            case_id=f"CASE-CLEAN-{i}",
            patient_id=f"PAT-CLEAN-{i}",
            report_id=f"RPT-CLEAN-{i}",
        )
        for i in range(3)
    ]
    res = validator.validate(records=records, min_cases_override=3)
    assert res.passed
    assert res.gates_passed == 14
    assert res.gates_failed == 0
    assert len(res.failed_gates) == 0


def test_manifest_creation_and_reproducible_sha256():
    """Lifecycle Step: Freezing dataset creates reproducible SHA-256 digest and manifest."""
    manager = ModelLifecycleManager(manifests_dir=MANIFESTS_DIR)
    records = [_create_valid_record(case_id="CASE-MNF-01", patient_id="PAT-MNF-01")]

    frozen_path, digest1 = manager.freeze_dataset(records, "TEST-HASH-01")
    assert os.path.exists(frozen_path)
    assert len(digest1) == 64  # SHA-256 hex digest length

    # Re-freezing identical data must yield the exact same SHA-256 digest
    _, digest2 = manager.freeze_dataset(records, "TEST-HASH-02")
    assert digest1 == digest2

    # Manifest emission
    manifest = manager.create_manifest(
        manifest_id="MNF-TEST-001",
        records=records,
        hyperparameters={"epochs": 4, "learning_rate": 2e-4},
        frozen_dataset_path=frozen_path,
        dataset_hash=digest1,
    )
    assert manifest.manifest_id == "MNF-TEST-001"
    assert manifest.dataset_hash_sha256 == digest1
    assert manifest.base_model_version == "google/medgemma-4b"
    assert manifest.eligible_records_count == 1

    # Verify manifest file exists on disk
    manifest_file = os.path.join(MANIFESTS_DIR, "manifest_MNF-TEST-001.json")
    assert os.path.exists(manifest_file)
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["dataset_hash_sha256"] == digest1


def test_post_training_evaluation_and_promotion_gating():
    """Lifecycle Step: Post-training benchmark evaluation and promotion decision."""
    manager = ModelLifecycleManager(manifests_dir=MANIFESTS_DIR)
    eval_res = manager.run_post_training_evaluation(
        candidate_version="medgemma-dpo-lora-test",
        adapter_path="models/medgemma-dpo-lora",
    )
    assert eval_res.candidate_version == "medgemma-dpo-lora-test"
    assert eval_res.cases_evaluated == len(BENCHMARK_CASES)
    # Must produce one of the valid promotion decisions
    assert eval_res.promotion_decision in ("PROMOTED", "REJECTED_SAFETY_REGRESSION", "REJECTED_BELOW_BASELINE")
    assert len(eval_res.promotion_rationale) > 0


def test_api_pre_training_validate_endpoint():
    """API endpoint GET /api/rl/train/validate returns full 14-gate audit checklist."""
    client = TestClient(app)
    response = client.get("/api/rl/train/validate")
    assert response.status_code == 200
    data = response.json()

    assert "gates_evaluated" in data
    assert data["gates_evaluated"] == 14
    assert "gate_results" in data
    assert len(data["gate_results"]) == 14
    assert "thresholds_verified" in data


def test_api_train_blocked_when_gates_fail(monkeypatch):
    """API endpoint POST /api/rl/train returns HTTP 422 with gate diagnostics when gates fail."""
    # Ensure VH_ALLOW_RL_TRAIN=true so the 503 latch does not intercept first
    monkeypatch.setenv("VH_ALLOW_RL_TRAIN", "true")
    client = TestClient(app)

    # Calling train with default dataset (which has fewer than 500 records) MUST fail closed with 422
    response = client.post("/api/rl/train", json={"epochs": 1, "dry_run": True})
    assert response.status_code == 422
    err_data = response.json()
    detail = err_data.get("detail", {})

    assert detail.get("status") == "BLOCKED_VALIDATION_FAILED"
    assert len(detail.get("blockers", [])) > 0
    assert "validation" in detail
    assert detail["validation"]["passed"] is False
    assert len(detail["validation"]["failed_gates"]) > 0


def test_api_list_manifests_endpoint():
    """API endpoint GET /api/rl/train/manifests returns list of training manifests."""
    client = TestClient(app)
    response = client.get("/api/rl/train/manifests")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
