"""
Unit and integration tests for Synthea FHIR R4 Synthetic Patient Integration.
Validates adapter parsing, timeline ordering, service caching, internal API endpoints,
hospital admission bridge, and non-clinical synthetic disclaimers.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from vh.synthea.config import SyntheaGenerationConfig
from vh.synthea.fhir_adapter import FHIRR4Adapter, TimelineEvent, calculate_age
from vh.synthea.service import SYNTHETIC_DISCLAIMER, demo_data_service
from backend.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client():
    """TestClient instance for backend FastAPI application."""
    return TestClient(app)


@pytest.mark.unit
def test_fhir_adapter_parses_all_nine_resources():
    """Verify that the FHIR R4 adapter parses all 9 resource categories from demo patient 1."""
    demo_file = REPO_ROOT / "data" / "synthea" / "demo_patients" / "pat_001_nstemi.json"
    assert demo_file.exists(), f"Demo file missing: {demo_file}"

    bundle_dict = json.loads(demo_file.read_text(encoding="utf-8"))
    profile, events = FHIRR4Adapter.parse_bundle(bundle_dict)

    # Patient assertions
    assert profile.id == "pat-demo-001"
    assert profile.name == "Robert Thomas Miller"
    assert profile.gender == "male"
    assert profile.age == 62
    assert profile.city == "Boston"
    assert profile.state == "Massachusetts"

    # Clinical resource assertions
    assert len(profile.recent_encounters) >= 1
    assert len(profile.active_conditions) >= 2
    assert len(profile.current_medications) >= 2
    assert len(profile.allergies) >= 1
    assert len(profile.procedures) >= 1
    assert len(profile.immunizations) >= 1
    assert len(profile.care_plans) >= 1
    assert "heart_rate" in profile.latest_vitals

    # Check timeline ordering (strictly reverse chronological)
    assert len(events) >= 10
    for idx in range(len(events) - 1):
        assert events[idx].timestamp >= events[idx + 1].timestamp, (
            f"Timeline not sorted reverse chronologically at index {idx}: "
            f"{events[idx].timestamp} < {events[idx + 1].timestamp}"
        )


@pytest.mark.unit
def test_demo_data_service_loads_bundled_patients():
    """Verify that DemoDataService indexes all bundled demo patients on initialization."""
    patients = demo_data_service.list_patients()
    assert len(patients) >= 5

    patient_ids = [p.id for p in patients]
    assert "pat-demo-001" in patient_ids
    assert "pat-demo-002" in patient_ids
    assert "pat-demo-003" in patient_ids
    assert "pat-demo-004" in patient_ids
    assert "pat-demo-005" in patient_ids

    # Check retrieving individual profile and timeline
    prof = demo_data_service.get_patient_profile("pat-demo-002")
    assert prof is not None
    assert prof.name == "Margaret Ann Jenkins"
    assert prof.gender == "female"

    timeline = demo_data_service.get_patient_timeline("pat-demo-003")
    assert timeline is not None
    assert timeline.patient_name == "Tariq Hassan Al-Mansoor"
    assert timeline.total_events > 0

    raw = demo_data_service.get_raw_bundle("pat-demo-001")
    assert raw is not None
    assert raw.get("resourceType") == "Bundle"


@pytest.mark.unit
def test_api_get_demo_patients_list(client):
    """Verify GET /api/demo-patients returns list of patient summaries and disclaimer."""
    res = client.get("/api/demo-patients")
    assert res.status_code == 200

    data = res.json()
    assert "disclaimer" in data
    assert SYNTHETIC_DISCLAIMER in data["disclaimer"]
    assert data["total"] >= 5
    assert len(data["patients"]) >= 5

    first = data["patients"][0]
    assert "id" in first
    assert "mrn" in first
    assert "name" in first
    assert "gender" in first
    assert "active_condition_count" in first
    assert "encounter_count" in first


@pytest.mark.unit
def test_api_get_demo_patient_profile_and_404(client):
    """Verify GET /api/demo-patients/{id} retrieves full profile or returns 404."""
    res = client.get("/api/demo-patients/pat-demo-001")
    assert res.status_code == 200

    data = res.json()
    assert data["name"] == "Robert Thomas Miller"
    assert data["disclaimer"] == SYNTHETIC_DISCLAIMER
    assert len(data["active_conditions"]) >= 2
    assert len(data["current_medications"]) >= 2

    # Check 404 for invalid ID
    res_404 = client.get("/api/demo-patients/nonexistent-patient-999")
    assert res_404.status_code == 404


@pytest.mark.unit
def test_api_get_demo_patient_timeline(client):
    """Verify GET /api/demo-patients/{id}/timeline returns chronological events."""
    res = client.get("/api/demo-patients/pat-demo-001/timeline")
    assert res.status_code == 200

    data = res.json()
    assert data["patient_name"] == "Robert Thomas Miller"
    assert data["total_events"] >= 10
    events = data["events"]
    assert len(events) >= 10

    # Verify event fields
    ev = events[0]
    assert "id" in ev
    assert "resource_type" in ev
    assert "category" in ev
    assert "timestamp" in ev
    assert "display_date" in ev
    assert "title" in ev


@pytest.mark.unit
def test_api_get_raw_fhir_bundle(client):
    """Verify GET /api/demo-patients/{id}/raw returns unmodified FHIR R4 Bundle."""
    res = client.get("/api/demo-patients/pat-demo-001/raw")
    assert res.status_code == 200

    bundle = res.json()
    assert bundle.get("resourceType") == "Bundle"
    assert bundle.get("type") == "transaction"
    assert isinstance(bundle.get("entry"), list)


@pytest.mark.integration
def test_api_generate_synthetic_patients(client):
    """Verify POST /api/demo-patients/generate generates and indexes new patients."""
    payload = {
        "population": 2,
        "seed": 9182,
        "clinician_seed": 777,
        "reference_date": "2026-04-01",
        "state": "California",
        "gender": "F",
        "age_range": [30, 60],
        "allow_docker": False,
    }

    res = client.post("/api/demo-patients/generate", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "success"
    assert data["population_generated"] == 2
    assert len(data["patient_ids"]) == 2

    # Check that newly generated patient can now be retrieved via GET
    new_id = data["patient_ids"][0]
    get_res = client.get(f"/api/demo-patients/{new_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == new_id
    assert get_res.json()["gender"] == "female"


@pytest.mark.integration
def test_api_admit_demo_patient_to_hospital(client):
    """Verify POST /api/demo-patients/{id}/admit bridges patient into hospital database."""
    res = client.post("/api/demo-patients/pat-demo-001/admit")
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "ADMITTED"
    assert "patient" in data
    admitted = data["patient"]
    assert admitted["name"] == "Robert Thomas Miller"

    # Confirm patient appears in hospital patient census endpoint
    census_res = client.get("/api/patients")
    assert census_res.status_code == 200
    admitted_names = [p["name"] for p in census_res.json().get("patients", [])]
    assert "Robert Thomas Miller" in admitted_names


@pytest.mark.unit
def test_zero_em_dash_in_synthea_integration():
    """Verify zero em-dash characters in all newly authored synthea code and documentation."""
    files_to_check = [
        REPO_ROOT / "src" / "vh" / "synthea" / "fhir_adapter.py",
        REPO_ROOT / "src" / "vh" / "synthea" / "service.py",
        REPO_ROOT / "backend" / "api" / "demo_patients.py",
        REPO_ROOT / "docs" / "SYNTHEA_INTEGRATION.md",
        REPO_ROOT / "frontend" / "src" / "components" / "synthea" / "SyntheticTimelineModal.tsx",
        REPO_ROOT / "frontend" / "src" / "components" / "synthea" / "DemoPatientsSection.tsx",
    ]

    for path in files_to_check:
        assert path.exists(), f"File does not exist: {path}"
        text = path.read_text(encoding="utf-8")
        assert "\u2014" not in text, f"Found em-dash in {path.name}"
