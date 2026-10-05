"""
Unit and Integration Tests for Review -> Structured Feedback -> Training Dataset Pipeline.
Verifies report immutability, separate review storage, separate correction storage,
preservation of all 13 training dataset fields, patient/case deduplication,
strict ground-truth isolation, eligibility status rules, and manual-only training enforcement.
"""

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.clinical.models import (
    ClinicalReport,
    PhysicianReview,
    ReviewAssessment,
    ReviewErrorTaxonomy,
    DatasetEligibilityStatus,
    TrainingDatasetRecord,
    VitalSigns,
    LabResult,
    LabTestType,
    DifferentialItem,
)
from backend.clinical.cases import BENCHMARK_CASES
from backend.database.repository import db_repo
from backend.rl.dataset_curator import dataset_curator
from backend.simulation.orchestrator import orchestrator


@pytest.fixture(autouse=True)
def clean_database():
    """Ensure clean database baseline before and after each test."""
    from backend.api.router import _training_state
    _training_state["status"] = "IDLE"
    _training_state["last_run"] = None
    _training_state["last_error"] = None
    _training_state["failed_gates"] = []
    _training_state["blockers"] = []

    db_repo.purge_mock_data()
    orchestrator.reports.clear()
    orchestrator.reviews.clear()
    orchestrator.encounters.clear()
    yield
    db_repo.purge_mock_data()
    _training_state["status"] = "IDLE"


def _create_sample_report(report_id: str = "RPT-REV-TEST-001", patient_id: str = "CASE-101") -> ClinicalReport:
    report = ClinicalReport(
        id=report_id,
        encounter_id=f"ENC-{uuid.uuid4().hex[:6].upper()}",
        patient_id=patient_id,
        patient_name="Robert Miller",
        patient_age=62,
        patient_sex="Male",
        chief_complaint="Substernal chest pressure and dyspnea",
        history_of_present_illness="62yo male presenting with sudden onset acute substernal chest pressure.",
        past_medical_history=["Hypertension", "Type 2 Diabetes"],
        medications=["Metformin 1000mg", "Lisinopril 20mg"],
        allergies=["Penicillin"],
        vital_signs=VitalSigns(
            heart_rate=96,
            systolic_bp=140,
            diastolic_bp=85,
            respiratory_rate=18,
            temperature_c=36.8,
            spo2_percent=98.0,
            pain_score=7,
        ),
        physical_exam_findings={"heart": "Regular rhythm, no murmurs", "lungs": "Clear to auscultation bilaterally"},
        investigations_ordered=[LabTestType.ECG_12_LEAD, LabTestType.TROPONIN_I],
        investigation_results=[
            LabResult(test_type=LabTestType.ECG_12_LEAD, values={"ecg": "ST depression"}, interpretation="ST-segment depression in inferior leads"),
            LabResult(test_type=LabTestType.TROPONIN_I, values={"troponin_i": 2.1}, interpretation="Troponin-I 2.1 ng/mL (elevated)"),
        ],
        clinical_summary="Patient with acute substernal chest pain and elevated biomarkers.",
        relevant_findings=["Ischemic ECG findings", "Elevated cardiac enzymes"],
        primary_diagnosis="Acute Coronary Syndrome, Unspecified",
        diagnostic_confidence=0.82,
        differential_diagnosis=[
            DifferentialItem(condition="Acute Coronary Syndrome, Unspecified", likelihood=0.82, supporting_points=["Chest pain"]),
            DifferentialItem(condition="Gastroesophageal Reflux", likelihood=0.18, supporting_points=["Discomfort"]),
        ],
        clinical_reasoning="Clinical findings and ischemic ECG indicate ACS requiring further stratification.",
        treatment_plan=["Aspirin 325mg PO", "Telemetry monitoring"],
        recommended_disposition="Admit to Cardiology",
        recommended_next_steps=["Telemetry", "Serial Troponins"],
        medical_knowledge_citations=[
            {"source": "Harrison's Principles of Internal Medicine", "chapter": "Acute Coronary Syndromes", "page": 1820, "text": "ACS evaluation"}
        ],
        model_provenance="google/medgemma-4b",
        ungrounded=False,
    )
    db_repo.save_report(report, case_id=patient_id)
    orchestrator.reports[report.id] = report
    return report


