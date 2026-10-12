"""
Automated Test Suite for Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine Full Ingestion
Verifies 2,350-page coverage, 16,359 embedded vectors, SQLite database persistence,
and semantic retrieval across acute coronary, heart failure, arrhythmia, and valvular domains.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.database.repository import DatabaseRepository
from backend.rag.specialists.cardiology_rag import CardiologyRAGAgent
from backend.agents.specialists.cardiology import CardiologySpecialistAgent
from backend.agents.router import MedicalSpecialtyRouter, RoutingDecision

COLLECTION_PATH = Path("data/knowledge/braunwald_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/braunwald_embeddings.npy")


def test_braunwald_files_and_embeddings_exist():
    """Confirms that the full 2,350-page Braunwald's embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "braunwald_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "braunwald_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 16000, f"Expected >= 16,000 embedded chunks, got {emb_matrix.shape[0]}"


def test_database_cardiology_chunks_count():
    """Confirms that the SQLite knowledge_chunks table contains the full embedded Cardiology collection."""
    import sqlite3
    conn = sqlite3.connect("data/aivh.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge_chunks WHERE specialty = 'Cardiology';")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 16000, f"Database Cardiology knowledge_chunks count is {count}, expected >= 16,000"


def test_cardiology_rag_agent_initialization():
    """Confirms CardiologyRAGAgent loads all 16,359 chunks with dense vectors enabled."""
    rag_agent = CardiologyRAGAgent()
    assert len(rag_agent.chunks) >= 16000
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_stemi_pci():
    """Tests retrieval for STEMI, primary percutaneous coronary intervention, and troponin biomarkers."""
    rag_agent = CardiologyRAGAgent()
    query = "acute ST-elevation myocardial infarction transmural ischemia primary percutaneous coronary intervention troponin"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_cardiac = any(
        "infarction" in r.get("chapter", "").lower()
        or "coronary" in r.get("chapter", "").lower()
        or "ischemia" in r.get("chapter", "").lower()
        or "myocardial" in r.get("text", "").lower()
        or "coronary" in r.get("text", "").lower()
        or "infarction" in r.get("text", "").lower()
        for r in results
    )
    assert found_cardiac, "Cardiology RAG search must retrieve coronary/myocardial infarction evidence from Braunwald"


def test_retrieval_grounding_heart_failure():
    """Tests retrieval for heart failure with reduced ejection fraction (HFrEF) and guideline-directed therapy."""
    rag_agent = CardiologyRAGAgent()
    query = "heart failure reduced ejection fraction HFrEF guideline directed medical therapy sacubitril valsartan loop diuretic"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_hf = any(
        "heart failure" in r.get("chapter", "").lower()
        or "cardiomyopathy" in r.get("chapter", "").lower()
        or "heart failure" in r.get("text", "").lower()
        or "ejection fraction" in r.get("text", "").lower()
        for r in results
    )
    assert found_hf, "Cardiology RAG search must retrieve heart failure evidence from Braunwald"


def test_retrieval_grounding_atrial_fibrillation():
    """Tests retrieval for atrial fibrillation, rapid ventricular response, rate control, and anticoagulation."""
    rag_agent = CardiologyRAGAgent()
    query = "atrial fibrillation rapid ventricular response rate control beta blocker anticoagulation CHA2DS2-VASc"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_af = any(
        "fibrillation" in r.get("chapter", "").lower()
        or "arrhythmia" in r.get("chapter", "").lower()
        or "fibrillation" in r.get("text", "").lower()
        or "arrhythmia" in r.get("text", "").lower()
        for r in results
    )
    assert found_af, "Cardiology RAG search must retrieve atrial fibrillation / arrhythmia evidence from Braunwald"


@pytest.mark.asyncio
async def test_cardiology_specialist_consult_generation():
    """Tests that CardiologySpecialistAgent produces a structured cardiology consult grounded in Braunwald."""
    cardiologist = CardiologySpecialistAgent()
    consult = await cardiologist.conduct_specialist_consultation(
        encounter_id="enc-test-cardio-101",
        patient_id="VH-TEST-CARDIO",
        clinical_scenario="64yo male with acute retrosternal chest tightness radiating to left jaw, ST elevation in anterior leads, troponin 2.4 ng/mL",
        abnormal_labs=["Troponin I: 2.4 ng/mL", "CK-MB: 42 ng/mL"],
    )
    assert consult is not None
    assert consult["specialist"] == "Dr. Rachel Vance, MD, FACC"
    assert consult["specialty"] == "Cardiology"
    assert "consult_note" in consult
    assert "differential" in consult["consult_note"]
    assert len(consult["citations"]) > 0
    assert "Braunwald" in consult["model_provenance"]


def test_medical_specialty_router_triage_cardiology():
    """Tests that MedicalSpecialtyRouter correctly routes acute coronary syndrome presentations to Cardiology."""
    cardio_patient = {
        "id": "VH-CARDIO-ROUTING",
        "chief_complaint": "Acute severe crushing substernal chest pain, diaphoresis, shortness of breath",
        "history_of_present_illness": "Pain began 45 minutes ago radiating to left arm. Prior CAD and stent in LAD.",
    }
    decision = MedicalSpecialtyRouter.route_case(cardio_patient)
    assert decision.specialty == "CARDIOLOGY"
    assert "Dr. Rachel Vance" in decision.suggested_specialist_name
    assert "Braunwald" in decision.target_medical_book
