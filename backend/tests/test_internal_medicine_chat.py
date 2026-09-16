"""
Test Suite for Dr. Marcus Vance Direct Clinical Chat & Diagnostic Grounding
Verifies conversational reasoning grounded in Harrison's Principles of Internal Medicine and MedGemma.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.llm.medgemma_service import medgemma_service
from backend.simulation.orchestrator import HospitalOrchestrator


client = TestClient(app)


def test_doctor_chat_cardiology_grounding():
    """Verifies Dr. Marcus Vance responds to acute chest pain with Harrison's citations and safety alerts."""
    orch = HospitalOrchestrator(enable_gpu=False)
    response = medgemma_service.generate_doctor_chat_response(
        messages=[{"role": "user", "content": "Doctor, what is the emergent protocol for 62yo male with acute substernal chest pressure and troponin elevation?"}],
        rag_context=[{
            "chapter": "Harrison's Principles of Internal Medicine - Chapter 273: Non-ST-Segment Elevation Acute Coronary Syndromes",
            "page": 1942,
            "text": "Initial medical therapy includes aspirin, P2Y12 receptor inhibitors, anticoagulation with unfractionated heparin, and anti-ischemic therapy. NSAIDs are strictly contraindicated."
        }]
    )
    assert response["doctor"] == "Dr. Marcus Vance, MD, FACP"
    assert "chest pain" in response["reply"].lower() or "coronary" in response["reply"].lower()
    assert len(response["differential"]) >= 1
    assert any("Aspirin" in t for t in response["guideline_therapy"])
    assert any("NSAID" in c for c in response["contraindications"])
    assert len(response["citations"]) >= 1


def test_doctor_chat_dka_grounding():
    """Verifies Dr. Marcus Vance identifies DKA and flags potassium contraindications."""
    response = medgemma_service.generate_doctor_chat_response(
        messages=[{"role": "user", "content": "24-year-old with Type 1 Diabetes in DKA, high anion gap, pH 7.14. Can I start insulin right now?"}],
        rag_context=[{
            "chapter": "Harrison's Principles of Internal Medicine - Chapter 397: Diabetes Mellitus and Acute Complications",
            "page": 2850,
            "text": "Intravenous insulin must not be administered if serum potassium is below 3.3 mEq/L due to the risk of precipitating lethal cardiac dysrhythmias."
        }]
    )
    assert response["doctor"] == "Dr. Marcus Vance, MD, FACP"
    assert any("potassium" in c.lower() for c in response["contraindications"])
    assert any("insulin" in t.lower() for t in response["guideline_therapy"])


def test_doctor_chat_api_endpoint():
    """Verifies POST /api/specialists/internal-medicine/chat returns 200 with structured response."""
    payload = {
        "message": "Doctor Vance, what workup do you recommend for acute dyspnea with pleuritic chest pain?",
        "conversation_history": [],
        "patient_context": {"age": 58, "sex": "Female", "history": "Recent DVT"}
    }
    res = client.post("/api/specialists/internal-medicine/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["doctor"] == "Dr. Marcus Vance, MD, FACP"
    assert "reply" in data and len(data["reply"]) > 20
    assert "differential" in data
    assert "citations" in data
    assert "telemetry" in data
    assert "Harrison's" in data["telemetry"]["knowledge_source"]


@pytest.mark.asyncio
async def test_specialist_consult_with_medgemma_diagnosis():
    """Verifies that formal consults now synthesize both Harrison's Evidence Brief and MedGemma reasoning."""
    orch = HospitalOrchestrator(enable_gpu=False)
    consult = await orch.conduct_specialist_consult(
        clinical_scenario="62yo male with substernal chest pressure radiating to arm, diaphoresis, troponin 1.84",
        abnormal_labs=["Troponin-I 1.84 ng/mL", "ECG ST depression"]
    )
    assert consult["specialist"] == "Dr. Marcus Vance, MD, FACP"
    assert consult["primary_diagnosis"] is not None
    assert "Harrison's" in consult["model_provenance"]
    assert "differential" in consult
    assert len(consult["citations"]) >= 1
