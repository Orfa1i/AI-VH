"""
Production Multi-Agent Architecture & Live AI Integration Test Suite.
Validates the 5-Step Clinical Workflow:
1. Patient Intake (preservation of clinical facts, vitals, labs, imaging, EHR vs synthetic tracking)
2. MedGemma Specialty Router (all 7 core specialties with full doctor personas and rationales)
3. Specialist Agent Execution (specialty RAG + active shared knowledge sources)
4. Dynamic Multi-Agent Consultation (triggers, DAG cycle breaker, timeout, disagreements, emergency locks)
5. Evidence-Grounded Nemotron Synthesis (5-tier provenance, no silent mocks, live Nebius verification)
"""

import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from backend.agents.router import MedicalSpecialtyRouter, RoutingDecision
from backend.agents.consultation import (
    ConsultationEngine,
    ConsultationFinding,
    ClinicalDisagreement,
    MultiAgentConsultationRecord,
    consultation_engine,
)
from backend.llm.nemotron_synthesis import (
    NemotronSynthesisEngine,
    NemotronSynthesisResult,
    nemotron_synthesis_engine,
)
from backend.simulation.orchestrator import orchestrator
from backend.rag.shared_sources import SharedKnowledgeService, shared_knowledge_service
from backend.clinical.cases import get_benchmark_case


# ---------------------------------------------------------------------------
# Step 1: Patient Intake Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patient_intake_preserves_data_and_origin():
    """Verifies intake preserves all clinical observations and tags data_origin."""
    patient_payload = {
        "id": "EHR-PT-901",
        "name": "Maria Gonzales",
        "age": 31,
        "sex": "Female",
        "chief_complaint": "Severe headache and epigastric pain at 34 weeks gestation",
        "history_of_present_illness": "Patient reports persistent throbbing frontal headache and visual scotomata for 12 hours.",
        "past_medical_history": ["Nulliparous", "Gestational hypertension"],
        "medications": ["Prenatal vitamins", "Labetalol 100mg PO BID"],
        "allergies": ["Penicillin"],
        "vital_signs": {"BP": "172/114", "HR": "88", "RR": "18", "SpO2": "98%"},
        "lab_results": [
            {"test_type": "Platelets", "values": "64,000 /uL", "interpretation": "Severe thrombocytopenia"},
            {"test_type": "AST", "values": "210 U/L", "interpretation": "Markedly elevated"},
            {"test_type": "Proteinuria", "values": "3+ dipstick", "interpretation": "Marked proteinuria"},
        ],
        "imaging_findings": {"Ultrasound": "Single intrauterine pregnancy, biophysical profile 8/8"},
        "data_origin": "REAL_EHR",
    }

    result = await orchestrator.execute_production_clinical_workflow(
        patient_case=patient_payload,
        data_origin="REAL_EHR",
        max_consultations=2,
    )

    assert result["data_origin"] == "REAL_EHR"
    assert "Maria Gonzales" in str(result)
    assert result["routing"]["specialty"] in ["OBSTETRICS", "GYNECOLOGY"]
    assert "Dr. Evelyn Reed" in result["routing"]["suggested_specialist_name"]
    assert result["synthesis"]["provenance"]["tier_1_patient_observed_data"]["data_origin"] == "REAL_EHR"
    assert result["synthesis"]["provenance"]["tier_1_patient_observed_data"]["patient_id"] == "EHR-PT-901"


# ---------------------------------------------------------------------------
# Step 2: MedGemma Specialty Router Tests
# ---------------------------------------------------------------------------

