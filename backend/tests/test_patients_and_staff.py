"""
Automated Test Suite for Patient Admission Storage and Hospital Staff Management
Tests patient case intake, MRN generation, relational persistence, discharge lifecycles,
staff directory seeding, and FastAPI REST endpoints.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.database.connection import DatabaseConnectionManager
from backend.database.repository import DatabaseRepository
from backend.main import app


@pytest.fixture
def temp_db():
    """Creates an isolated temporary SQLite database for unit tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name

    manager = DatabaseConnectionManager(sqlite_path=temp_path)
    repo = DatabaseRepository(manager=manager)
    yield repo

    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def test_patient_admission_and_discharge_repo(temp_db):
    """Verifies that patient intake, bed assignment, and discharge lifecycle work in repo."""
    patient_data = {
        "name": "Evelyn Reed",
        "age": 47,
        "sex": "Female",
        "chief_complaint": "Acute severe shortness of breath with pleuritic chest pain",
        "history_of_present_illness": "Sudden onset dyspnea 4 hours following long-haul travel.",
        "past_medical_history": ["Mild asthma", "Oral contraceptive use"],
        "medications": ["Albuterol inhaler PRN"],
        "allergies": ["Penicillin (Hives)"],
        "baseline_vitals": {
            "heart_rate": 108,
            "systolic_bp": 118,
            "diastolic_bp": 76,
            "respiratory_rate": 24,
            "spo2": 93.0,
            "temperature_c": 37.1
        },
        "triage_acuity": "EMERGENT",
        "assigned_department": "EMERGENCY",
        "bed_number": "ED-BAY-04"
    }

    admitted = temp_db.admit_patient(patient_data)
    assert admitted["id"].startswith("PAT-")
    assert admitted["mrn"].startswith("MRN-")
    assert admitted["name"] == "Evelyn Reed"
    assert admitted["admission_status"] == "ADMITTED"
    assert admitted["triage_acuity"] == "EMERGENT"
    assert admitted["bed_number"] == "ED-BAY-04"

    # Count patients
    assert temp_db.count_patients() == 1
    assert temp_db.count_patients(status="ADMITTED") == 1
    assert temp_db.count_patients(status="DISCHARGED") == 0

    # Retrieve by ID
    fetched_by_id = temp_db.get_patient(admitted["id"])
    assert fetched_by_id is not None
    assert fetched_by_id["name"] == "Evelyn Reed"
    assert fetched_by_id["chief_complaint"] == patient_data["chief_complaint"]

    # Retrieve by MRN
    fetched_by_mrn = temp_db.get_patient(admitted["mrn"])
    assert fetched_by_mrn is not None
    assert fetched_by_mrn["id"] == admitted["id"]

    # List patients
    patients = temp_db.list_patients()
    assert len(patients) == 1
    assert patients[0]["id"] == admitted["id"]

    # Discharge patient
    discharged = temp_db.discharge_patient(admitted["id"])
    assert discharged is True

    # Verify updated status
    updated_patient = temp_db.get_patient(admitted["id"])
    assert updated_patient["admission_status"] == "DISCHARGED"
    assert temp_db.count_patients(status="DISCHARGED") == 1
    assert temp_db.count_patients(status="ADMITTED") == 0


def test_staff_management_repo(temp_db):
    """Verifies staff default seeding, registration, status updating, and deletion in repo."""
    # Initially empty before seeding
    assert temp_db.count_staff() == 0

    # Seed default hospital team (Dr. Marcus Vance)
    temp_db.seed_default_staff()
    assert temp_db.count_staff() >= 1

    # Verify Dr. Marcus Vance is present
    vance = temp_db.get_staff_member("STAFF-VANCE")
    assert vance is not None
    assert "Marcus Vance" in vance["name"]
    assert vance["role"] == "DOCTOR"
    assert vance["specialty"] == "INTERNAL_MEDICINE"
    assert vance["status"] == "ON_DUTY"

    # Filter by role
    doctors = temp_db.list_staff(role="DOCTOR")
    assert len(doctors) >= 1
    assert any(d["id"] == "STAFF-VANCE" for d in doctors)

    # Add a new custom surgeon
    new_staff = {
        "id": "STAFF-CHOWDHURY",
        "name": "Dr. Tariq Chowdhury",
        "role": "DOCTOR",
        "specialty": "CARDIOTHORACIC_SURGERY",
        "title": "Attending Cardiothoracic Surgeon",
        "department": "SURGERY",
        "status": "ON_DUTY",
        "credentials": "MD, FACS",
        "bio": "Specialist in emergency coronary revascularization and aortic dissections.",
        "total_encounters": 45
    }
    added_id = temp_db.add_staff_member(new_staff)
    assert added_id == "STAFF-CHOWDHURY"

    # Update status to IN_CONSULT
    updated = temp_db.update_staff_status("STAFF-CHOWDHURY", "IN_CONSULT")
    assert updated is True

    fetched = temp_db.get_staff_member("STAFF-CHOWDHURY")
    assert fetched["status"] == "IN_CONSULT"

    # Delete staff member
    deleted = temp_db.delete_staff_member("STAFF-CHOWDHURY")
    assert deleted is True
    assert temp_db.get_staff_member("STAFF-CHOWDHURY") is None