def test_original_report_immutability():
    """Rule: When reviewer submits feedback, the original AI report MUST remain unchanged."""
    report = _create_sample_report()
    orig_diag = report.primary_diagnosis
    orig_reasoning = report.clinical_reasoning
    orig_tx = list(report.treatment_plan)

    # Submit physician correction with revised diagnosis and plan
    review = orchestrator.submit_physician_review(
        report_id=report.id,
        physician_name="Dr. Attending Specialist, MD",
        diagnosis_grade="PARTIALLY_CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=3,
        approved=False,
        notes="Refined to specific NSTEMI with dual antiplatelet therapy.",
        corrected_diagnosis="Non-ST-Elevation Myocardial Infarction (NSTEMI)",
        corrected_reasoning="Biomarker positivity with ST depressions confirms NSTEMI.",
        corrected_treatment=["Aspirin 325 mg", "Ticagrelor 180 mg", "Heparin drip"],
        assessment="PARTIALLY_CORRECT",
        identified_errors=["MISSING_INFORMATION", "POOR_EVIDENCE_USE"],
    )

    # 1. Check in-memory report
    current_report = orchestrator.get_report(report.id)
    assert current_report["primary_diagnosis"] == orig_diag
    assert current_report["clinical_reasoning"] == orig_reasoning
    assert current_report["treatment_plan"] == orig_tx

    # 2. Check persistent database record
    db_report = db_repo.get_report(report.id)
    assert db_report["primary_diagnosis"] == orig_diag
    assert db_report["clinical_reasoning"] == orig_reasoning
    assert db_report["treatment_plan"] == orig_tx


def test_separate_storage_of_review_and_corrections():
    """Rule: Store reviewer feedback separately, store corrected version separately."""
    report = _create_sample_report()
    review = orchestrator.submit_physician_review(
        report_id=report.id,
        physician_name="Dr. Sarah Connor, MD",
        diagnosis_grade="PARTIALLY_CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=4,
        approved=True,
        notes="Solid foundation; refine differential ordering.",
        corrected_diagnosis="Acute NSTEMI",
        corrected_reasoning="Direct ischemic elevation.",
        corrected_treatment=["Aspirin", "Clopidogrel", "Atorvastatin 80mg"],
        assessment="PARTIALLY_CORRECT",
        identified_errors=["MISSING_INFORMATION"],
        reviewer_role="ATTENDING_PHYSICIAN",
        specialty="CARDIOLOGY",
    )

    # Retrieve from separate review table
    saved_review = db_repo.get_review(review.id)
    assert saved_review is not None
    assert saved_review["report_id"] == report.id
    assert saved_review["physician_name"] == "Dr. Sarah Connor, MD"
    assert saved_review["assessment"] == "PARTIALLY_CORRECT"
    assert saved_review["corrected_diagnosis"] == "Acute NSTEMI"

    # Retrieve from curated training dataset records table
    records = db_repo.get_training_dataset_records()
    assert len(records) == 1
    rec = records[0]
    # Check separate storage of original AI output vs corrected output
    assert rec["original_ai_output"]["primary_diagnosis"] == "Acute Coronary Syndrome, Unspecified"
    assert rec["corrected_output"]["primary_diagnosis"] == "Acute NSTEMI"
    assert rec["corrected_output"]["corrections_applied"] is True
    assert rec["corrected_output"]["preferred_basis"] == "PHYSICIAN_CORRECTION"


def test_training_record_preserves_all_13_lifecycle_fields():
    """Rule: Training records should preserve all 13 specified fields."""
    report = _create_sample_report()
    review = orchestrator.submit_physician_review(
        report_id=report.id,
        physician_name="Dr. Vance, MD",
        diagnosis_grade="CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=5,
        approved=True,
        notes="Gold-standard evaluation per Harrison's.",
        assessment="CORRECT",
        identified_errors=[],
    )

    records = db_repo.get_training_dataset_records()
    assert len(records) == 1
    rec = records[0]

    # Verify all 13 fields exist and are populated
    required_fields = [
        "case_id",
        "patient_id",
        "report_id",
        "model_version",
        "specialty",
        "original_input",
        "original_ai_output",
        "reviewer_feedback",
        "corrected_output",
        "provenance",
        "review_status",
        "dataset_eligibility",
        "timestamp",
    ]
    for field in required_fields:
        assert field in rec, f"Missing required field: {field}"
        assert rec[field] is not None, f"Field {field} should not be None"

    assert rec["case_id"] == "CASE-101"
    assert rec["patient_id"] == "CASE-101"
    assert rec["report_id"] == report.id
    assert rec["model_version"] == "google/medgemma-4b"
    assert rec["review_status"] == "APPROVED"
    assert rec["dataset_eligibility"] == "ELIGIBLE"


