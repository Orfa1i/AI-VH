"""
Tests for the 11-step SpecialtyClinicalReasoningEngine used by every Specialty Agent.

Verifies:
- Both specialists (Internal Medicine, Cardiology) delegate encounters to the shared engine.
- Steps run in order (event sequence) and MedGemma performs the diagnostic synthesis.
- Ground truth isolation: diagnostic ground-truth fields are never read.
- Patient data primacy: objective findings are passed to the model and appear in the report.
- Report carries all required sections, source attribution, and no verbatim-copied passages.

All tests are mocked (no GPU / no live model call).
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.agents.specialists.cardiology import CardiologySpecialistAgent
from backend.agents.specialists.internal_medicine import InternalMedicineSpecialistAgent
from backend.agents.specialists.reasoning_engine import SpecialtyClinicalReasoningEngine
from backend.clinical.models import LabTestType, VitalSigns
from backend.simulation.events import EventType

SOURCE_PASSAGE = (
    "Acute coronary syndromes result from rupture of an atherosclerotic plaque with superimposed "
    "thrombus formation that reduces coronary blood flow and produces myocardial ischemia and necrosis"
)


class GuardedGroundTruth:
    """Exposes only the patient identifier; reading any diagnostic field fails the test."""

    FORBIDDEN = {"true_diagnosis", "icd10_code", "recommended_labs", "expected_treatment", "diagnosis"}

    def __init__(self, patient_id: str):
        self.id = patient_id
        self.accessed = []

    def __getattr__(self, name):
        if name in GuardedGroundTruth.FORBIDDEN:
            raise AssertionError(f"Ground truth leak: '{name}' was read by the generation path")
        raise AttributeError(name)


def _vitals():
    return VitalSigns(
        heart_rate=108, systolic_bp=150, diastolic_bp=92, respiratory_rate=20,
        temperature_c=36.9, spo2_percent=96.0, pain_score=8,
    )


def _toolkit():
    tk = MagicMock()
    tk.ground_truth = GuardedGroundTruth("PAT-001")
    tk.get_patient_history.return_value = {
        "name": "Test Patient", "age": 61, "sex": "male",
        "chief_complaint": "Substernal chest pressure",
        "history_of_present_illness": "Two hours of crushing chest pain radiating to the left arm with diaphoresis.",
        "past_medical_history": ["Hypertension", "Type 2 diabetes"],
        "medications": ["Metformin", "Lisinopril"],
        "allergies": [],
    }
    tk.get_vital_signs.return_value = _vitals()
    tk.perform_physical_exam.return_value = {"General": "Diaphoretic, in distress", "Cardiovascular": "Normal S1/S2"}

    def order(test):
        interp = "Elevated at 2.4 ng/mL" if test == LabTestType.TROPONIN_I else "Within normal limits"
        return SimpleNamespace(model_dump=lambda: {"test_type": test.value, "values": {}, "interpretation": interp})

    tk.order_lab_test.side_effect = order
    tk.write_clinical_report.side_effect = lambda **kw: SimpleNamespace(
        id="RPT-1", primary_diagnosis=kw["primary_diagnosis"], kwargs=kw
    )
    return tk


def _rag():
    rag = MagicMock()
    rag.generate_evidence_brief.return_value = SimpleNamespace(
        domain="Cardiovascular",
        citations=[{"source": "Braunwald's Heart Disease", "chapter": "Acute Coronary Syndromes", "page": "1150",
                    "text": SOURCE_PASSAGE}],
        recommended_therapy=["Aspirin"],
    )
    return rag


def _llm(reasoning=None):
    llm = MagicMock()
    llm.generate_clinical_decision.return_value = {
        "primary_diagnosis": "NSTEMI",
        "confidence": 0.9,
        "differential": [
            {"condition": "NSTEMI", "likelihood": 0.9, "supporting_points": ["Elevated troponin"], "opposing_points": []},
            {"condition": "Unstable angina", "likelihood": 0.08, "supporting_points": [], "opposing_points": ["Troponin elevated"]},
        ],
        "clinical_reasoning": reasoning or "Ischemic chest pain with a rising troponin in a diabetic hypertensive man indicates myocardial infarction.",
        "treatment_plan": ["Aspirin 325 mg", "Heparin infusion"],
        "recommended_disposition": "Admit to CCU",
    }
    return llm


def _shared():
    shared = MagicMock()
    shared.retrieve_shared_evidence.return_value = [
        {"source": "nabd_rxnorm", "chapter": "Metformin", "text": "Biguanide antihyperglycemic."}
    ]
    return shared


def _run(agent_cls, llm=None):
    llm = llm or _llm()
    agent = agent_cls(rag_agent=_rag(), medgemma_service=llm)
    agent.reasoning_engine.shared_sources = _shared()
    events = []

    async def capture(**kw):
        events.append(kw["event_type"])

    agent.reasoning_engine._emit_event_fn = capture
    tk = _toolkit()
    report = asyncio.run(agent.conduct_clinical_encounter("ENC-000001", tk))
    return report, events, llm, tk


@pytest.mark.parametrize("agent_cls", [InternalMedicineSpecialistAgent, CardiologySpecialistAgent])
def test_specialists_delegate_to_shared_engine(agent_cls):
    agent = agent_cls(rag_agent=MagicMock(), medgemma_service=MagicMock())
    assert isinstance(agent.reasoning_engine, SpecialtyClinicalReasoningEngine)
    assert agent.reasoning_engine.llm is agent.llm  # same MedGemma base model


@pytest.mark.parametrize("agent_cls", [InternalMedicineSpecialistAgent, CardiologySpecialistAgent])
def test_workflow_step_order_and_model_synthesis(agent_cls):
    report, events, llm, _ = _run(agent_cls)
    order = [
        EventType.DOCTOR_ASSIGNED, EventType.EXAMINATION_STARTED, EventType.DIFFERENTIAL_UPDATED,
        EventType.RAG_QUERY_INITIATED, EventType.RAG_KNOWLEDGE_RETRIEVED, EventType.DIFFERENTIAL_UPDATED,
        EventType.DIAGNOSIS_MADE, EventType.TREATMENT_ORDERED, EventType.CLINICAL_REPORT_GENERATED,
    ]
    assert events == order
    llm.generate_clinical_decision.assert_called_once()
    assert report.primary_diagnosis == "NSTEMI"  # diagnosis comes from the model


@pytest.mark.parametrize("agent_cls", [InternalMedicineSpecialistAgent, CardiologySpecialistAgent])
def test_ground_truth_never_read(agent_cls):
    _run(agent_cls)  # GuardedGroundTruth raises on any forbidden access


def test_model_receives_patient_data_and_both_evidence_sources():
    _, _, llm, _ = _run(InternalMedicineSpecialistAgent)
    kw = llm.generate_clinical_decision.call_args.kwargs
    assert kw["chief_complaint"] == "Substernal chest pressure"
    assert any("Elevated" in str(r.get("interpretation")) for r in kw["lab_results"])
    sources = {c["source"] for c in kw["rag_context"]}
    assert sources == {"Braunwald's Heart Disease", "nabd_rxnorm"}
    # Nothing from ground truth or evaluator metadata reaches the prompt inputs
    assert "true_diagnosis" not in str(kw) and "score" not in str(kw).lower()


def test_report_has_all_sections_and_attribution():
    report, _, _, _ = _run(CardiologySpecialistAgent)
    kw = report.kwargs
    assert "61-year-old male" in kw["clinical_summary"]
    assert kw["primary_diagnosis"] == "NSTEMI"
    assert len(kw["differential"]) == 2
    assert kw["differential"][0].supporting_points == ["Elevated troponin"]
    assert any("Troponin" in f and "Elevated" in f for f in kw["relevant_findings"])
    assert kw["recommended_next_steps"] and "CCU" in kw["recommended_next_steps"][0]
    assert kw["treatment_plan"] == ["Aspirin 325 mg", "Heparin infusion"]
    assert kw["recommended_disposition"] == "Admit to CCU"
    assert len(kw["citations"]) == 2 and kw["ungrounded"] is False
    assert "[1] Braunwald's Heart Disease, Acute Coronary Syndromes, p.1150" in kw["clinical_reasoning"]


def test_verbatim_source_text_is_removed_from_report():
    copied = "Plaque rupture explains this. " + SOURCE_PASSAGE + ". The patient needs urgent angiography."
    report, _, _, _ = _run(InternalMedicineSpecialistAgent, llm=_llm(reasoning=copied))
    reasoning = report.kwargs["clinical_reasoning"]
    assert "superimposed thrombus formation that reduces coronary blood flow" not in reasoning
    assert "urgent angiography" in reasoning


def test_empty_model_output_raises_instead_of_fabricating():
    llm = MagicMock()
    llm.generate_clinical_decision.return_value = {}
    with pytest.raises(RuntimeError, match="no primary diagnosis"):
        _run(InternalMedicineSpecialistAgent, llm=llm)


def test_no_citations_marks_report_ungrounded():
    agent = InternalMedicineSpecialistAgent(rag_agent=_rag(), medgemma_service=_llm())
    agent.reasoning_engine.rag_agent.generate_evidence_brief.return_value.citations = []
    shared = MagicMock()
    shared.retrieve_shared_evidence.return_value = []
    agent.reasoning_engine.shared_sources = shared

    async def noop(**kw):
        return None

    agent.reasoning_engine._emit_event_fn = noop
    report = asyncio.run(agent.conduct_clinical_encounter("ENC-000002", _toolkit()))
    assert report.kwargs["ungrounded"] is True
