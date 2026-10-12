"""
Tests for Case Pool, SyntheticClinicalCaseBuilder, and Patient Deduplication (Phase 1).
"""

import pytest
from backend.database.repository import DatabaseRepository
from backend.database.connection import DatabaseConnectionManager
from backend.clinical.case_builder import SyntheticClinicalCaseBuilder
from backend.clinical.cases import get_benchmark_case
from backend.clinical.models import LabTestType


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "test_pool.db"
    mgr = DatabaseConnectionManager(sqlite_path=str(db_file))
    return DatabaseRepository(manager=mgr)


def test_case_builder_generates_complete_ground_truth():
    """Verify that SyntheticClinicalCaseBuilder generates rich simulated labs and physical exam."""
    raw_profile = {
        "id": "SYNTH-TEST-01",
        "name": "David Clark",
        "age": 64,
        "sex": "Male",
        "chief_complaint": "Severe retrosternal crushing chest pain radiating to left shoulder",
        "active_conditions": [{"name": "Coronary artery disease"}, {"name": "Hypertension"}],
        "medications": ["Aspirin 81mg", "Lisinopril 10mg"],
        "allergies": ["Penicillin"],
        "baseline_vitals": {"heart_rate": 98, "systolic_bp": 150, "diastolic_bp": 92, "respiratory_rate": 20},
    }

    gt = SyntheticClinicalCaseBuilder.build_from_profile(raw_profile)

    assert gt.id == "SYNTH-TEST-01"
    assert gt.name == "David Clark"
    assert "NSTEMI" in gt.true_diagnosis or "Myocardial Infarction" in gt.true_diagnosis
    assert gt.icd10_code == "I21.4"
    assert len(gt.differential_candidates) >= 3
    assert LabTestType.TROPONIN_I in gt.recommended_labs
    assert LabTestType.ECG_12_LEAD in gt.recommended_labs

    # Crucially verify simulated labs and physical exam are NOT empty
    assert len(gt.simulated_labs) >= 4
    assert "Troponin I / T" in gt.simulated_labs
    assert "12-Lead ECG" in gt.simulated_labs
    assert "Cardiovascular" in gt.physical_exam
    assert "Respiratory" in gt.physical_exam


def test_case_pool_crud_and_status_update(repo):
    """Verify case pool insertion, retrieval, filtering, and status updates."""
    case_item = {
        "id": "POOL-001",
        "name": "Jane Doe",
        "age": 45,
        "sex": "Female",
        "chief_complaint": "Acute productive cough, fever, and right-sided pleuritic chest pain",
        "specialty_category": "INTERNAL_MEDICINE",
        "triage_acuity": "URGENT",
        "difficulty_level": 2,
        "source": "SYNTHEA",
        "status": "UNADMITTED",
    }

    cid = repo.save_case_to_pool(case_item)
    assert cid == "POOL-001"

    # List pool
    pool_cases = repo.list_pool_cases(status="UNADMITTED")
    assert len(pool_cases) == 1
    assert pool_cases[0]["name"] == "Jane Doe"
    assert pool_cases[0]["specialty_category"] == "INTERNAL_MEDICINE"

    # Get single
    retrieved = repo.get_pool_case("POOL-001")
    assert retrieved is not None
    assert retrieved["name"] == "Jane Doe"

    # Update status
    updated = repo.update_pool_case_status("POOL-001", "ADMITTED")
    assert updated is True

    # Confirm it no longer shows in UNADMITTED pool
    unadmitted = repo.list_pool_cases(status="UNADMITTED")
    assert len(unadmitted) == 0


def test_patient_deduplication(repo):
    """Verify that admitting the same patient multiple times returns the active census record."""
    patient_data = {
        "name": "Eleanor Rigby",
        "age": 60,
        "sex": "Female",
        "chief_complaint": "Shortness of breath on exertion",
        "mrn": "MRN-RIGBY-01",
    }

    admitted_1 = repo.admit_patient(patient_data)
    assert admitted_1["mrn"] == "MRN-RIGBY-01"

    # Second admission attempt with identical MRN
    admitted_2 = repo.admit_patient(patient_data)
    assert admitted_2["id"] == admitted_1["id"]
    assert admitted_2["mrn"] == admitted_1["mrn"]

    # Verify count in database is still 1
    total_active = repo.count_patients(status="ADMITTED")
    assert total_active == 1
