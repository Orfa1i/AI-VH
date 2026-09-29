"""
Acceptance criteria tests for STEP 12 (P1.6):
Case validation suite, plausibility rules, batch reporting, and spot-check packet export.
"""

import json
from pathlib import Path
from typing import Any, Dict
import pytest

from vh.cases.validation import (
    CaseValidator,
    BatchCaseValidator,
    VitalsRangeRule,
    UCUMUnitsRule,
    DiagnosticLabConsistencyRule,
    MedicationConditionConsistencyRule,
    TemporalOrderingRule,
    LeakageValidationRule,
    generate_spotcheck_packet,
)
from vh.cases.builder import CaseBuilder, CaseBuilderConfig, ACS_COHORT, DKA_COHORT, CAP_COHORT
from vh.cases.spec import CaseSpec, VisiblePresentation, HiddenResult
from vh.cases.schema import GroundTruth


def _create_sample_spec(
    specialty_slug: str = "acute_coronary_syndrome",
    bp: str = "140/90",
    hr: int = 88,
    rr: int = 18,
    spo2: int = 96,
    temp: float = 37.0,
    presentation: str = "Substernal chest pressure and diaphoresis.",
    history: str = "Hypertension, hyperlipidemia.",
    meds: list = None,
    allergies: list = None,
    hidden_results: list = None,
    primary_dx: str = "Acute Coronary Syndrome",
) -> CaseSpec:
    return CaseSpec(
        case_id=f"TEST-{specialty_slug[:3].upper()}-001",
        specialty="Cardiology",
        patient_ref="PAT-001",
        visible=VisiblePresentation(
            presentation=presentation,
            demographics={"age": 62, "gender": "male"},
            history=history,
            current_medications=meds if meds is not None else ["Lisinopril 10mg", "Atorvastatin 20mg"],
            allergies=allergies if allergies is not None else ["Penicillin"],
            initial_vitals={"bp": bp, "hr": hr, "rr": rr, "spo2": spo2, "temp": temp},
            exam="Cardiovascular exam normal, lungs clear.",
        ),
        hidden=hidden_results if hidden_results is not None else [
            HiddenResult(
                order_code="LAB-TROP",
                order_name="High-Sensitivity Troponin I",
                result="185 ng/L (elevated)",
                turnaround_time_minutes=30,
                category="laboratory",
                loinc_code="49563-0",
            )
        ],
        ground_truth=GroundTruth(
            primary_dx=primary_dx,
            acceptable_differential=["NSTEMI", "Unstable Angina"],
            expected_workup=["12-Lead ECG", "Troponin I"],
            red_flags=["Cardiogenic shock"],
        ),
        metadata={
            "specialty_slug": specialty_slug,
            "lineage": {
                "triage_time": "2026-09-28T10:00:00Z",
                "order_time": "2026-09-28T10:15:00Z",
                "result_time": "2026-09-28T10:45:00Z",
            }
        },
    )


def test_vitals_range_rule_positive_and_negative():
    """Verify VitalsRangeRule validates physiological bounds and catches out-of-range values."""
    rule = VitalsRangeRule()

    # Positive test: physiological vitals
    valid_spec = _create_sample_spec(bp="136/84", hr=78, rr=16, spo2=98, temp=37.0)
    passed, reason = rule.validate(valid_spec)
    assert passed, f"Expected vitals rule to pass: {reason}"

    # Negative test 1: Heart rate outside physiological bounds (HR 320)
    invalid_hr_spec = _create_sample_spec(hr=320)
    passed_hr, reason_hr = rule.validate(invalid_hr_spec)
    assert not passed_hr
    assert "hr" in reason_hr.lower()

    # Negative test 2: Inverted blood pressure (systolic < diastolic: 70/110)
    invalid_bp_spec = _create_sample_spec(bp="70/110")
    passed_bp, reason_bp = rule.validate(invalid_bp_spec)
    assert not passed_bp
    assert "blood pressure" in reason_bp.lower() or "bp" in reason_bp.lower()

    # Negative test 3: Severe hypoxemia out of human survival range (SpO2 30%)
    invalid_spo2_spec = _create_sample_spec(spo2=30)
    passed_spo2, reason_spo2 = rule.validate(invalid_spo2_spec)
    assert not passed_spo2
    assert "spo2" in reason_spo2.lower()


