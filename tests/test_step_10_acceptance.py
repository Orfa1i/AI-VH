"""
Acceptance criteria tests for STEP 10 (P1.4):
Case specification schema, AgentView data isolation, and lossless GoldenCase round-trip.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set
import pytest

from vh.cases.schema import GoldenCase, GroundTruth, SupportingReference
from vh.cases.spec import (
    CaseSpec,
    AgentView,
    VisiblePresentation,
    HiddenResult,
    ReleasedResult,
    DataIsolationError,
)

FORBIDDEN_LEAKAGE_KEYS: Set[str] = {
    "hidden",
    "hidden_results",
    "_hidden",
    "_hidden_results",
    "ground_truth",
    "_ground_truth",
    "primary_dx",
    "acceptable_differential",
    "expected_workup",
    "red_flags",
}


def _recursive_key_leakage_check(node: Any, forbidden_keys: Set[str]) -> None:
    """Recursively verify that no dictionary key or element matches forbidden keys."""
    if isinstance(node, dict):
        for key, value in node.items():
            key_lower = str(key).strip().lower()
            assert key_lower not in forbidden_keys, f"Security leakage: forbidden key '{key}' found in AgentView serialization!"
            _recursive_key_leakage_check(value, forbidden_keys)
    elif isinstance(node, list):
        for item in node:
            _recursive_key_leakage_check(item, forbidden_keys)


def test_case_spec_structure_and_validation():
    """Verify CaseSpec structure conforms to required visible, hidden, and ground_truth parts."""
    visible = VisiblePresentation(
        presentation="62-year-old male with acute substernal chest pressure.",
        demographics={"age": 62, "gender": "male"},
        history="Hypertension, 20 pack-year smoking history.",
        current_medications=["Lisinopril 10mg daily"],
        allergies=["Penicillin"],
        initial_vitals={"bp": "142/88", "hr": 92, "rr": 18, "spo2": 96, "temp": 37.1},
        exam="Diaphoretic, regular rate and rhythm, clear lung fields.",
    )
    hidden = [
        HiddenResult(
            order_code="LAB-TROP",
            order_name="High-Sensitivity Troponin I",
            result="145 ng/L (elevated, reference < 14 ng/L)",
            turnaround_time_minutes=30,
            category="laboratory",
            loinc_code="49563-0",
        ),
        HiddenResult(
            order_code="DX-ECG",
            order_name="12-Lead Electrocardiogram",
            result="ST-elevation in leads V1-V4 with reciprocal depression in III and aVF",
            turnaround_time_minutes=10,
            category="diagnostic",
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Acute Anterior STEMI",
        acceptable_differential=["NSTEMI", "Acute Pericarditis", "Aortic Dissection"],
        expected_workup=["12-Lead ECG", "High-Sensitivity Troponin", "Echocardiogram", "Emergent Angiography"],
        red_flags=["Cardiogenic shock", "Ventricular tachycardia", "Hypotension"],
    )

    spec = CaseSpec(
        case_id="CASE-ACS-001",
        specialty="Cardiology",
        patient_ref="PAT-001",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
        status="verified",
        version="1.0.0",
    )

    assert spec.case_id == "CASE-ACS-001"
    assert spec.visible.presentation.startswith("62-year-old male")
    assert len(spec.hidden) == 2
    assert spec.ground_truth.primary_dx == "Acute Anterior STEMI"


def test_agent_view_serialization_zero_leakage():
    """Acceptance criterion 1: Serialising an AgentView contains no hidden or ground-truth keys."""
    visible = VisiblePresentation(
        presentation="45-year-old female with worsening cough and dyspnea.",
        demographics={"age": 45, "gender": "female"},
        history="Asthma, seasonal allergies.",
        current_medications=["Albuterol inhaler PRN"],
        allergies=["Sulfa drugs"],
        initial_vitals={"bp": "118/76", "hr": 104, "rr": 24, "spo2": 91, "temp": 38.8},
    )
    hidden = [
        HiddenResult(
            order_code="RAD-CXR",
            order_name="Chest X-Ray PA/Lateral",
            result="Right lower lobe consolidation consistent with bacterial pneumonia.",
            turnaround_time_minutes=45,
        ),
        HiddenResult(
            order_code="LAB-WBC",
            order_name="Complete Blood Count",
            result="WBC 16.2 x10^3/uL with 88% neutrophils",
            turnaround_time_minutes=30,
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Community-Acquired Pneumonia",
        acceptable_differential=["Aspiration Pneumonia", "Acute Bronchitis"],
        expected_workup=["Chest X-Ray", "CBC", "Blood Cultures", "Sputum Culture"],
        red_flags=["Hypoxemia refractory to oxygen", "Septic shock"],
    )

    spec = CaseSpec(
        case_id="CASE-CAP-001",
        specialty="Pulmonology",
        patient_ref="PAT-002",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
    )

    view = spec.to_agent_view()
    assert isinstance(view, AgentView)

    # 1. Test model_dump() dictionary representation
    dumped_dict = view.model_dump()
    _recursive_key_leakage_check(dumped_dict, FORBIDDEN_LEAKAGE_KEYS)

    # 2. Test JSON string serialization
    json_str = view.model_dump_json()
    parsed_json = json.loads(json_str)
    _recursive_key_leakage_check(parsed_json, FORBIDDEN_LEAKAGE_KEYS)

    # 3. Textual content scan: diagnosis and hidden findings must not leak into agent view JSON
    assert "Community-Acquired Pneumonia" not in json_str
    assert "Right lower lobe consolidation" not in json_str
    assert "Septic shock" not in json_str


def test_agent_view_access_attempts_raise():
    """Acceptance criterion 2: Any attempt to reach hidden data or ground truth from an AgentView raises."""
    visible = VisiblePresentation(
        presentation="28-year-old male with severe polyuria and vomiting.",
        demographics={"age": 28, "gender": "male"},
        history="Type 1 Diabetes Mellitus.",
        current_medications=["Insulin Glargine 20u qHS"],
        allergies=[],
        initial_vitals={"bp": "98/62", "hr": 118, "rr": 28, "spo2": 98, "temp": 36.9},
    )
    spec = CaseSpec(
        case_id="CASE-DKA-001",
        specialty="Endocrinology",
        patient_ref="PAT-003",
        visible=visible,
        hidden=[
            HiddenResult(
                order_code="LAB-BMP",
                order_name="Basic Metabolic Panel",
                result="Glucose 480 mg/dL, Bicarbonate 8 mEq/L, Anion Gap 24",
                turnaround_time_minutes=30,
            )
        ],
        ground_truth=GroundTruth(
            primary_dx="Diabetic Ketoacidosis",
            acceptable_differential=["Hyperosmolar Hyperglycemic State", "Sepsis"],
            expected_workup=["BMP", "Venous Blood Gas", "Serum Ketones", "Urinalysis"],
            red_flags=["Hypokalemia", "Cerebral edema", "Severe acidemia"],
        ),
    )

    view = spec.to_agent_view()

    # Any dot-attribute access to hidden or ground_truth must raise DataIsolationError or PermissionError
    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.hidden

    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.hidden_results

    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.ground_truth

    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.primary_dx

    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.acceptable_differential

    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.expected_workup

    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = view.red_flags

    # Any dictionary-style subscript access must raise
    with pytest.raises((DataIsolationError, PermissionError, KeyError)):
        _ = view["hidden"]

    with pytest.raises((DataIsolationError, PermissionError, KeyError)):
        _ = view["ground_truth"]

    # Any get() lookup must raise
    with pytest.raises((DataIsolationError, PermissionError, KeyError)):
        _ = view.get("hidden")

    with pytest.raises((DataIsolationError, PermissionError, KeyError)):
        _ = view.get("ground_truth")


def test_agent_view_logged_order_release():
    """Verify that hidden results arrive only through an explicit logged release(order) call."""
    visible = VisiblePresentation(
        presentation="55-year-old female with sudden tearing chest pain.",
        demographics={"age": 55, "gender": "female"},
        history="Uncontrolled hypertension.",
        current_medications=[],
        allergies=[],
        initial_vitals={"bp": "190/110", "hr": 96, "rr": 20, "spo2": 97, "temp": 37.0},
    )
    spec = CaseSpec(
        case_id="CASE-AOR-001",
        specialty="Vascular Surgery",
        patient_ref="PAT-004",
        visible=visible,
        hidden=[
            HiddenResult(
                order_code="CTA-CHEST",
                order_name="CT Angiography Chest",
                result="Type A aortic dissection extending from aortic root to descending aorta.",
                turnaround_time_minutes=40,
            ),
            HiddenResult(
                order_code="LAB-CBC",
                order_name="Complete Blood Count",
                result="Hemoglobin 13.5 g/dL, Platelets 220k",
                turnaround_time_minutes=25,
            ),
        ],
        ground_truth=GroundTruth(
            primary_dx="Stanford Type A Aortic Dissection",
            acceptable_differential=["Acute Coronary Syndrome", "Pulmonary Embolism"],
            expected_workup=["CT Angiogram Chest/Abdomen/Pelvis", "Bedside TTE"],
            red_flags=["Cardiac tamponade", "Aortic rupture", "Hypotension"],
        ),
    )

    audit_logs: List[Dict[str, Any]] = []

    def mock_audit_logger(event: Dict[str, Any]) -> None:
        audit_logs.append(event)

    # Initial AgentView has no released results
    view = spec.to_agent_view()
    assert len(view.released_results) == 0
    assert not view.has_released("CTA-CHEST")

    # Release CTA-CHEST with audit logging
    released = spec.release("CTA-CHEST", audit_logger=mock_audit_logger)
    assert isinstance(released, ReleasedResult)
    assert released.order_code == "CTA-CHEST"
    assert "Type A aortic dissection" in released.result
    assert released.turnaround_time_minutes == 40

    # Verify audit log was recorded
    assert len(audit_logs) == 1
    assert audit_logs[0]["case_id"] == "CASE-AOR-001"
    assert audit_logs[0]["order_code"] == "CTA-CHEST"
    assert audit_logs[0]["turnaround_time_minutes"] == 40
    assert "timestamp" in audit_logs[0]

    # Incorporate released result into view
    updated_view = view.with_released_result(released)
    assert len(updated_view.released_results) == 1
    assert updated_view.has_released("CTA-CHEST")
    assert updated_view.get_released_result("CTA-CHEST") == released.result

    # Unreleased result is still not accessible
    assert not updated_view.has_released("LAB-CBC")
    assert updated_view.get_released_result("LAB-CBC") is None

    # Even with released result, ground truth remains strictly isolated
    with pytest.raises((DataIsolationError, PermissionError, AttributeError)):
        _ = updated_view.ground_truth

    # Serialization of updated view still contains zero forbidden keys
    dumped = updated_view.model_dump()
    _recursive_key_leakage_check(dumped, FORBIDDEN_LEAKAGE_KEYS)


def test_golden_case_round_trip_synthetic():
    """Acceptance criterion 3: Golden case to CaseSpec round-trip is lossless on synthetic case."""
    original_golden = GoldenCase(
        case_id="GOLDEN-TEST-001",
        specialty="Cardiology",
        patient_ref="PAT-SYNTH-999",
        visible_presentation={
            "chief_complaint": "Acute substernal pressure and diaphoresis",
            "history": "Hypertension, Hyperlipidemia, family history of premature CAD.",
            "vitals": {"bp": "138/86", "hr": 84, "rr": 18, "spo2": 97, "temp": 37.0},
            "exam": "S1/S2 present, no murmurs, lungs clear to auscultation bilaterally.",
        },
        hidden_results=[
            {"order": "Cardiac Enzymes", "result": "High-sensitivity Troponin I 280 ng/L"},
            {"order": "12-Lead ECG", "result": "Anterior ST elevation in V2-V5"},
        ],
        ground_truth=GroundTruth(
            primary_dx="Acute Anterior STEMI",
            acceptable_differential=["NSTEMI", "Acute Myopericarditis"],
            expected_workup=["12-Lead ECG", "Troponin I", "Emergent Coronary Angiography"],
            red_flags=["Ventricular fibrillation", "Cardiogenic shock"],
        ),
        supporting_references=[
            SupportingReference(
                source="Harrison's Principles of Internal Medicine",
                locator="Chapter 269",
                note="Management of STEMI clinical pathways",
            )
        ],
        status="verified",
        reviewer="Dr. Marcus Vance, MD",
        reviewed_at="2026-09-28",
        version="1.0.0",
    )

    # Convert to CaseSpec
    case_spec = CaseSpec.from_golden_case(original_golden)
    assert case_spec.case_id == original_golden.case_id
    assert case_spec.specialty == original_golden.specialty
    assert case_spec.patient_ref == original_golden.patient_ref

    # Convert back to GoldenCase
    restored_golden = case_spec.to_golden_case()
    assert restored_golden.model_dump() == original_golden.model_dump()


def test_golden_case_round_trip_all_golden_v1_cases():
    """Acceptance criterion 3: Golden case to CaseSpec round-trip is lossless across ALL 60 verified golden cases."""
    golden_v1_dir = Path("eval/golden/v1")
    assert golden_v1_dir.exists(), "eval/golden/v1 directory does not exist!"

    case_files = sorted(golden_v1_dir.glob("golden_draft_*.json"))
    assert len(case_files) == 60, f"Expected 60 golden cases, found {len(case_files)}"

    for case_file in case_files:
        with open(case_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        golden_case = GoldenCase(**raw_data)
        case_spec = CaseSpec.from_golden_case(golden_case)
        restored_case = case_spec.to_golden_case()

        orig_dump = golden_case.model_dump()
        restored_dump = restored_case.model_dump()

        assert restored_dump == orig_dump, f"Lossless round-trip failed for case file {case_file.name}!"
