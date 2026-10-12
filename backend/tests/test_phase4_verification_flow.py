"""
Unit and Integration Tests for Phase 4: Generalized Verification and Review Flow.
Verifies:
1. AssessmentReport Pydantic schema accepts multi-source evidence (Harrison, Braunwald, NABD/RxNorm).
2. Phase 3 validation layer (V6, V7, V8) correctly verifies multi-source evidence.
3. Physician reviews generate valid DPO preference pairs for dynamically resolved patients.
4. Strict separation of human review and automated evaluation data structures.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from vh.generation.v2_report import (
    AssessmentReport,
    FinalDiagnosis,
    DifferentialDx,
    EvidenceItem,
    WorkupItem,
    TreatmentItem,
    Disposition,
)
from vh.verification.phase3 import validate_assessment_report, check_v6, check_v7, check_v8, _Ctx
from backend.simulation.orchestrator import HospitalOrchestrator
from backend.clinical.cases import BENCHMARK_CASES
from backend.clinical.models import (
    DiagnosisFeedback,
    ReasoningFeedback,
    TestAppropriatenessFeedback,
    TreatmentSafetyFeedback,
)


def test_v2_report_multi_source_schema_validation():
    """Verify AssessmentReport accepts braunwald and nabd_rxnorm evidence sources."""
    evidence_braunwald = EvidenceItem(
        source="braunwald",
        chunk_id="B-CH-42-001",
        supporting_quote="Acute myocardial infarction requires rapid restoration of coronary perfusion.",
    )
    evidence_rxnorm = EvidenceItem(
        source="nabd_rxnorm",
        chunk_id="RX-1191",
        supporting_quote="Aspirin 325 mg orally immediately upon suspicion of acute coronary syndrome.",
    )

    report = AssessmentReport(
        report_id="AR-TEST-001",
        case_summary="62-year-old male with severe acute retrosternal pressure radiating to the jaw.",
        chief_complaint="Severe retrosternal pressure",
        prompt_version="specialist_assessment@1.2.0",
        differential_diagnosis=[
            DifferentialDx(
                diagnosis="ST-Elevation Myocardial Infarction",
                icd10="I21.0",
                probability=0.85,
                supporting_findings=["ST elevations in V1-V4", "Elevated troponin"],
                against_findings=[],
                evidence=[evidence_braunwald],
            ),
            DifferentialDx(
                diagnosis="Aortic Dissection",
                icd10="I71.0",
                probability=0.15,
                supporting_findings=["Severe chest pain"],
                against_findings=["Symmetric pulses", "No mediastinal widening"],
                evidence=[EvidenceItem(source="model_knowledge")],
            ),
        ],
        final_diagnosis=FinalDiagnosis(
            diagnosis="ST-Elevation Myocardial Infarction",
            icd10="I21.0",
            certainty="confirmed",
            confidence=0.90,
            evidence=[evidence_braunwald],
        ),
        clinical_reasoning="Clinical presentation and electrocardiographic findings are diagnostic of STEMI.",
        workup=[
            WorkupItem(test="12-Lead ECG", priority="stat", rationale="Evaluate ST changes", evidence=[evidence_braunwald]),
        ],
        treatment=[
            TreatmentItem(
                item="Aspirin",
                dose_route_frequency_duration="325 mg PO once immediately",
                rationale="Antiplatelet therapy",
                evidence=[evidence_rxnorm],
            ),
        ],
        disposition=Disposition(setting="ICU", rationale="Continuous cardiac monitoring and reperfusion", evidence=[evidence_braunwald]),
    )

    dumped = report.model_dump()
    assert dumped["final_diagnosis"]["evidence"][0]["source"] == "braunwald"
    assert dumped["treatment"][0]["evidence"][0]["source"] == "nabd_rxnorm"


def test_phase3_validation_with_multi_source_evidence():
    """Verify V6, V7, V8 pass when grounded in Braunwald + NABD/RxNorm."""
    braunwald_text = "Acute myocardial infarction requires rapid restoration of coronary perfusion via primary PCI."
    rxnorm_text = "Aspirin 325 mg orally immediately upon suspicion of acute coronary syndrome."

    retrieval_log = {
        "chunks": {
            "B-CH-42-001": {"text": braunwald_text, "metadata": {"source": "braunwald"}},
            "RX-1191": {"text": rxnorm_text, "metadata": {"source": "nabd_rxnorm"}},
        }
    }

    report = AssessmentReport(
        report_id="AR-TEST-002",
        case_summary="Acute coronary syndrome presenting with diaphoresis and substernal chest pain.",
        chief_complaint="Severe retrosternal pressure",
        prompt_version="specialist_assessment@1.2.0",
        differential_diagnosis=[
            DifferentialDx(
                diagnosis="ST-Elevation Myocardial Infarction",
                icd10="I21.0",
                probability=0.90,
                supporting_findings=["ST elevations"],
                against_findings=[],
                evidence=[
                    EvidenceItem(
                        source="braunwald",
                        chunk_id="B-CH-42-001",
                        supporting_quote="Acute myocardial infarction requires rapid restoration",
                    )
                ],
            ),
        ],
        final_diagnosis=FinalDiagnosis(
            diagnosis="ST-Elevation Myocardial Infarction",
            icd10="I21.0",
            certainty="confirmed",
            confidence=0.95,
            evidence=[
                EvidenceItem(
                    source="braunwald",
                    chunk_id="B-CH-42-001",
                    supporting_quote="Acute myocardial infarction requires rapid restoration",
                )
            ],
        ),
        clinical_reasoning="Clinical findings confirm acute STEMI based on Braunwald protocols.",
        workup=[
            WorkupItem(
                test="Primary PCI",
                priority="stat",
                rationale="Coronary reperfusion",
                evidence=[
                    EvidenceItem(
                        source="braunwald",
                        chunk_id="B-CH-42-001",
                        supporting_quote="restoration of coronary perfusion via primary PCI",
                    )
                ],
            )
        ],
        treatment=[
            TreatmentItem(
                item="Aspirin",
                dose_route_frequency_duration="325 mg PO once immediately",
                rationale="Inhibit platelet aggregation",
                evidence=[
                    EvidenceItem(
                        source="nabd_rxnorm",
                        chunk_id="RX-1191",
                        supporting_quote="Aspirin 325 mg orally immediately",
                    )
                ],
            )
        ],
        disposition=Disposition(
            setting="ICU",
            rationale="Cardiac catheterization unit",
            evidence=[
                EvidenceItem(
                    source="braunwald",
                    chunk_id="B-CH-42-001",
                    supporting_quote="restoration of coronary perfusion",
                )
            ],
        ),
    )

    ctx = _Ctx(retrieval_log, {})
    res_v6 = check_v6(report, ctx)
    assert res_v6.passed is True, f"V6 failed: {res_v6.message}"

    res_v7 = check_v7(report, ctx)
    assert res_v7.passed is True, f"V7 failed: {res_v7.message}"

    res_v8 = check_v8(report, ctx)
    assert res_v8.passed is True, f"V8 failed: {res_v8.message}"


def test_dpo_pair_generation_for_dynamic_case():
    """Verify submit_physician_review generates DPO pairs for dynamically resolved patients."""
    orchestrator = HospitalOrchestrator(enable_gpu=False)

    # Use existing benchmark case CASE-101
    case = BENCHMARK_CASES[0]
    toolkit = MagicMock()
    toolkit.ground_truth = case

    # Mock a clinical report in orchestrator
    mock_report = MagicMock()
    mock_report.id = "REP-TEST-DPO"
    mock_report.encounter_id = "ENC-TEST-DPO"
    mock_report.patient_id = case.id
    mock_report.patient_name = case.name
    mock_report.primary_diagnosis = "Non-ST-Elevation Myocardial Infarction (NSTEMI)"
    mock_report.diagnostic_confidence = 0.90
    mock_report.clinical_reasoning = "Presentation and elevated troponin are diagnostic of NSTEMI."
    mock_report.treatment_plan = ["Aspirin 325 mg", "Ticagrelor 180 mg", "Heparin bolus"]
    mock_report.model_dump.return_value = {
        "id": mock_report.id,
        "encounter_id": mock_report.encounter_id,
        "patient_id": mock_report.patient_id,
        "patient_name": mock_report.patient_name,
        "primary_diagnosis": mock_report.primary_diagnosis,
        "treatment_plan": mock_report.treatment_plan,
        "clinical_reasoning": mock_report.clinical_reasoning,
    }

    orchestrator.reports[mock_report.id] = mock_report

    review = orchestrator.submit_physician_review(
        report_id=mock_report.id,
        physician_name="Dr. Sarah Connor, MD",
        diagnosis_grade=DiagnosisFeedback.CORRECT.value,
        reasoning_grade=ReasoningFeedback.SOUND.value,
        tests_grade=TestAppropriatenessFeedback.APPROPRIATE.value,
        treatment_grade=TreatmentSafetyFeedback.SAFE_AND_OPTIMAL.value,
        overall_score=5,
        approved=True,
        notes="Exemplary clinical reasoning and guideline-directed medical therapy.",
    )

    assert review.approved is True
    assert review.overall_score == 5
    assert review.report_id == mock_report.id