def test_patient_case_deduplication():
    """Rule: Prevent duplicate patient cases from artificially inflating training counts."""
    # First review for patient CASE-101
    rep1 = _create_sample_report(report_id="RPT-DEDUP-001", patient_id="CASE-101")
    orchestrator.submit_physician_review(
        report_id=rep1.id,
        physician_name="Dr. Physician One",
        diagnosis_grade="CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=5,
        approved=True,
        notes="First review for patient.",
        assessment="CORRECT",
    )

    # Second review for the SAME patient CASE-101
    rep2 = _create_sample_report(report_id="RPT-DEDUP-002", patient_id="CASE-101")
    orchestrator.submit_physician_review(
        report_id=rep2.id,
        physician_name="Dr. Physician Two",
        diagnosis_grade="CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=4,
        approved=True,
        notes="Duplicate review for same patient.",
        assessment="CORRECT",
    )

    records = db_repo.get_training_dataset_records()
    assert len(records) == 2

    # The second record must be marked INELIGIBLE_DUPLICATE
    second_rec = next(r for r in records if r["report_id"] == rep2.id)
    assert second_rec["dataset_eligibility"] == "INELIGIBLE_DUPLICATE"

    # Only one eligible record exists for CASE-101
    eligible_records = db_repo.get_training_dataset_records(eligibility="ELIGIBLE")
    assert len(eligible_records) == 1
    assert eligible_records[0]["report_id"] == rep1.id


def test_dataset_eligibility_incomplete_correction():
    """Rule: Only valid, complete, eligible examples should enter training dataset."""
    rep = _create_sample_report()
    # Mark INCORRECT but leave corrected diagnosis, reasoning, and notes blank
    review = orchestrator.submit_physician_review(
        report_id=rep.id,
        physician_name="Dr. Busy Reviewer",
        diagnosis_grade="INCORRECT",
        reasoning_grade="FAULTY_LOGIC",
        tests_grade="INAPPROPRIATE_TEST",
        treatment_grade="CONTRAINDICATED_OR_HARMFUL",
        overall_score=1,
        approved=False,
        notes="",  # Incomplete feedback
        assessment="INCORRECT",
        identified_errors=["INCORRECT_DIAGNOSIS"],
    )

    records = db_repo.get_training_dataset_records()
    assert len(records) == 1
    assert records[0]["dataset_eligibility"] == "INELIGIBLE_INCOMPLETE"


def test_zero_ground_truth_leakage_to_reviewer_and_model():
    """Rule: Reviewer/student identifies problems without seeing hidden Ground Truth."""
    client = TestClient(app)
    rep = _create_sample_report()

    # Query report detail API endpoint
    response = client.get(f"/api/reports/{rep.id}")
    assert response.status_code == 200
    data = response.json()

    # Ensure hidden Ground Truth keys are NOT present in the clinical report
    assert "true_diagnosis" not in data
    assert "contraindicated_treatments" not in data
    assert "optimal_treatment" not in data


def test_no_automatic_training_triggered():
    """Rule: Do not immediately train the model upon feedback submission."""
    from backend.api.router import _training_state

    # Verify initial state is IDLE
    assert _training_state["status"] == "IDLE"

    rep = _create_sample_report()
    orchestrator.submit_physician_review(
        report_id=rep.id,
        physician_name="Dr. Marcus Vance",
        diagnosis_grade="CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=5,
        approved=True,
        notes="Exemplary report.",
        assessment="CORRECT",
    )

    # State must remain IDLE (training is strictly manual)
    assert _training_state["status"] == "IDLE"
    assert _training_state["last_run"] is None


def test_api_submit_review_and_curated_dataset():
    """Test API endpoints for review submission and curated dataset inspection."""
    client = TestClient(app)
    rep = _create_sample_report()

    payload = {
        "report_id": rep.id,
        "physician_name": "Dr. API Tester, MD",
        "overall_score": 4,
        "approved": True,
        "notes": "Verified via REST API endpoint with rich taxonomy.",
        "assessment": "PARTIALLY_CORRECT",
        "identified_errors": ["MISSING_INFORMATION", "POOR_EVIDENCE_USE"],
        "corrected_diagnosis": "Acute NSTEMI (Type 1 MI)",
        "corrected_reasoning": "Coronary plaque rupture evidenced by troponin rise.",
        "corrected_recommendations": ["Aspirin 325mg", "Heparin IV infusion"],
        "reviewer_role": "ATTENDING_PHYSICIAN",
        "specialty": "CARDIOLOGY",
    }

    res = client.post("/api/reviews", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["report_id"] == rep.id
    assert res_data["assessment"] == "PARTIALLY_CORRECT"
    assert "MISSING_INFORMATION" in res_data["identified_errors"]

    # Query curated dataset endpoint
    cur_res = client.get("/api/rl/dataset/curated?eligibility=ELIGIBLE")
    assert cur_res.status_code == 200
    cur_data = cur_res.json()
    assert cur_data["total_count"] >= 1
    matching = next(r for r in cur_data["records"] if r["report_id"] == rep.id)
    assert matching["dataset_eligibility"] == "ELIGIBLE"
    assert matching["corrected_output"]["primary_diagnosis"] == "Acute NSTEMI (Type 1 MI)"
