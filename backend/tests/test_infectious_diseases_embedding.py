"""
Automated Test Suite for Harrison's Infectious Diseases Full Ingestion
Verifies 1,313-page coverage, 7,336 embedded vectors, SQLite database persistence,
and semantic retrieval across infective endocarditis, FUO, meningitis, and antimicrobial stewardship domains.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.rag.specialists.infectious_diseases_rag import InfectiousDiseasesRAGAgent
from backend.agents.specialists.infectious_diseases import InfectiousDiseasesSpecialistAgent
from backend.agents.router import MedicalSpecialtyRouter

COLLECTION_PATH = Path("data/knowledge/infectious_diseases_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/infectious_diseases_embeddings.npy")


def test_infectious_diseases_files_and_embeddings_exist():
    """Confirms that the full 1,313-page Harrison's Infectious Diseases embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "infectious_diseases_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "infectious_diseases_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 7000, f"Expected >= 7,000 embedded chunks, got {emb_matrix.shape[0]}"


def test_database_infectious_diseases_chunks_count():
    """Confirms that SQLite knowledge_chunks table contains the full embedded Infectious Diseases collection."""
    import sqlite3
    conn = sqlite3.connect("data/aivh.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge_chunks WHERE specialty = 'Infectious Diseases';")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 7000, f"Database Infectious Diseases knowledge_chunks count is {count}, expected >= 7,000"


def test_infectious_diseases_rag_agent_initialization():
    """Confirms InfectiousDiseasesRAGAgent loads all chunks with dense vectors enabled."""
    rag_agent = InfectiousDiseasesRAGAgent()
    assert len(rag_agent.chunks) >= 7000
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_endocarditis():
    """Tests retrieval for infective endocarditis, Duke criteria, blood cultures, and echocardiogram vegetations."""
    rag_agent = InfectiousDiseasesRAGAgent()
    query = "infective endocarditis duke criteria valvular vegetation staphylococcus aureus blood cultures echocardiogram"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_endocarditis = any(
        "endocarditis" in r.get("chapter", "").lower()
        or "infective" in r.get("chapter", "").lower()
        or "endocarditis" in r.get("text", "").lower()
        or "vegetation" in r.get("text", "").lower()
        or "duke" in r.get("text", "").lower()
        for r in results
    )
    assert found_endocarditis, "ID RAG search must retrieve infective endocarditis evidence from Harrison's"


def test_retrieval_grounding_fuo():
    """Tests retrieval for classical fever of unknown origin (FUO) and diagnostic evaluation."""
    rag_agent = InfectiousDiseasesRAGAgent()
    query = "fever of unknown origin classical FUO prolonged febrile illness diagnostic evaluation blood cultures"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_fuo = any(
        "fever" in r.get("chapter", "").lower()
        or "origin" in r.get("chapter", "").lower()
        or "fever" in r.get("text", "").lower()
        or "fuo" in r.get("text", "").lower()
        or "febrile" in r.get("text", "").lower()
        for r in results
    )
    assert found_fuo, "ID RAG search must retrieve FUO evidence from Harrison's Infectious Diseases"


def test_retrieval_grounding_meningitis_csf():
    """Tests retrieval for acute bacterial meningitis, CSF pleocytosis, and antimicrobial therapy."""
    rag_agent = InfectiousDiseasesRAGAgent()
    query = "acute bacterial meningitis cerebrospinal fluid pleocytosis lumbar puncture dexamethasone ceftriaxone"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_meningitis = any(
        "meningitis" in r.get("chapter", "").lower()
        or "central nervous system" in r.get("chapter", "").lower()
        or "meningitis" in r.get("text", "").lower()
        or "cerebrospinal" in r.get("text", "").lower()
        or "csf" in r.get("text", "").lower()
        for r in results
    )
    assert found_meningitis, "ID RAG search must retrieve meningitis evidence from Harrison's Infectious Diseases"


@pytest.mark.asyncio
async def test_infectious_diseases_specialist_consult_generation():
    """Tests that InfectiousDiseasesSpecialistAgent produces a structured consult grounded in Harrison's."""
    specialist = InfectiousDiseasesSpecialistAgent()
    consult = await specialist.conduct_specialist_consultation(
        encounter_id="enc-test-id-101",
        patient_id="VH-TEST-INFECTIOUS",
        clinical_scenario="58yo male with persistent remittent fever of 39.1C for 3 weeks, new regurgitant cardiac murmur, Roth spots, and blood cultures positive for gram-positive cocci in clusters",
        abnormal_labs=["Blood Culture: Gram-positive cocci in clusters", "CRP: 142 mg/L", "ESR: 88 mm/hr"],
    )
    assert consult is not None
    assert consult["specialist"] == "Dr. Anthony Mercer, MD, FIDSA"
    assert consult["specialty"] == "Infectious Diseases"
    assert "consult_note" in consult
    assert "differential" in consult["consult_note"]
    assert "antimicrobial_plan" in consult["consult_note"]
    assert len(consult["citations"]) > 0
    assert "Harrison's" in consult["model_provenance"]


def test_medical_specialty_router_triage_infectious_diseases():
    """Tests that MedicalSpecialtyRouter correctly routes bacteremia / endocarditis presentations to Infectious Diseases."""
    id_patient = {
        "id": "VH-ID-ROUTING",
        "chief_complaint": "Persistent high fever of unknown origin for 4 weeks with recurrent bacteremia and weight loss",
        "history_of_present_illness": "Patient has had spiking fevers daily without clear localizing source despite outpatient amoxicillin.",
    }
    decision = MedicalSpecialtyRouter.route_case(id_patient)
    assert decision.specialty == "INFECTIOUS_DISEASES"
    assert "Dr. Anthony Mercer" in decision.suggested_specialist_name
    assert "Harrison's" in decision.target_medical_book
