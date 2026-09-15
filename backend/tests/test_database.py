"""
Automated Test Suite for Database Persistence & Repository Layer
Tests schema initialization, report CRUD, review CRUD, DPO pair storage,
cross-session data survival, and API endpoints for PostgreSQL & SQLite.
"""

import os
import tempfile
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.database.connection import DatabaseConnectionManager
from backend.database.repository import DatabaseRepository
from backend.clinical.models import (
    ClinicalReport,
    PhysicianReview,
    VitalSigns,
    LabTestType,
    LabResult,
    DifferentialItem,
    DiagnosisFeedback,
    ReasoningFeedback,
    TestAppropriatenessFeedback,
    TreatmentSafetyFeedback,
)
from backend.rl.dpo_generator import DPOPreferencePair
from backend.main import app


@pytest.fixture
def temp_db():
    """Creates an isolated temporary database for test execution."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    
    manager = DatabaseConnectionManager(sqlite_path=temp_path)
    repo = DatabaseRepository(manager=manager)
    yield repo
    
    # Cleanup
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def _create_sample_report(report_id: str = "REP-TEST-001", encounter_id: str = "ENC-TEST-001") -> ClinicalReport:
    return ClinicalReport(
        id=report_id,
        encounter_id=encounter_id,
        patient_id="CASE-101",
        patient_name="Robert Miller",
        patient_age=62,
        patient_sex="Male",
        chief_complaint="Substernal crushing chest pressure",
        history_of_present_illness="Acute onset 2 hours ago radiating to left arm.",
        vital_signs=VitalSigns(
            heart_rate=102,
            systolic_bp=158,
            diastolic_bp=94,
            respiratory_rate=22,
            temperature_c=36.9,
            spo2_percent=95.0,
        ),
        differential_diagnosis=[
            DifferentialItem(condition="NSTEMI", likelihood=0.88, supporting_points=["Troponin rise", "ST depression"])
        ],
        primary_diagnosis="Non-ST-Segment Elevation Myocardial Infarction (NSTEMI)",
        diagnostic_confidence=0.92,
        clinical_reasoning="Clinical presentation, ECG horizontal ST depressions and elevated troponin.",
        treatment_plan=["Aspirin 325mg", "Ticagrelor 180mg", "Heparin drip"],
        recommended_disposition="Admit to CCU",
    )


def test_database_init_and_status(temp_db):
    status = temp_db.manager.get_status()
    assert status["engine"] in ["postgresql", "sqlite"]
    assert temp_db.count_reports() == 0
    assert temp_db.count_reviews() == 0
    assert temp_db.count_knowledge_chunks() == 0


def test_save_and_retrieve_clinical_report(temp_db):
    report = _create_sample_report()
    saved_id = temp_db.save_report(report, case_id="CASE-101")
    assert saved_id == "REP-TEST-001"
    assert temp_db.count_reports() == 1

    # Retrieve by ID
    loaded_data = temp_db.get_report("REP-TEST-001")
    assert loaded_data is not None
    assert loaded_data["id"] == "REP-TEST-001"
    assert loaded_data["patient_name"] == "Robert Miller"
    assert loaded_data["primary_diagnosis"] == "Non-ST-Segment Elevation Myocardial Infarction (NSTEMI)"
    assert loaded_data["diagnostic_confidence"] == 0.92

    # Reconstitute as Pydantic model
    model = temp_db.get_report_model("REP-TEST-001")
    assert model is not None
    assert model.vital_signs.heart_rate == 102
    assert len(model.treatment_plan) == 3

    # List reports
    all_reports = temp_db.list_reports(case_id="CASE-101")
    assert len(all_reports) == 1


def test_save_and_retrieve_physician_review(temp_db):
    report = _create_sample_report()
    temp_db.save_report(report, case_id="CASE-101")

    review = PhysicianReview(
        id="REV-TEST-001",
        report_id="REP-TEST-001",
        encounter_id="ENC-TEST-001",
        physician_name="Dr. Sarah Johnson, MD",
        reviewed_at=datetime.utcnow(),
        diagnosis_grade=DiagnosisFeedback.CORRECT,
        reasoning_grade=ReasoningFeedback.SOUND,
        tests_grade=TestAppropriatenessFeedback.APPROPRIATE,
        treatment_grade=TreatmentSafetyFeedback.SAFE_AND_OPTIMAL,
        overall_score=5,
        approved=True,
        corrected_diagnosis=None,
        corrected_treatment=["Aspirin 325mg", "Ticagrelor 180mg", "Heparin drip", "Atorvastatin 80mg"],
        physician_feedback_notes="Excellent diagnostic workup and adherence to cardiology guidelines.",
    )

    saved_rev_id = temp_db.save_review(review)
    assert saved_rev_id == "REV-TEST-001"
    assert temp_db.count_reviews() == 1

    # Fetch by ID
    rev_data = temp_db.get_review("REV-TEST-001")
    assert rev_data is not None
    assert rev_data["overall_score"] == 5
    assert rev_data["approved"] is True

    # Fetch by report ID
    rev_by_rep = temp_db.get_review_for_report("REP-TEST-001")
    assert rev_by_rep is not None
    assert rev_by_rep["id"] == "REV-TEST-001"

    # Reconstruct model
    rev_model = temp_db.get_review_model("REV-TEST-001")
    assert rev_model is not None
    assert rev_model.diagnosis_grade == DiagnosisFeedback.CORRECT


def test_save_and_retrieve_dpo_pair(temp_db):
    pair = DPOPreferencePair(
        id="DPO-TEST-001",
        encounter_id="ENC-TEST-001",
        case_id="CASE-101",
        source="HUMAN_PHYSICIAN",
        prompt="Clinical Presentation: 62yo male with severe chest pain.",
        chosen="Immediate DAPT + Anticoagulation + Urgent Cath",
        rejected="Prescribe NSAID and discharge home",
        reward_chosen=0.9,
        reward_rejected=-0.5,
        reward_margin=1.4,
        is_safety_critical=True,
        harrison_citations=["Harrison's Principles of Internal Medicine, Ch. 275"],
    )

    pair_id = temp_db.save_dpo_pair(pair)
    assert pair_id == "DPO-TEST-001"

    all_pairs = temp_db.list_dpo_pairs()
    assert len(all_pairs) == 1
    assert all_pairs[0]["id"] == "DPO-TEST-001"
    assert all_pairs[0]["is_safety_critical"] is True


def test_knowledge_chunks_persistence(temp_db):
    temp_db.save_knowledge_chunk(
        chunk_id="CHUNK-IM-001",
        specialty="INTERNAL_MEDICINE",
        book_title="Harrison's Principles of Internal Medicine",
        chapter="Cardiology",
        topic="Acute Coronary Syndrome",
        content="NSTEMI is diagnosed when myocardial necrosis biomarkers rise without ST elevation.",
        embedding=[0.012, -0.045, 0.128, 0.991],
        metadata={"page": 1978},
    )
    assert temp_db.count_knowledge_chunks() == 1


def test_persistence_across_reconnection():
    """Verifies that data written to SQLite disk survives process / connection teardown."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_file = f.name

    try:
        # Session 1: Write report & review
        mgr1 = DatabaseConnectionManager(sqlite_path=db_file)
        repo1 = DatabaseRepository(manager=mgr1)
        
        rep = _create_sample_report("REP-PERSIST", "ENC-PERSIST")
        repo1.save_report(rep, case_id="CASE-101")
        assert repo1.count_reports() == 1

        # Session 2: Fresh instance pointing to the same file
        mgr2 = DatabaseConnectionManager(sqlite_path=db_file)
        repo2 = DatabaseRepository(manager=mgr2)
        
        assert repo2.count_reports() == 1
        fetched = repo2.get_report_model("REP-PERSIST")
        assert fetched is not None
        assert fetched.patient_name == "Robert Miller"
        assert fetched.primary_diagnosis == rep.primary_diagnosis
    finally:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass


def test_database_api_endpoints():
    """Tests /api/database/status and /api/reports/history endpoints."""
    client = TestClient(app)

    # Health check
    r_health = client.get("/api/health")
    assert r_health.status_code == 200

    # Database status
    r_status = client.get("/api/database/status")
    assert r_status.status_code == 200
    status_data = r_status.json()
    assert "engine" in status_data
    assert "total_reports" in status_data
    assert "total_reviews" in status_data

    # Report history
    r_hist = client.get("/api/reports/history?limit=10")
    assert r_hist.status_code == 200
    hist_data = r_hist.json()
    assert "total" in hist_data
    assert "reports" in hist_data
    assert isinstance(hist_data["reports"], list)

    # Review history
    r_rev = client.get("/api/reviews/history?limit=10")
    assert r_rev.status_code == 200
    rev_data = r_rev.json()
    assert "total" in rev_data
    assert "reviews" in rev_data