def test_ucum_units_rule_positive_and_negative():
    """Verify UCUMUnitsRule checks standard measurement units on laboratory and diagnostic results."""
    rule = UCUMUnitsRule()

    # Positive test: valid standard units
    valid_spec = _create_sample_spec(
        hidden_results=[
            HiddenResult(
                order_code="LAB-TROP",
                order_name="Troponin",
                result="120 ng/L",
                turnaround_time_minutes=30,
            ),
            HiddenResult(
                order_code="LAB-GLU",
                order_name="Glucose",
                result="420 mg/dL",
                turnaround_time_minutes=20,
            ),
        ]
    )
    passed, reason = rule.validate(valid_spec)
    assert passed, f"Expected UCUM rule to pass: {reason}"

    # Negative test: invalid non-standard unit
    invalid_spec = _create_sample_spec(
        hidden_results=[
            HiddenResult(
                order_code="LAB-BAD",
                order_name="Custom Lab",
                result="150 fl_oz_per_hour",
                turnaround_time_minutes=30,
            )
        ]
    )
    passed_bad, reason_bad = rule.validate(invalid_spec)
    assert not passed_bad
    assert "unit" in reason_bad.lower()


def test_diagnostic_lab_consistency_rule_positive_and_negative():
    """Verify DiagnosticLabConsistencyRule checks concordance between labs and ground truth."""
    rule = DiagnosticLabConsistencyRule()

    # Positive test: DKA with hyperglycemia, high ketones, low bicarb
    valid_dka = CaseSpec(
        case_id="DKA-VALID-001",
        specialty="Endocrinology",
        patient_ref="P-DKA-1",
        visible=VisiblePresentation(
            presentation="Nausea, vomiting, diffuse abdominal pain, polyuria.",
            demographics={"age": 24, "gender": "female"},
            initial_vitals={"bp": "104/68", "hr": 118, "rr": 28, "spo2": 98, "temp": 36.9},
        ),
        hidden=[
            HiddenResult(
                order_code="LAB-BMP",
                order_name="Basic Metabolic Panel",
                result="Glucose 540 mg/dL, Bicarbonate 10 mEq/L, Anion Gap 24",
                turnaround_time_minutes=30,
            ),
            HiddenResult(
                order_code="LAB-BOHB",
                order_name="Beta-Hydroxybutyrate",
                result="7.2 mmol/L (critical high)",
                turnaround_time_minutes=35,
            ),
        ],
        ground_truth=GroundTruth(
            primary_dx="Diabetic Ketoacidosis",
            acceptable_differential=["HHS"],
            expected_workup=["BMP", "VBG"],
            red_flags=["Hypokalemia"],
        ),
        metadata={"specialty_slug": "diabetic_ketoacidosis"},
    )
    passed_dka, reason_dka = rule.validate(valid_dka)
    assert passed_dka, f"Expected DKA rule to pass: {reason_dka}"

    # Negative test: DKA diagnosed with completely normal glucose and normal bicarb (discordant!)
    discordant_dka = CaseSpec(
        case_id="DKA-INVALID-001",
        specialty="Endocrinology",
        patient_ref="P-DKA-2",
        visible=VisiblePresentation(
            presentation="Abdominal pain.",
            demographics={"age": 24, "gender": "female"},
            initial_vitals={"bp": "120/80", "hr": 72, "rr": 16, "spo2": 99, "temp": 37.0},
        ),
        hidden=[
            HiddenResult(
                order_code="LAB-BMP",
                order_name="Basic Metabolic Panel",
                result="Glucose 92 mg/dL, Bicarbonate 26 mEq/L, Anion Gap 8",
                turnaround_time_minutes=30,
            ),
        ],
        ground_truth=GroundTruth(
            primary_dx="Diabetic Ketoacidosis",
            acceptable_differential=[],
            expected_workup=[],
            red_flags=[],
        ),
        metadata={"specialty_slug": "diabetic_ketoacidosis"},
    )
    passed_disc, reason_disc = rule.validate(discordant_dka)
    assert not passed_disc
    assert "dka" in reason_disc.lower() or "glucose" in reason_disc.lower() or "bicarbonate" in reason_disc.lower()


