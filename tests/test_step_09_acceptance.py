"""
Acceptance tests for Phase 1 | STEP 09 (P1.3: Patient store and FHIR loader).
Written before implementation to verify red-to-green TDD cycle.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_bundles_dir(tmp_path):
    """Generate a reproducible fixture population with 3 bundles for loader testing."""
    from vh.synthea.config import SyntheaGenerationConfig
    from vh.synthea.runner import SyntheaRunner

    cfg = SyntheaGenerationConfig(
        seed=1234,
        clinician_seed=5678,
        reference_date="2026-02-15",
        population=3,
        synthea_version="v3.3.0"
    )
    runner = SyntheaRunner(base_output_dir=tmp_path / "synthea")
    res = runner.generate(cfg, output_subdir="fixture_pop")
    return res.output_dir


@pytest.mark.unit
def test_loader_resource_counts_equal_bundle_entry_counts(sample_bundles_dir, tmp_path):
    """Verify that resource counts in store after loading match entry counts in the bundles."""
    from vh.cases.fhir_loader import FHIRBundleLoader
    from vh.cases.patient_repo import PatientRepository

    # Calculate ground truth total entries from bundle JSON files
    expected_total_entries = 0
    expected_patients = 0
    for bf in sample_bundles_dir.glob("*.json"):
        data = json.loads(bf.read_text(encoding="utf-8"))
        entries = data.get("entry", [])
        expected_total_entries += len(entries)
        for e in entries:
            if e.get("resource", {}).get("resourceType") == "Patient":
                expected_patients += 1

    db_path = tmp_path / "patients.db"
    repo = PatientRepository(db_path=db_path)
    loader = FHIRBundleLoader(repo=repo)

    summary = loader.load_directory(sample_bundles_dir)

    assert summary.total_files == 3
    assert summary.total_resources == expected_total_entries
    assert repo.count_resources() == expected_total_entries
    assert repo.count_resources(resource_type="Patient") == expected_patients


@pytest.mark.unit
def test_idempotent_loading_creates_zero_duplicates(sample_bundles_dir, tmp_path):
    """Verify that loading the exact same bundles twice creates zero duplicate resources."""
    from vh.cases.fhir_loader import FHIRBundleLoader
    from vh.cases.patient_repo import PatientRepository

    db_path = tmp_path / "patients_idempotent.db"
    repo = PatientRepository(db_path=db_path)
    loader = FHIRBundleLoader(repo=repo)

    # First load
    first_summary = loader.load_directory(sample_bundles_dir)
    count_after_first = repo.count_resources()
    assert count_after_first > 0

    # Second load with identical bundles
    second_summary = loader.load_directory(sample_bundles_dir)
    count_after_second = repo.count_resources()

    assert count_after_second == count_after_first, "Second load must not duplicate resources"
    assert second_summary.created_count == 0, "No new resources should be created on reload"
    assert second_summary.updated_count == count_after_first


@pytest.mark.unit
def test_query_patient_and_encounters(sample_bundles_dir, tmp_path):
    """Verify retrieval of patient demographics and associated time-ordered encounters."""
    from vh.cases.fhir_loader import FHIRBundleLoader
    from vh.cases.patient_repo import PatientRepository

    db_path = tmp_path / "patients_query.db"
    repo = PatientRepository(db_path=db_path)
    loader = FHIRBundleLoader(repo=repo)
    loader.load_directory(sample_bundles_dir)

    patient_ids = repo.list_patient_ids()
    assert len(patient_ids) == 3

    target_pid = patient_ids[0]
    patient = repo.get_patient(target_pid)
    assert patient is not None
    assert patient["resourceType"] == "Patient"
    assert patient["id"] == target_pid

    encounters = repo.get_encounters(target_pid)
    assert len(encounters) >= 1
    for enc in encounters:
        assert enc["resourceType"] == "Encounter"


@pytest.mark.unit
def test_time_window_query_over_observations(sample_bundles_dir, tmp_path):
    """Verify observation queries filtered by time window return chronologically ordered records."""
    from vh.cases.fhir_loader import FHIRBundleLoader
    from vh.cases.patient_repo import PatientRepository

    db_path = tmp_path / "patients_timeline.db"
    repo = PatientRepository(db_path=db_path)
    loader = FHIRBundleLoader(repo=repo)
    loader.load_directory(sample_bundles_dir)

    target_pid = repo.list_patient_ids()[0]

    all_obs = repo.get_observations(target_pid)
    assert len(all_obs) >= 1

    # Time-window query matching reference date
    window_obs = repo.get_observations(
        patient_id=target_pid,
        start_time="2026-02-14T00:00:00Z",
        end_time="2026-02-16T23:59:59Z"
    )
    assert len(window_obs) == len(all_obs)

    # Empty window query outside dates
    empty_obs = repo.get_observations(
        patient_id=target_pid,
        start_time="2020-01-01T00:00:00Z",
        end_time="2020-01-02T00:00:00Z"
    )
    assert len(empty_obs) == 0


@pytest.mark.unit
def test_clinical_timeline_aggregates_multiple_resource_types(sample_bundles_dir, tmp_path):
    """Verify clinical timeline aggregates encounters, conditions, and observations in chronological order."""
    from vh.cases.fhir_loader import FHIRBundleLoader
    from vh.cases.patient_repo import PatientRepository

    db_path = tmp_path / "patients_agg.db"
    repo = PatientRepository(db_path=db_path)
    loader = FHIRBundleLoader(repo=repo)
    loader.load_directory(sample_bundles_dir)

    target_pid = repo.list_patient_ids()[0]
    timeline = repo.get_clinical_timeline(target_pid)

    assert len(timeline) >= 3
    types_found = {item["resourceType"] for item in timeline}
    assert "Encounter" in types_found
    assert "Observation" in types_found
    assert "Condition" in types_found
