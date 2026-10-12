"""
Unit and Integration Tests for Ground Truth Isolation and Shared Knowledge Sources (Phase 3).
Verifies:
1. Ground Truth Isolation: Specialist agents determine diagnostic workup autonomously
   without peeking at toolkit.ground_truth.recommended_labs.
2. Shared Knowledge Service: RxNorm and NABD drug profile lookup and citation retrieval.
3. Multi-Specialty Citation Integration: Harrison's / Braunwald's medical book evidence
   is combined with shared knowledge pharmacology citations.
"""

import pytest
from unittest.mock import MagicMock
from backend.clinical.models import LabTestType, VitalSigns
from backend.agents.specialists.internal_medicine import InternalMedicineSpecialistAgent
from backend.agents.specialists.cardiology import CardiologySpecialistAgent
from backend.rag.shared_sources import shared_knowledge_service
from backend.llm.model_config import get_model_id


def test_internal_medicine_autonomous_diagnostic_workup():
    """Verify IM agent autonomously selects labs based on clinical presentation without ground truth."""
    agent = InternalMedicineSpecialistAgent(
        rag_agent=MagicMock(),
        medgemma_service=MagicMock(),
    )

    # 1. Cardiovascular / ACS syndrome
    vitals = VitalSigns(
        heart_rate=95,
        systolic_bp=135,
        diastolic_bp=85,
        respiratory_rate=18,
        temperature_c=36.8,
        spo2_percent=98.0,
        pain_score=8,
    )
    workup = agent.determine_diagnostic_workup(
        chief_complaint="Substernal chest pressure and dyspnea",
        hpi="62-year-old male with 2 hours of crushing substernal chest pain radiating to left arm",
        vitals=vitals,
    )
    assert LabTestType.CBC in workup
    assert LabTestType.BMP in workup
    assert LabTestType.ECG_12_LEAD in workup
    assert LabTestType.TROPONIN_I in workup
    assert LabTestType.CXR in workup

    # 2. DKA syndrome
    workup_dka = agent.determine_diagnostic_workup(
        chief_complaint="Nausea, vomiting, and extreme thirst",
        hpi="24-year-old with type 1 diabetes presenting with elevated glucose and Kussmaul respirations",
        vitals=vitals,
    )
    assert LabTestType.BMP in workup_dka
    assert LabTestType.URINALYSIS in workup_dka
    assert LabTestType.ABG in workup_dka
    assert LabTestType.LACTATE in workup_dka

    # 3. Sepsis / Fever syndrome
    fever_vitals = VitalSigns(
        heart_rate=115,
        systolic_bp=88,
        diastolic_bp=55,
        respiratory_rate=24,
        temperature_c=39.2,
        spo2_percent=94.0,
    )
    workup_sepsis = agent.determine_diagnostic_workup(
        chief_complaint="High fever and productive cough",
        hpi="Presents with severe chills and purulent sputum",
        vitals=fever_vitals,
    )
    assert LabTestType.CBC in workup_sepsis
    assert LabTestType.CXR in workup_sepsis
    assert LabTestType.LACTATE in workup_sepsis
    assert LabTestType.URINALYSIS in workup_sepsis


def test_cardiology_autonomous_diagnostic_workup():
    """Verify Cardiology agent autonomously selects cardiac investigations without ground truth."""
    agent = CardiologySpecialistAgent(
        rag_agent=MagicMock(),
        medgemma_service=MagicMock(),
    )

    vitals_chf = VitalSigns(
        heart_rate=102,
        systolic_bp=150,
        diastolic_bp=92,
        respiratory_rate=26,
        temperature_c=37.0,
        spo2_percent=91.0,
    )
    workup_chf = agent.determine_diagnostic_workup(
        chief_complaint="Severe shortness of breath and leg swelling",
        hpi="70-year-old female with acute heart failure exacerbation, orthopnea, and bilateral lung rales",
        vitals=vitals_chf,
    )
    assert LabTestType.ECG_12_LEAD in workup_chf
    assert LabTestType.TROPONIN_I in workup_chf
    assert LabTestType.BNP in workup_chf
    assert LabTestType.CXR in workup_chf
    assert LabTestType.BMP in workup_chf


def test_shared_knowledge_service_pharmacology_retrieval():
    """Verify SharedKnowledgeService returns structured clinical pharmacology citations."""
    query = "Patient with acute coronary syndrome taking aspirin, ticagrelor, and lisinopril"
    citations = shared_knowledge_service.retrieve_shared_evidence(query, top_k=3)

    assert len(citations) >= 1
    top = citations[0]
    assert top["source"] == "nabd_rxnorm"
    assert "generic_name" in top or "chapter" in top
    assert "text" in top
    assert len(top["text"]) > 10


def test_specialist_consultation_provenance():
    """Verify model provenance in consult matches resolved model ID."""
    im_rag = MagicMock()
    im_rag.generate_evidence_brief.return_value = MagicMock(
        query="Chest pain",
        domain="Cardiovascular",
        citations=[{"source": "harrison", "chapter": "Acute Coronary Syndromes", "page": "1800"}],
        clinical_summary="Summary",
        recommended_workup=["ECG"],
        recommended_therapy=["Aspirin"],
        contraindications=["NSAIDs"],
        to_dict=lambda: {"domain": "Cardiovascular"},
    )
    im_service = MagicMock()
    im_service.generate_clinical_decision.return_value = {
        "primary_diagnosis": "Unstable Angina",
        "confidence": 0.92,
        "clinical_reasoning": "Reasoning",
        "differential": [],
        "treatment_plan": ["Aspirin 325 mg"],
    }

    im_agent = InternalMedicineSpecialistAgent(
        rag_agent=im_rag,
        medgemma_service=im_service,
    )

    import asyncio
    consult = asyncio.run(
        im_agent.conduct_specialist_consultation(
            encounter_id="ENC-TEST-001",
            patient_id="PAT-TEST-001",
            clinical_scenario="Substernal chest pressure on exertion",
        )
    )

    expected_model = get_model_id()
    assert expected_model in consult["model_provenance"]
    assert "Harrison's" in consult["model_provenance"]