def test_patient_api_endpoints():
    """Tests FastAPI REST endpoints for patient intake, listing, retrieval, and discharge."""
    client = TestClient(app)

    # 1. Admit a new patient
    admit_payload = {
        "name": "Gerald Montgomery",
        "age": 63,
        "sex": "Male",
        "chief_complaint": "Diaphoresis and central crushing chest pressure",
        "history_of_present_illness": "Sudden onset crushing chest pain radiating to left jaw during light exertion.",
        "past_medical_history": ["Type 2 Diabetes Mellitus", "Hyperlipidemia", "Essential Hypertension"],
        "medications": ["Metformin 1000mg BID", "Atorvastatin 40mg QHS", "Lisinopril 20mg daily"],
        "allergies": ["Sulfa drugs (Rash)"],
        "baseline_vitals": {
            "heart_rate": 104,
            "systolic_bp": 142,
            "diastolic_bp": 88,
            "respiratory_rate": 20,
            "spo2": 97.0
        },
        "triage_acuity": "RESUSCITATION",
        "assigned_department": "CARDIOLOGY",
        "bed_number": "CCU-02"
    }

    resp = client.post("/api/patients/admit", json=admit_payload)
    assert resp.status_code == 200, resp.text
    patient = resp.json()
    assert "id" in patient
    assert "mrn" in patient
    assert patient["name"] == "Gerald Montgomery"
    assert patient["admission_status"] == "ADMITTED"
    patient_id = patient["id"]

    # 2. List patients
    resp_list = client.get("/api/patients?limit=10")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert list_data["total"] >= 1
    assert any(p["id"] == patient_id for p in list_data["patients"])

    # 3. Retrieve patient by ID
    resp_get = client.get(f"/api/patients/{patient_id}")
    assert resp_get.status_code == 200
    fetched = resp_get.json()
    assert fetched["id"] == patient_id
    assert fetched["name"] == "Gerald Montgomery"
    assert fetched["bed_number"] == "CCU-02"

    # 4. Discharge patient
    resp_dc = client.post(f"/api/patients/{patient_id}/discharge")
    assert resp_dc.status_code == 200
    dc_data = resp_dc.json()
    assert dc_data["status"] == "DISCHARGED"

    # 5. Verify 404 for nonexistent patient
    resp_404 = client.get("/api/patients/NONEXISTENT-ID-9999")
    assert resp_404.status_code == 404


def test_staff_api_endpoints():
    """Tests FastAPI REST endpoints for staff roster, registration, and duty status updates."""
    client = TestClient(app)

    # 1. List staff roster
    resp = client.get("/api/staff")
    assert resp.status_code == 200
    roster_data = resp.json()
    assert roster_data["total"] >= 1
    assert any(s["id"] == "STAFF-VANCE" for s in roster_data["staff"])

    # 2. Get specific staff member
    resp_vance = client.get("/api/staff/STAFF-VANCE")
    assert resp_vance.status_code == 200
    vance_data = resp_vance.json()
    assert vance_data["name"] == "Dr. Marcus Vance"
    assert vance_data["role"] == "DOCTOR"
    assert "Harrison" in vance_data["bio"] or "Internal Medicine" in vance_data["bio"]

    # 3. Create a new staff member via API
    new_staff_payload = {
        "name": "Dr. Miriam O'Connor",
        "role": "DOCTOR",
        "specialty": "NEUROLOGY",
        "title": "Attending Vascular Neurologist",
        "department": "NEUROLOGY",
        "status": "ON_DUTY",
        "credentials": "MD, PhD",
        "bio": "Specializes in acute ischemic stroke intervention, NIHSS scoring, and neuro-ICU care.",
        "system_prompt": "Acute stroke protocol specialist. Rapid assessment of tPA and thrombectomy candidacy."
    }
    resp_create = client.post("/api/staff", json=new_staff_payload)
    assert resp_create.status_code == 200
    created_staff = resp_create.json()
    assert created_staff["name"] == "Dr. Miriam O'Connor"
    created_id = created_staff["id"]

    # 4. Update status to OFF_DUTY
    resp_status = client.put(f"/api/staff/{created_id}/status", json={"status": "OFF_DUTY"})
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert status_data["status"] == "OFF_DUTY"

    # 5. Verify updated status
    resp_check = client.get(f"/api/staff/{created_id}")
    assert resp_check.status_code == 200
    assert resp_check.json()["status"] == "OFF_DUTY"

    # 6. Delete staff member via API
    resp_del = client.delete(f"/api/staff/{created_id}")
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "DELETED"

    # 7. Verify 404 after deletion and for missing staff
    resp_deleted_check = client.get(f"/api/staff/{created_id}")
    assert resp_deleted_check.status_code == 404

    resp_404 = client.get("/api/staff/STAFF-DOESNOTEXIST")
    assert resp_404.status_code == 404

