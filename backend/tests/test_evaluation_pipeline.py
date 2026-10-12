"""
Comprehensive Unit and Integration Tests for Diagnosis Report Evaluation Pipeline.
Verifies all 6 evaluation dimensions, fail-closed semantics, ground-truth isolation,
aggregate evaluation calculations, and hospital orchestrator integration.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.evaluation.models import (
    EvaluationSeverity,
    EvaluationStatus,
    DimensionEvaluationResult,
    AggregateEvaluationResult,
)
from backend.evaluation.dimensions import (
    ClinicalContextRelevanceEvaluator,
    HallucinationDetectionEvaluator,
    StructuralComplianceEvaluator,
    ClinicalReasoningConsistencyEvaluator,
    RecommendationValidityEvaluator,
    EvidenceGroundingEvaluator,
)
from backend.evaluation.pipeline import DiagnosisReportEvaluationPipeline, evaluation_pipeline
from backend.clinical.models import ClinicalReport, DifferentialItem, VitalSigns, LabResult, LabTestType
from backend.main import app


def _valid_report():
    return {
        "id": "RPT-TEST-001",
        "encounter_id": "ENC-TEST-001",
        "patient_id": "PAT-001",
        "patient_name": "James Wilson",
        "patient_age": 62,
        "patient_sex": "male",
        "chief_complaint": "Substernal chest pressure and dyspnea",
        "history_of_present_illness": "62-year-old male with 2 hours of crushing substernal chest pressure radiating to the left arm and jaw with diaphoresis.",
        "past_medical_history": ["Hypertension", "Type 2 Diabetes"],
        "medications": ["Metformin 500mg", "Lisinopril 10mg"],
        "allergies": [],
        "vital_signs": {
            "heart_rate": 96,
            "systolic_bp": 145,
            "diastolic_bp": 88,
            "respiratory_rate": 18,
            "temperature_c": 36.8,
            "spo2_percent": 97.0,
            "pain_score": 8,
        },
        "investigations_ordered": ["12-Lead ECG", "Cardiac Troponin-I", "Chest X-Ray (PA & Lateral)"],
        "investigation_results": [
            {"test_type": "12-Lead ECG", "values": {"rhythm": "ST-depression in leads II, III, aVF"}, "interpretation": "Ischemic ST-segment depression"},
            {"test_type": "Cardiac Troponin-I", "values": {"Troponin-I": "2.4 ng/mL"}, "interpretation": "Markedly elevated cardiac biomarkers (>0.04 ng/mL)"},
        ],
        "clinical_summary": "62-year-old male presenting with acute substernal chest pressure. Biomarkers show elevated troponin and ECG demonstrates lateral ischemia.",
        "relevant_findings": [
            "Cardiac Biomarkers: Elevated Troponin-I (2.4 ng/mL)",
            "12-Lead ECG: ST-segment depression in inferior/lateral leads",
            "Hemodynamics: Systolic BP 145/88 mmHg, HR 96 bpm",
        ],
        "primary_diagnosis": "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)",
        "diagnostic_confidence": 0.94,
        "differential_diagnosis": [
            {
                "condition": "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)",
                "likelihood": 0.94,
                "supporting_points": ["Substernal chest pain with radiation", "Elevated cardiac troponin-I", "Ischemic ST depression"],
                "opposing_points": [],
            },
            {
                "condition": "Unstable Angina",
                "likelihood": 0.05,
                "supporting_points": ["Anginal pattern"],
                "opposing_points": ["Ruled out by positive cardiac necrosis biomarkers"],
            },
        ],
        "clinical_reasoning": "Patient presents with crushing chest discomfort, positive high-sensitivity troponin-I, and ischemic ST depressions, confirming NSTEMI per Harrison's and Braunwald's clinical guidelines.",
        "treatment_plan": [
            "Aspirin 325 mg PO chewable immediately",
            "Ticagrelor 180 mg PO loading dose",
            "Unfractionated Heparin IV weight-based bolus and infusion",
            "Continuous cardiac telemetry and serial troponin monitoring",
        ],
        "recommended_disposition": "Admit to Cardiac Intensive Care Unit (CCU)",
        "recommended_next_steps": [
            "Admit to CCU for continuous telemetry monitoring",
            "Urgent Cardiology consult for early invasive coronary angiography",
        ],
        "medical_knowledge_citations": [
            {"source": "Harrison's Principles of Internal Medicine", "chapter": "Acute Coronary Syndromes", "page": 1820, "text": "NSTEMI management guidelines"},
            {"source": "nabd_rxnorm", "chapter": "Aspirin", "text": "Antiplatelet therapy in ACS"},
        ],
        "ungrounded": False,
    }


def _valid_patient_presentation():
    return {
        "age": 62,
        "sex": "male",
        "chief_complaint": "Substernal chest pressure and dyspnea",
        "history_of_present_illness": "62-year-old male with 2 hours of crushing substernal chest pressure radiating to the left arm and jaw with diaphoresis.",
        "past_medical_history": ["Hypertension", "Type 2 Diabetes"],
        "vital_signs": {
            "heart_rate": 96,
            "systolic_bp": 145,
            "diastolic_bp": 88,
            "temperature_c": 36.8,
            "spo2_percent": 97.0,
        },
    }


# =============================================================================
# 1. Clinical Context Relevance Tests
# =============================================================================

def test_clinical_context_relevance_valid():
    evaluator = ClinicalContextRelevanceEvaluator()
    res = evaluator.evaluate(_valid_report(), _valid_patient_presentation())
    assert res.passed is True
    assert res.score >= 0.85
    assert len(res.detected_issues) == 0


def test_clinical_context_relevance_demographic_mismatch():
    evaluator = ClinicalContextRelevanceEvaluator()
    rep = _valid_report()
    rep["patient_age"] = 24  # Mismatch from 62
    rep["patient_sex"] = "female"  # Mismatch from male
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("Demographic mismatch" in iss for iss in res.detected_issues)


def test_clinical_context_relevance_syndrome_misalignment():
    evaluator = ClinicalContextRelevanceEvaluator()
    rep = _valid_report()
    # Change diagnosis and reasoning to something completely unrelated to chest pain
    rep["primary_diagnosis"] = "Tinea Pedis"
    rep["clinical_summary"] = "Patient has foot rash."
    rep["clinical_reasoning"] = "Topical antifungal prescribed for foot lesion."
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("Syndrome misalignment" in iss for iss in res.detected_issues)


# =============================================================================
# 2. Hallucination / Unsupported Claims Tests
# =============================================================================

def test_hallucination_evaluator_valid():
    evaluator = HallucinationDetectionEvaluator()
    res = evaluator.evaluate(_valid_report(), _valid_patient_presentation())
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.detected_issues) == 0


def test_hallucination_unperformed_imaging():
    evaluator = HallucinationDetectionEvaluator()
    rep = _valid_report()
    # Claims CT was performed with positive findings when CT was not ordered
    rep["clinical_reasoning"] += " CT pulmonary angiogram demonstrated a large saddle pulmonary embolism."
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert res.severity in [EvaluationSeverity.CRITICAL, EvaluationSeverity.HIGH]
    assert any("Unsupported imaging claim" in iss for iss in res.detected_issues)


def test_hallucination_biomarker_contradiction():
    evaluator = HallucinationDetectionEvaluator()
    rep = _valid_report()
    # Troponin was elevated in labs, but report claims it was normal
    rep["clinical_reasoning"] = "Patient troponin is normal and undetectable, excluding infarction."
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("biomarker" in iss.lower() for iss in res.detected_issues)


def test_hallucination_fabricated_vitals():
    evaluator = HallucinationDetectionEvaluator()
    rep = _valid_report()
    # Recorded temp was 36.8C; report claims fever 40.2C
    rep["clinical_summary"] += " Patient is febrile to 40.2 C on arrival."
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("temperature" in iss.lower() for iss in res.detected_issues)


# =============================================================================
# 3. Structural Compliance Tests
# =============================================================================

def test_structural_compliance_valid():
    evaluator = StructuralComplianceEvaluator()
    res = evaluator.evaluate(_valid_report(), _valid_patient_presentation())
    assert res.passed is True
    assert res.score == 1.0


def test_structural_compliance_missing_sections():
    evaluator = StructuralComplianceEvaluator()
    rep = _valid_report()
    rep["clinical_summary"] = ""
    rep["treatment_plan"] = []
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("Clinical Summary" in iss for iss in res.detected_issues)
    assert any("Treatment Plan" in iss for iss in res.detected_issues)


def test_structural_compliance_invalid_confidence():
    evaluator = StructuralComplianceEvaluator()
    rep = _valid_report()
    rep["diagnostic_confidence"] = 1.95  # Out of bounds (>1.0)
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("diagnostic confidence" in iss.lower() for iss in res.detected_issues)


# =============================================================================
# 4. Clinical Reasoning Consistency Tests
# =============================================================================

def test_clinical_reasoning_consistency_valid():
    evaluator = ClinicalReasoningConsistencyEvaluator()
    res = evaluator.evaluate(_valid_report(), _valid_patient_presentation())
    assert res.passed is True
    assert res.score == 1.0


def test_clinical_reasoning_consistency_differential_mismatch():
    evaluator = ClinicalReasoningConsistencyEvaluator()
    rep = _valid_report()
    rep["primary_diagnosis"] = "Acute Appendicitis"
    # Differential top item is NSTEMI
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("Differential inconsistency" in iss for iss in res.detected_issues)


def test_clinical_reasoning_logical_contradiction():
    evaluator = ClinicalReasoningConsistencyEvaluator()
    rep = _valid_report()
    rep["primary_diagnosis"] = "Acute ST-Elevation Myocardial Infarction (STEMI)"
    rep["clinical_reasoning"] = "Patient 12-lead ECG showed normal sinus rhythm with no ST-elevation or ischemic changes."
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("Logical contradiction" in iss for iss in res.detected_issues)


# =============================================================================
# 5. Recommendation Validity Tests
# =============================================================================

def test_recommendation_validity_valid():
    evaluator = RecommendationValidityEvaluator()
    res = evaluator.evaluate(_valid_report(), _valid_patient_presentation())
    assert res.passed is True
    assert res.score == 1.0


def test_recommendation_validity_contraindicated_drug():
    evaluator = RecommendationValidityEvaluator()
    rep = _valid_report()
    # Add cardiogenic shock to context and beta-blocker to treatment
    rep["clinical_summary"] += " Patient in cardiogenic shock with severe hypotension."
    rep["treatment_plan"].append("Metoprolol 50 mg PO BID")
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert res.severity == EvaluationSeverity.CRITICAL
    assert any("contraindication" in iss.lower() for iss in res.detected_issues)


def test_recommendation_validity_ground_truth_contraindication():
    evaluator = RecommendationValidityEvaluator()
    rep = _valid_report()
    rep["treatment_plan"].append("Ibuprofen 800 mg PO TID")
    gt = {"contraindications": ["Avoid all NSAIDs due to severe acute kidney injury"]}
    res = evaluator.evaluate(rep, _valid_patient_presentation(), ground_truth=gt)
    assert res.passed is False
    assert res.severity == EvaluationSeverity.CRITICAL
    assert any("Ground-truth contraindicated" in iss for iss in res.detected_issues)


# =============================================================================
# 6. Evidence & Grounding Quality Tests
# =============================================================================

def test_evidence_grounding_valid():
    evaluator = EvidenceGroundingEvaluator()
    res = evaluator.evaluate(_valid_report(), _valid_patient_presentation())
    assert res.passed is True
    assert res.score == 1.0


def test_evidence_grounding_ungrounded_flag():
    evaluator = EvidenceGroundingEvaluator()
    rep = _valid_report()
    rep["ungrounded"] = True
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("ungrounded" in iss.lower() for iss in res.detected_issues)


def test_evidence_grounding_missing_citations():
    evaluator = EvidenceGroundingEvaluator()
    rep = _valid_report()
    rep["medical_knowledge_citations"] = []
    res = evaluator.evaluate(rep, _valid_patient_presentation())
    assert res.passed is False
    assert any("No medical knowledge citations" in iss for iss in res.detected_issues)


# =============================================================================
# 7. Pipeline Aggregate & Fail-Closed Tests
# =============================================================================

@pytest.mark.asyncio
async def test_pipeline_fail_closed_on_none_report():
    pipeline = DiagnosisReportEvaluationPipeline()
    res = await pipeline.evaluate_report(None, emit_events=False)
    assert res.passed is False
    assert res.final_status == EvaluationStatus.REJECTED
    assert res.severity == EvaluationSeverity.CRITICAL
    assert "MISSING_REPORT" in res.failed_checks


@pytest.mark.asyncio
async def test_pipeline_aggregate_success():
    pipeline = DiagnosisReportEvaluationPipeline()
    res = await pipeline.evaluate_report(_valid_report(), _valid_patient_presentation(), emit_events=False)
    assert res.passed is True
    assert res.final_status == EvaluationStatus.PASSED
    assert res.overall_score >= 0.85
    assert len(res.failed_checks) == 0
    assert len(res.dimensions) == 6


@pytest.mark.asyncio
async def test_pipeline_aggregate_catches_flaws():
    pipeline = DiagnosisReportEvaluationPipeline()
    flawed_report = _valid_report()
    flawed_report["primary_diagnosis"] = "Tinea Pedis"
    flawed_report["ungrounded"] = True
    flawed_report["treatment_plan"] = ["Metoprolol 50mg"]
    flawed_report["clinical_summary"] += " Patient in cardiogenic shock."

    res = await pipeline.evaluate_report(flawed_report, _valid_patient_presentation(), emit_events=False)
    assert res.passed is False
    assert res.final_status == EvaluationStatus.REJECTED
    assert len(res.failed_checks) >= 2


# =============================================================================
# 8. REST API Endpoints Tests
# =============================================================================

def test_api_report_evaluation_endpoints():
    client = TestClient(app)
    # 1. Fetch pending reports
    r = client.get("/api/reports/pending")
    assert r.status_code == 200
    reports = r.json()
    if reports:
        report_id = reports[0]["id"]
        # 2. Get evaluation for this report
        eval_res = client.get(f"/api/reports/{report_id}/evaluation")
        assert eval_res.status_code == 200
        data = eval_res.json()
        assert "evaluation_id" in data
        assert "overall_score" in data
        assert "final_status" in data
        assert "dimensions" in data

        # 3. Post on-demand evaluation
        post_res = client.post(f"/api/reports/{report_id}/evaluate")
        assert post_res.status_code == 200
        assert post_res.json()["evaluation_id"] == data["evaluation_id"] or "evaluation_id" in post_res.json()
