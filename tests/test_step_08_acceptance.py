"""
Acceptance tests for Phase 1 | STEP 08 (P1.2: Custom Synthea modules for target specialties).
Written before implementation to verify red-to-green TDD cycle.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CUSTOM_MODULES_DIR = REPO_ROOT / "synthea" / "modules" / "custom"


@pytest.mark.unit
def test_custom_modules_exist_and_validate_state_machine_schema():
    """Verify that all target specialty modules exist and parse as valid Synthea Generic Module state machines."""
    from vh.synthea.modules.validator import validate_module_file

    expected_modules = [
        "acute_coronary_syndrome.json",
        "community_acquired_pneumonia.json",
        "diabetic_ketoacidosis.json",
    ]

    assert CUSTOM_MODULES_DIR.exists(), f"Custom modules directory missing: {CUSTOM_MODULES_DIR}"

    for mod_name in expected_modules:
        mod_path = CUSTOM_MODULES_DIR / mod_name
        assert mod_path.exists(), f"Missing custom module file: {mod_path}"
        report = validate_module_file(mod_path)
        assert report["valid"] is True, f"Module validation failed for {mod_name}: {report.get('error')}"
        assert report["has_initial"] is True
        assert report["terminal_count"] >= 1
        assert report["state_count"] >= 5


@pytest.mark.unit
def test_observation_codes_are_valid_loinc_with_ucum_units():
    """Verify all Observation states in custom modules use validated LOINC codes and UCUM units."""
    from vh.synthea.modules.validator import validate_terminology_in_directory

    report = validate_terminology_in_directory(CUSTOM_MODULES_DIR)
    assert report["invalid_loinc_codes"] == []
    assert report["invalid_ucum_units"] == []
    assert report["total_observations_checked"] >= 10


@pytest.mark.unit
def test_medication_codes_are_valid_rxnorm():
    """Verify all MedicationOrder states in custom modules use validated RxNorm codes."""
    from vh.synthea.modules.validator import validate_terminology_in_directory

    report = validate_terminology_in_directory(CUSTOM_MODULES_DIR)
    assert report["invalid_rxnorm_codes"] == []
    assert report["total_medications_checked"] >= 5


@pytest.mark.unit
def test_target_condition_prevalence_in_1000_patient_simulation():
    """Verify in a 1,000-patient simulation that conditions appear within configured clinical prevalence ranges."""
    from vh.synthea.modules.simulator import ModuleSimulator

    simulator = ModuleSimulator(modules_dir=CUSTOM_MODULES_DIR, seed=42)
    results = simulator.simulate_population(population_size=1000)

    # 1. Acute Coronary Syndrome: target 1.5% to 6.0%
    acs_rate = results["prevalence"]["acute_coronary_syndrome"]
    assert 0.015 <= acs_rate <= 0.060, f"ACS prevalence {acs_rate:.3f} outside expected range [0.015, 0.060]"

    # 2. Community-Acquired Pneumonia: target 2.0% to 7.0%
    cap_rate = results["prevalence"]["community_acquired_pneumonia"]
    assert 0.020 <= cap_rate <= 0.070, f"CAP prevalence {cap_rate:.3f} outside expected range [0.020, 0.070]"

    # 3. Diabetic Ketoacidosis: target 0.5% to 3.5%
    dka_rate = results["prevalence"]["diabetic_ketoacidosis"]
    assert 0.005 <= dka_rate <= 0.035, f"DKA prevalence {dka_rate:.3f} outside expected range [0.005, 0.035]"


@pytest.mark.unit
def test_clinical_assumptions_readme_documents_all_specialties():
    """Verify synthea/modules/custom/README.md thoroughly documents clinical assumptions and guidelines."""
    readme_path = CUSTOM_MODULES_DIR / "README.md"
    assert readme_path.exists(), "synthea/modules/custom/README.md must exist for physician checkpoint H1"

    content = readme_path.read_text(encoding="utf-8")
    assert "Acute Coronary Syndrome" in content
    assert "Community-Acquired Pneumonia" in content
    assert "Diabetic Ketoacidosis" in content
    assert "LOINC" in content
    assert "RxNorm" in content
    assert "SNOMED" in content
