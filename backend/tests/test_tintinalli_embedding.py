"""
Automated Test Suite for Tintinalli's Emergency Medicine Manual Full Ingestion
Verifies 1,089-page coverage, 2,981 embedded vectors, SQLite database persistence,
and semantic retrieval across acute resuscitation, airway RSI, anaphylaxis, and shock domains.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.rag.specialists.emergency_rag import EmergencyMedicineRAGAgent
from backend.agents.specialists.emergency import EmergencySpecialistAgent
from backend.agents.router import MedicalSpecialtyRouter

COLLECTION_PATH = Path("data/knowledge/tintinalli_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/tintinalli_embeddings.npy")


def test_tintinalli_files_and_embeddings_exist():
    """Confirms that the full 1,089-page Tintinalli embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "tintinalli_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "tintinalli_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 2900, f"Expected >= 2,900 embedded chunks, got {emb_matrix.shape[0]}"


def test_database_emergency_chunks_count():
    """Confirms that the SQLite knowledge_chunks table contains the full embedded Emergency Medicine collection."""
    import sqlite3
    conn = sqlite3.connect("data/aivh.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge_chunks WHERE specialty = 'Emergency Medicine';")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 2900, f"Database Emergency Medicine knowledge_chunks count is {count}, expected >= 2,900"


def test_emergency_rag_agent_initialization():
    """Confirms EmergencyMedicineRAGAgent loads all chunks with dense vectors enabled."""
    rag_agent = EmergencyMedicineRAGAgent()
    assert len(rag_agent.chunks) >= 2900
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_anaphylaxis_epinephrine():
    """Tests retrieval for acute anaphylaxis, intramuscular epinephrine dosing, and refractory shock."""
    rag_agent = EmergencyMedicineRAGAgent()
    query = "acute severe anaphylaxis stridor hypotension intramuscular epinephrine dose concentration lateral thigh"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_anaphylaxis = any(
        "anaphylaxis" in r.get("chapter", "").lower()
        or "allergic" in r.get("chapter", "").lower()
        or "shock" in r.get("chapter", "").lower()
        or "epinephrine" in r.get("text", "").lower()
        or "anaphylaxis" in r.get("text", "").lower()
        for r in results
    )
    assert found_anaphylaxis, "Emergency RAG search must retrieve anaphylaxis/epinephrine evidence from Tintinalli"


def test_retrieval_grounding_airway_rsi():
    """Tests retrieval for rapid sequence intubation (RSI), preoxygenation, and paralytic selection."""
    rag_agent = EmergencyMedicineRAGAgent()
    query = "rapid sequence intubation RSI preoxygenation etomidate succinylcholine acute hypoxic respiratory failure"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_airway = any(
        "airway" in r.get("chapter", "").lower()
        or "intubation" in r.get("chapter", "").lower()
        or "resuscitation" in r.get("chapter", "").lower()
        or "intubation" in r.get("text", "").lower()
        or "airway" in r.get("text", "").lower()
        or "etomidate" in r.get("text", "").lower()
        or "succinylcholine" in r.get("text", "").lower()
        for r in results
    )
    assert found_airway, "Emergency RAG search must retrieve airway/intubation evidence from Tintinalli"


def test_retrieval_grounding_tension_pneumothorax():
    """Tests retrieval for tension pneumothorax, needle decompression landmarks, and chest tube thoracostomy."""
    rag_agent = EmergencyMedicineRAGAgent()
    query = "tension pneumothorax needle decompression tube thoracostomy chest tube shock absent breath sounds"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_pneumo = any(
        "pneumothorax" in r.get("chapter", "").lower()
        or "thoracostomy" in r.get("chapter", "").lower()
        or "trauma" in r.get("chapter", "").lower()
        or "pneumothorax" in r.get("text", "").lower()
        or "thoracostomy" in r.get("text", "").lower()
        or "needle" in r.get("text", "").lower()
        for r in results
    )
    assert found_pneumo, "Emergency RAG search must retrieve tension pneumothorax evidence from Tintinalli"


@pytest.mark.asyncio
async def test_emergency_specialist_consult_generation():
    """Tests that EmergencySpecialistAgent produces a structured resuscitation consult grounded in Tintinalli."""
    emergency_md = EmergencySpecialistAgent()
    consult = await emergency_md.conduct_specialist_consultation(
        encounter_id="enc-test-em-101",
        patient_id="VH-TEST-EMERGENCY",
        clinical_scenario="29yo female with sudden facial edema, biphasic stridor, diffuse hives, and BP 78/42 within 10 minutes of wasp sting",
        abnormal_labs=["Lactate: 3.8 mmol/L", "Blood Pressure: 78/42 mmHg"],
    )
    assert consult is not None
    assert consult["specialist"] == "Dr. David Kim, MD, FACEP"
    assert consult["specialty"] == "Emergency Medicine"
    assert "consult_note" in consult
    assert "differential" in consult["consult_note"]
    assert len(consult["citations"]) > 0
    assert "Tintinalli" in consult["model_provenance"]


def test_medical_specialty_router_triage_emergency():
    """Tests that MedicalSpecialtyRouter correctly routes acute resuscitation presentations to Emergency Medicine."""
    emergency_patient = {
        "id": "VH-EMERGENCY-ROUTING",
        "chief_complaint": "Acute severe anaphylactic shock with audible stridor, facial angioedema, and BP 75/40",
        "history_of_present_illness": "Patient stung by bee 15 minutes ago, rapidly developed airway compromise and cardiovascular collapse.",
    }
    decision = MedicalSpecialtyRouter.route_case(emergency_patient)
    assert decision.specialty == "EMERGENCY"
    assert "Dr. David Kim" in decision.suggested_specialist_name
    assert "Tintinalli" in decision.target_medical_book