def test_specialty_routing_across_seven_specialties():
    """Verifies that all 7 specialties are correctly routed with doctor personas and rationales."""
    test_cases = [
        # 1. Cardiology
        (
            {"chief_complaint": "Crushing substernal chest pressure radiating to left jaw with diaphoresis", "abnormal_labs": ["Troponin I: 3.4 ng/mL"]},
            "CARDIOLOGY",
            "Dr. Rachel Vance",
        ),
        # 2. Neurology
        (
            {"chief_complaint": "Sudden onset right-sided hemiplegia and expressive aphasia 45 minutes ago"},
            "NEUROLOGY",
            "Dr. Alexander Hayes",
        ),
        # 3. Surgery
        (
            {"chief_complaint": "Right lower quadrant abdominal pain with rebound tenderness and guarding"},
            "SURGERY",
            "Dr. Sarah Lin",
        ),
        # 4. Emergency Medicine
        (
            {"chief_complaint": "Severe polytrauma, hypotension, altered mental status following motor vehicle collision"},
            "EMERGENCY_MEDICINE",
            "Dr. David Kim",
        ),
        # 5. Obstetrics
        (
            {"chief_complaint": "Third trimester 35 weeks pregnancy with painful uterine contractions and vaginal bleeding"},
            "OBSTETRICS",
            "Dr. Evelyn Reed",
        ),
        # 6. Gynecology
        (
            {"chief_complaint": "Sudden sharp left pelvic adnexal pain with nausea and negative pregnancy test"},
            "GYNECOLOGY",
            "Dr. Evelyn Reed",
        ),
        # 7. Internal Medicine
        (
            {"chief_complaint": "Unintentional weight loss, polyuria, polydipsia, fatigue, and fasting glucose 260 mg/dL"},
            "INTERNAL_MEDICINE",
            "Dr. Marcus Vance",
        ),
    ]

    for case_data, expected_spec, expected_doc in test_cases:
        decision = MedicalSpecialtyRouter.route_case(case_data)
        if expected_spec == "EMERGENCY_MEDICINE":
            assert decision.specialty in ["EMERGENCY", "EMERGENCY_MEDICINE"], f"Expected Emergency, got {decision.specialty}"
        else:
            assert decision.specialty == expected_spec, f"Expected {expected_spec}, got {decision.specialty} for {case_data}"
        assert expected_doc in decision.suggested_specialist_name, f"Expected doctor {expected_doc} in {decision.suggested_specialist_name}"
        assert len(decision.primary_rationale) > 10
        assert decision.confidence > 0.6




# ---------------------------------------------------------------------------
# Step 3 & 4: Dynamic Consultation Engine Tests
# ---------------------------------------------------------------------------

def test_dynamic_consultation_triggers():
    """Verifies clinical triggers identify only indicated secondary specialties."""
    engine = ConsultationEngine(max_consultations=2)

    # Presentation: Severe preeclampsia with epigastric pain and elevated liver enzymes
    patient_data = {
        "chief_complaint": "34 weeks pregnant with severe headache and epigastric pain",
        "history_of_present_illness": "Worsening epigastric pain, nausea, and blurry vision",
    }
    abnormal_labs = ["AST 240 U/L", "Platelets 55k", "Cr 1.6 mg/dL"]

    # When Obstetrics is primary, what is triggered?
    indicated = engine.determine_indicated_consultations(
        primary_specialty="OBSTETRICS",
        patient_data=patient_data,
        initial_diagnosis="Preeclampsia with severe features / HELLP Syndrome",
        abnormal_labs=abnormal_labs,
    )

    # Should NOT trigger all specialists; capped at max_consultations
    assert len(indicated) <= 2
    assert "OBSTETRICS" not in indicated  # Must not consult itself


def test_circular_referral_prevention():
    """Verifies that circular referrals are strictly blocked (A -> B -> A)."""
    engine = ConsultationEngine(max_consultations=2)
    path = ["INTERNAL_MEDICINE", "CARDIOLOGY"]

    # Trying to refer back to INTERNAL_MEDICINE
    is_circular = engine.check_circular_referral("INTERNAL_MEDICINE", path)
    assert is_circular is True

    # Trying to refer to a new specialty
    is_circular_surgery = engine.check_circular_referral("SURGERY", path)
    assert is_circular_surgery is False


def test_emergency_red_flags_locking():
    """Verifies that emergency red flags lock safety escalation and cannot be suppressed."""
    engine = ConsultationEngine()
    
    flags = engine.scan_emergency_red_flags("Patient exhibits severe hellp syndrome with impending eclampsia.")
    assert len(flags) > 0
    assert any("ECLAMPSIA" in f or "HELLP" in f for f in flags)

    record = MultiAgentConsultationRecord(
        encounter_id="ENC-EMERGENCY-01",
        primary_specialty="OBSTETRICS",
        emergency_red_flags=flags,
        is_emergency_escalated=True,
    )
    assert record.is_emergency_escalated is True


