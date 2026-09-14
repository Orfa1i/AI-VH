"""
Unit & Integration Tests for Phase 6: Reinforcement Learning & DPO Preference Dataset Generator
Verifies clinical reward modeling, DPO pair generation, JSONL serialization, and orchestrator integration.
"""

import pytest
import os
import json
from datetime import datetime

from backend.clinical.models import (
    ClinicalReport,
    PhysicianReview,
    DiagnosisFeedback,
    ReasoningFeedback,
    TestAppropriatenessFeedback,
    TreatmentSafetyFeedback,
)
from backend.clinical.cases import BENCHMARK_CASES
from backend.rl.reward_model import ClinicalRewardModel, ClinicalRewardBreakdown
from backend.rl.dpo_generator import DPOPreferenceGenerator, DPOPreferencePair
from backend.simulation.orchestrator import HospitalOrchestrator


def test_clinical_reward_model_exemplary_case():
    """High-performing, guideline-adherent decision should yield a high positive reward."""
    review = PhysicianReview(
        id="REV-TEST-01",
        report_id="REP-TEST-01",
        encounter_id="ENC-TEST-01",
        physician_name="Dr. Attending, MD",
        reviewed_at=datetime.utcnow(),
        diagnosis_grade=DiagnosisFeedback.CORRECT,
        reasoning_grade=ReasoningFeedback.SOUND,
        tests_grade=TestAppropriatenessFeedback.APPROPRIATE,
        treatment_grade=TreatmentSafetyFeedback.SAFE_AND_OPTIMAL,
        overall_score=5,
        approved=True,
        physician_feedback_notes="Flawless adherence to clinical guidelines.",
    )

    breakdown = ClinicalRewardModel.compute_reward(review=review, has_harrison_citations=True)
    assert breakdown.is_safe is True
    assert breakdown.total_reward > 0.8
    assert breakdown.total_reward <= 1.0
    assert breakdown.safety_penalty == 0.0


def test_clinical_reward_model_unsafe_penalty():
    """Unsafe or contraindicated treatment must trigger severe safety penalties."""
    review = PhysicianReview(
        id="REV-TEST-02",
        report_id="REP-TEST-02",
        encounter_id="ENC-TEST-02",
        physician_name="Dr. Attending, MD",
        reviewed_at=datetime.utcnow(),
        diagnosis_grade=DiagnosisFeedback.INCORRECT,
        reasoning_grade=ReasoningFeedback.UNSUPPORTED_CONCLUSION,
        tests_grade=TestAppropriatenessFeedback.INAPPROPRIATE_TEST,
        treatment_grade=TreatmentSafetyFeedback.CONTRAINDICATED_OR_HARMFUL,
        overall_score=1,
        approved=False,
        physician_feedback_notes="Dangerous order: missed acute coronary syndrome.",
    )

    breakdown = ClinicalRewardModel.compute_reward(review=review, has_harrison_citations=False)
    assert breakdown.is_safe is False
    assert breakdown.total_reward < -0.5
    assert breakdown.safety_penalty < 0.0


def test_dpo_benchmark_calibrations():
    """Calibrated benchmark pairs must be valid, well-formed, and exhibit positive reward margins."""
    pairs = DPOPreferenceGenerator.generate_benchmark_calibrations()
    assert len(pairs) >= 3

    for pair in pairs:
        assert len(pair.prompt) > 20
        assert len(pair.chosen) > 30
        assert len(pair.rejected) > 30
        assert pair.reward_margin > 0.0
        assert pair.reward_chosen > pair.reward_rejected
        assert len(pair.harrison_citations) > 0
        assert pair.source == "CALIBRATED_BENCHMARK"


def test_dpo_pair_from_rejected_review():
    """When a review contains corrections, the physician's corrections must become 'chosen' and the flawed AI 'rejected'."""
    case = BENCHMARK_CASES[0]
    report = ClinicalReport(
        id="REP-TEST-REJECT",
        encounter_id="ENC-TEST-REJECT",
        patient_id=case.id,
        patient_name=case.name,
        patient_age=case.age,
        patient_sex=case.sex,
        chief_complaint=case.chief_complaint,
        history_of_present_illness=case.history_of_present_illness,
        past_medical_history=case.past_medical_history,
        medications=case.medications,
        allergies=case.allergies,
        vital_signs=case.baseline_vitals,
        physical_exam_findings=case.physical_exam,
        investigations_ordered=[],
        investigation_results=[],
        differential_diagnosis=[],
        primary_diagnosis="Musculoskeletal Chest Wall Pain",
        diagnostic_confidence=0.65,
        clinical_reasoning="Atypical pain, no acute risk factors.",
        treatment_plan=["Ibuprofen 400 mg PRN"],
        recommended_disposition="Discharge home with outpatient follow-up",
        medical_knowledge_citations=[],
    )

    review = PhysicianReview(
        id="REV-TEST-REJECT",
        report_id="REP-TEST-REJECT",
        encounter_id="ENC-TEST-REJECT",
        physician_name="Dr. Attending, MD",
        reviewed_at=datetime.utcnow(),
        diagnosis_grade=DiagnosisFeedback.INCORRECT,
        reasoning_grade=ReasoningFeedback.FAULTY_LOGIC,
        tests_grade=TestAppropriatenessFeedback.MISSING_ESSENTIAL_TEST,
        treatment_grade=TreatmentSafetyFeedback.CONTRAINDICATED_OR_HARMFUL,
        overall_score=1,
        approved=False,
        corrected_diagnosis="Acute NSTEMI / High-Risk Coronary Syndrome",
        corrected_treatment=["Immediate Aspirin + Ticagrelor", "Heparin anticoagulation", "Cath lab activation"],
        physician_feedback_notes="Critical error: missed troponin elevation and dynamic ST changes.",
    )

    pair = DPOPreferenceGenerator.generate_pair_from_review(report=report, review=review)

    assert "Acute NSTEMI" in pair.chosen
    assert "Musculoskeletal Chest Wall Pain" in pair.rejected
    assert pair.reward_chosen > pair.reward_rejected
    assert pair.is_safety_critical is True
    assert pair.source == "HUMAN_PHYSICIAN"


def test_dpo_export_jsonl(tmp_path):
    """Verifies that the DPO corpus exports correctly to valid JSONL for HuggingFace DPOTrainer."""
    pairs = DPOPreferenceGenerator.generate_benchmark_calibrations()
    export_file = tmp_path / "test_dpo_export.jsonl"

    count = DPOPreferenceGenerator.export_jsonl(pairs, str(export_file))
    assert count == len(pairs)
    assert os.path.exists(export_file)

    # Read back and validate JSON parsing
    with open(export_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == len(pairs)
        first_record = json.loads(lines[0])
        assert "prompt" in first_record
        assert "chosen" in first_record
        assert "rejected" in first_record
        assert "reward_margin" in first_record


def test_orchestrator_dpo_integration(tmp_path):
    """Verifies orchestrator DPO compilation and file export."""
    orch = HospitalOrchestrator(enable_gpu=False)
    data = orch.get_dpo_dataset(include_calibrations=True)

    assert "statistics" in data
    assert "pairs" in data
    assert data["statistics"]["total_pairs"] >= 3

    export_path = str(tmp_path / "orch_dpo.jsonl")
    export_result = orch.export_dpo_dataset(output_path=export_path)
    assert export_result["exported_count"] >= 3
    assert os.path.exists(export_path)