def test_medication_condition_consistency_rule_positive_and_negative():
    """Verify MedicationConditionConsistencyRule checks that medications match condition history."""
    rule = MedicationConditionConsistencyRule()

    # Positive test: ACS patient taking Lisinopril and Atorvastatin
    valid_spec = _create_sample_spec(meds=["Lisinopril 10mg daily", "Atorvastatin 40mg daily"])
    passed, reason = rule.validate(valid_spec)
    assert passed, f"Expected medication rule to pass: {reason}"

    # Negative test: Patient prescribed pediatric chemotherapy for adult ACS with no cancer history
    invalid_spec = _create_sample_spec(
        meds=["Vincristine 2mg IV weekly", "Doxorubicin 50mg/m2 IV"]
    )
    passed_inv, reason_inv = rule.validate(invalid_spec)
    assert not passed_inv
    assert "medication" in reason_inv.lower()


def test_temporal_ordering_rule_positive_and_negative():
    """Verify TemporalOrderingRule validates chronological progression of encounter events."""
    rule = TemporalOrderingRule()

    # Positive test: triage (10:00) -> order (10:15) -> result (10:45)
    valid_spec = _create_sample_spec()
    passed, reason = rule.validate(valid_spec)
    assert passed, f"Expected temporal rule to pass: {reason}"

    # Negative test: lab result arrives before the triage encounter took place
    invalid_spec = _create_sample_spec()
    invalid_spec.metadata["lineage"] = {
        "triage_time": "2026-09-28T10:00:00Z",
        "order_time": "2026-09-28T10:15:00Z",
        "result_time": "2026-09-28T09:30:00Z",  # 30 mins before triage!
    }
    passed_inv, reason_inv = rule.validate(invalid_spec)
    assert not passed_inv
    assert "temporal" in reason_inv.lower() or "time" in reason_inv.lower()


def test_leakage_validation_rule_positive_and_negative():
    """Verify LeakageValidationRule enforces zero diagnostic terms in visible presentation."""
    rule = LeakageValidationRule()

    # Positive test: purely phenomenological narrative
    valid_spec = _create_sample_spec(
        presentation="Crushing substernal pressure, diaphoresis, and shortness of breath."
    )
    passed, reason = rule.validate(valid_spec)
    assert passed, f"Expected leakage rule to pass: {reason}"

    # Negative test: visible presentation leaks the diagnosis
    leaked_spec = _create_sample_spec(
        presentation="Patient admitted with Acute Myocardial Infarction and STEMI."
    )
    passed_leak, reason_leak = rule.validate(leaked_spec)
    assert not passed_leak
    assert "leakage" in reason_leak.lower()


def test_500_case_batch_meets_thresholds(tmp_path):
    """Acceptance criterion 2: A 500-case batch meets the cases.* thresholds."""
    # Generate 500-case batch using CaseBuilder
    builder = CaseBuilder(config=CaseBuilderConfig(batch_size=500, seed=1337))
    batch = builder.build_batch(count=500, seed=1337)
    assert len(batch) == 500

    report_path = tmp_path / "cases_validation_report.json"
    batch_validator = BatchCaseValidator()
    report = batch_validator.validate_batch(batch, report_path=report_path)

    # Thresholds from configs/thresholds.yaml:
    # cases.leakage_count: 0
    # cases.plausibility_pass_rate: 1.0
    assert report["total_cases"] == 500
    assert report["leakage_count"] == 0, f"Expected 0 leakage defects, found {report['leakage_count']}"
    assert report["plausibility_pass_rate"] == 1.0, f"Expected 1.0 pass rate, got {report['plausibility_pass_rate']}"

    # Verify report JSON artifact was written
    assert report_path.exists()
    saved_data = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_data["total_cases"] == 500


def test_spotcheck_packet_generation_and_seed_recording(tmp_path):
    """Acceptance criterion 3: Spot-check packet generated with its seed recorded."""
    builder = CaseBuilder(config=CaseBuilderConfig(batch_size=60, seed=1337))
    cases = builder.build_batch(count=60, seed=1337)

    output_packet = tmp_path / "phase-1-spotcheck-packet.md"
    spotcheck_seed = 42

    result = generate_spotcheck_packet(
        cases=cases,
        sample_size=50,
        seed=spotcheck_seed,
        output_file=output_packet,
    )

    assert result["cases_sampled"] == 50
    assert result["seed"] == spotcheck_seed
    assert output_packet.exists()

    content = output_packet.read_text(encoding="utf-8")

    # Verify seed is explicitly recorded in packet
    assert f"Random Seed: `{spotcheck_seed}`" in content or f"Seed: {spotcheck_seed}" in content

    # Verify defect checklist exists
    assert "Defect Checklist" in content
    assert "Clinical Plausibility" in content
    assert "Zero Diagnostic Leakage" in content
    assert "Appropriate Differential & Workup" in content