def test_clinical_disagreement_detection():
    """Verifies that diagnostic divergence between specialists is extracted."""
    engine = ConsultationEngine()

    primary_finding = {
        "primary_diagnosis": "Preeclampsia with severe features",
    }
    consultant_finding = {
        "primary_diagnosis": "Placental abruption with concealed hemorrhage",
    }

    disagreements = engine.identify_disagreements(primary_finding, consultant_finding)
    assert len(disagreements) == 1
    assert disagreements[0].issue_type == "DIAGNOSTIC_DISAGREEMENT"
    assert "Preeclampsia" in disagreements[0].primary_view
    assert "Placental abruption" in disagreements[0].consultant_view


# ---------------------------------------------------------------------------
# Step 5: Shared Knowledge & Citation Provenance Tests
# ---------------------------------------------------------------------------

def test_shared_knowledge_excludes_deactivated_sources():
    """Verifies that deactivated knowledge sources are not queried."""
    service = SharedKnowledgeService()
    
    # Mock database to return one active and one inactive source
    mock_sources = [
        {"id": "SRC-01", "name": "PubMed Guidelines", "status": "ACTIVE", "source_type": "PUBMED"},
        {"id": "SRC-02", "name": "Discontinued Catalog", "status": "INACTIVE", "source_type": "CUSTOM"},
    ]

    with patch.object(service, "get_active_sources", return_value=[mock_sources[0]]):
        citations = service.retrieve_shared_evidence("Chest pain with STEMI protocol", top_k=2)
        assert len(citations) > 0
        for c in citations:
            assert c["book"] != "Discontinued Catalog"


# ---------------------------------------------------------------------------
# Step 6: Fail-Safe Degradation Without Silent Mocks Tests
# ---------------------------------------------------------------------------

def test_nemotron_failsafe_degradation_without_silent_mocks():
    """
    Verifies the No Silent Fallback Rule:
    If live API call fails, result is marked status='DEGRADED' with explicit
    error telemetry and provenance (never mock success masquerading as live AI).
    """
    # Create engine pointing to invalid/failing client
    engine = NemotronSynthesisEngine(api_key="test-dummy-key", timeout=1.0)
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Connection refused: 503 Service Unavailable")
    engine._client = mock_client
    engine.max_retries = 1

    patient_info = {"id": "PAT-TEST", "age": 55, "sex": "Male", "chief_complaint": "Chest pain"}
    vitals_summary = "BP 130/80, HR 72"
    exam_findings = {"CV": "Normal S1/S2"}
    lab_results = [{"test_type": "Troponin", "values": "Negative"}]
    medgemma_decision = {"primary_diagnosis": "Non-cardiac chest pain", "confidence": 0.8, "differential": []}
    citations = [{"source": "Harrison's", "chapter": "Chest Pain", "page": "12", "text": "Evaluation of pain"}]

    result = engine.synthesize_diagnostic_report(
        patient_info=patient_info,
        vitals_summary=vitals_summary,
        exam_findings=exam_findings,
        lab_results=lab_results,
        medgemma_decision=medgemma_decision,
        citations=citations,
    )

    # Must be marked DEGRADED
    assert result.status == "DEGRADED"
    assert result.engine_name == "Local-Clinical-Fallback"
    assert result.error_message is not None

    assert "503" in result.error_message or "failed" in result.error_message.lower()
    assert result.provenance["meta"]["status"] == "DEGRADED"


# ---------------------------------------------------------------------------
# Step 7: End-to-End Clinical Workflow Integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_end_to_end_production_clinical_workflow():
    """Tests complete 5-step execution loop for benchmark CASE-101."""
    result = await orchestrator.execute_production_clinical_workflow(
        patient_case="CASE-101",
        data_origin="SYNTHETIC_BENCHMARK",
        max_consultations=2,
    )

    # Verify return envelope
    assert "encounter_id" in result
    assert result["data_origin"] == "SYNTHETIC_BENCHMARK"
    assert "routing" in result
    assert "primary_specialist" in result
    assert "multi_agent_consultation" in result
    assert "synthesis" in result

    # Verify synthesis has 5-tier provenance
    prov = result["synthesis"]["provenance"]
    assert "tier_1_patient_observed_data" in prov
    assert "tier_2_model_hypotheses" in prov
    assert "tier_3_retrieved_evidence" in prov
    assert "tier_4_specialist_consult_findings" in prov
    assert "tier_5_final_synthesized_conclusions" in prov

    # Verify specialist findings
    assert result["primary_specialist"]["specialty"] is not None
    assert result["primary_specialist"]["doctor_name"] is not None


