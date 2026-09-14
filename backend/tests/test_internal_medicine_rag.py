"""
Automated Test Suite for Internal Medicine Specialist RAG Agent
Tests query expansion, Harrison's retrieval, Evidence Brief synthesis, and specialist consults.
"""

import pytest
import asyncio
from backend.rag.specialists.internal_medicine_rag import InternalMedicineRAGAgent, EvidenceBrief
from backend.agents.specialists.internal_medicine import InternalMedicineSpecialistAgent
from backend.simulation.orchestrator import HospitalOrchestrator


def test_query_expansion():
    agent = InternalMedicineRAGAgent()
    expanded = agent.expand_query("Patient has severe chest pain and suspected nstemi")
    assert "angina pectoris" in expanded.lower() or "myocardial" in expanded.lower()
    assert "subendocardial" in expanded.lower() or "heparin" in expanded.lower()


def test_evidence_brief_generation_cardiology():
    agent = InternalMedicineRAGAgent()
    brief = agent.generate_evidence_brief(
        chief_complaint="Substernal chest pressure radiating to arm",
        hpi="Diaphoresis and elevated troponin",
        abnormal_labs=["Troponin-I 1.84", "ST-depression"]
    )
    assert brief.domain == "Cardiovascular Medicine"
    assert len(brief.citations) > 0
    assert any("Aspirin" in t for t in brief.recommended_therapy)
    assert any("NSAID" in c for c in brief.contraindications)


def test_evidence_brief_generation_endocrinology():
    agent = InternalMedicineRAGAgent()
    brief = agent.generate_evidence_brief(
        chief_complaint="Vomiting and fruity breath",
        hpi="Severe DKA with high anion gap acidosis",
        abnormal_labs=["Glucose 488", "Anion Gap 29", "pH 7.14"]
    )
    assert brief.domain == "Endocrinology & Metabolism"
    assert len(brief.citations) > 0
    assert any("saline" in t.lower() or "crystalloid" in t.lower() for t in brief.recommended_therapy)
    assert any("potassium" in c.lower() for c in brief.contraindications)


@pytest.mark.asyncio
async def test_specialist_consultation():
    orch = HospitalOrchestrator(enable_gpu=False)
    consult = await orch.conduct_specialist_consult(
        clinical_scenario="62yo male with acute chest pain, diaphoresis, and troponin elevation",
        abnormal_labs=["Troponin-I 1.84 ng/mL"],
    )
    assert consult["specialist"] == "Dr. Marcus Vance, MD, FACP"
    assert consult["specialty"] == "Internal Medicine"
    assert consult["domain"] == "Cardiovascular Medicine"
    assert len(consult["recommendations"]["immediate_workup"]) >= 3
    assert len(consult["citations"]) >= 1


@pytest.mark.asyncio
async def test_specialist_in_hospital_encounter():
    orch = HospitalOrchestrator(enable_gpu=False)
    result = await orch.run_encounter_simulation("CASE-101")
    assert result["primary_diagnosis"] == "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)"
    assert result["report"]["medical_knowledge_citations"] is not None
    assert len(result["report"]["medical_knowledge_citations"]) > 0