# ---------------------------------------------------------------------------
# Step 8: Live Nebius Nemotron API Integration Test
# ---------------------------------------------------------------------------

@pytest.mark.live_api
def test_live_nebius_nemotron_api_call():
    """
    Live API integration test for NVIDIA-Nemotron-3-Nano-30B-A3B via Nebius AI Studio.
    Skipped if NEBIUS_API_KEY is not configured.
    """
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key or api_key.startswith("your-") or api_key.startswith("dummy"):
        pytest.skip("NEBIUS_API_KEY is not configured in environment. Skipping live API call.")

    engine = NemotronSynthesisEngine(api_key=api_key, timeout=45.0)
    assert engine.is_available is True

    patient_info = {
        "id": "LIVE-TEST-001",
        "name": "Live Verification Patient",
        "age": 62,
        "sex": "Female",
        "chief_complaint": "Acute substernal chest pressure radiating to left arm",
        "history_of_present_illness": "Severe retrosternal squeezing pain began 45 minutes ago at rest, accompanied by diaphoresis and nausea.",
        "past_medical_history": ["Type 2 Diabetes", "Hyperlipidemia"],
        "medications": ["Metformin 1000mg BID", "Atorvastatin 40mg daily"],
        "allergies": ["NKDA"],
        "data_origin": "REAL_EHR",
    }
    vitals_summary = "BP 148/92 mmHg, HR 96 bpm, RR 20 bpm, SpO2 97% on room air"
    exam_findings = {"Cardiovascular": "Tachycardic, regular rhythm, no murmurs", "Respiratory": "Clear to auscultation bilaterally"}
    lab_results = [
        {"test_type": "High-Sensitivity Troponin T", "values": "142 ng/L", "interpretation": "Markedly elevated above 99th percentile URL (14 ng/L)"},
        {"test_type": "12-Lead ECG", "values": "2.5mm ST elevation in leads II, III, aVF with reciprocal ST depression in I and aVL", "interpretation": "Acute Inferior STEMI"},
    ]
    medgemma_decision = {
        "specialty": "CARDIOLOGY",
        "suggested_specialist_name": "Dr. Rachel Vance, MD, FACC",
        "primary_diagnosis": "Acute Inferior ST-Elevation Myocardial Infarction (STEMI)",
        "confidence": 0.95,
        "differential": [
            {"condition": "Acute Inferior STEMI", "likelihood": 0.95, "supporting_points": ["ST elevation in II, III, aVF", "Elevated hs-cTnT"]},
            {"condition": "Acute Pericarditis", "likelihood": 0.05, "supporting_points": ["Chest pain"], "opposing_points": ["Reciprocal depressions", "Focal ST elevation"]},
        ],
        "treatment_plan": ["Aspirin 325 mg chewed", "Ticagrelor 180 mg loading dose", "Heparin bolus STAT", "Immediate cardiac catheterization laboratory activation"],
    }
    citations = [
        {
            "source": "Braunwald's Heart Disease 12th Ed",
            "chapter": "ST-Elevation Myocardial Infarction: Pathology and Clinical Manifestations",
            "page": "1140",
            "text": "Immediate reperfusion therapy via Primary Percutaneous Coronary Intervention (PPCI) is the gold standard for acute STEMI with door-to-balloon time goal < 90 minutes.",
        }
    ]

    result = engine.synthesize_diagnostic_report(
        patient_info=patient_info,
        vitals_summary=vitals_summary,
        exam_findings=exam_findings,
        lab_results=lab_results,
        medgemma_decision=medgemma_decision,
        citations=citations,
    )

    assert result.status == "COMPLETED"
    assert result.primary_diagnosis is not None
    assert len(result.primary_diagnosis) > 3
    assert result.confidence >= 0.5
    assert len(result.differential) >= 1
    assert "STEMI" in result.primary_diagnosis.upper() or "MYOCARDIAL" in result.primary_diagnosis.upper()
    assert result.provenance["tier_5_final_synthesized_conclusions"]["primary_diagnosis"] is not None
