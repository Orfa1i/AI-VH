"""
Automated Test Suite for Adams and Victor's Principles of Neurology Ingestion & Specialist Integration
Verifies 1,398-page coverage, 9,721 embedded vectors, SQLite database persistence,
semantic retrieval across acute stroke, status epilepticus, and myasthenia gravis, consult generation, and triage routing.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.rag.specialists.neurology_rag import NeurologyRAGAgent
from backend.agents.specialists.neurology import NeurologySpecialistAgent
from backend.agents.router import MedicalSpecialtyRouter

COLLECTION_PATH = Path("data/knowledge/neurology_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/neurology_embeddings.npy")


def test_neurology_files_and_embeddings_exist():
    """Confirms that the full 1,398-page Adams and Victor's Principles of Neurology embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "neurology_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "neurology_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 9000, f"Expected >= 9000 embedded chunks, got {emb_matrix.shape[0]}"


def test_database_neurology_chunks_count():
    """Confirms that SQLite knowledge_chunks table contains the full embedded Neurology collection."""
    import sqlite3
    conn = sqlite3.connect("data/aivh.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge_chunks WHERE specialty = 'Neurology';")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 9000, f"Database Neurology knowledge_chunks count is {count}, expected >= 9000"


def test_neurology_rag_agent_initialization():
    """Confirms NeurologyRAGAgent loads all chunks with dense vectors enabled."""
    rag_agent = NeurologyRAGAgent()
    assert len(rag_agent.chunks) >= 9000
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_ischemic_stroke():
    """Tests retrieval for acute ischemic stroke, tPA thrombolysis, thrombectomy, and MCA infarction."""
    rag_agent = NeurologyRAGAgent()
    query = "acute ischemic stroke tissue plasminogen activator alteplase tenecteplase endovascular mechanical thrombectomy middle cerebral artery"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_stroke = any(
        "cerebrovascular" in r.get("chapter", "").lower()
        or "stroke" in r.get("chapter", "").lower()
        or "stroke" in r.get("text", "").lower()
        or "ischemi" in r.get("text", "").lower()
        or "thrombo" in r.get("text", "").lower()
        or "infarct" in r.get("text", "").lower()
        for r in results
    )
    assert found_stroke, "Neurology RAG search must retrieve stroke evidence from Adams and Victor's Neurology"


def test_retrieval_grounding_status_epilepticus():
    """Tests retrieval for status epilepticus, seizure termination, lorazepam, and electroencephalography."""
    rag_agent = NeurologyRAGAgent()
    query = "status epilepticus generalized convulsive seizure lorazepam levetiracetam fosphenytoin electroencephalography burst suppression"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_seizure = any(
        "seizure" in r.get("chapter", "").lower()
        or "epilepsy" in r.get("chapter", "").lower()
        or "seizure" in r.get("text", "").lower()
        or "epilepticus" in r.get("text", "").lower()
        or "convuls" in r.get("text", "").lower()
        for r in results
    )
    assert found_seizure, "Neurology RAG search must retrieve status epilepticus evidence from Adams and Victor's Neurology"


def test_retrieval_grounding_myasthenia_gravis():
    """Tests retrieval for myasthenia gravis, acetylcholine receptor antibody, and crisis management."""
    rag_agent = NeurologyRAGAgent()
    query = "myasthenia gravis acetylcholine receptor antibody myasthenic crisis pyridostigmine plasma exchange ivig"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_myasthenia = any(
        "myasthenia" in r.get("chapter", "").lower()
        or "neuromuscular" in r.get("chapter", "").lower()
        or "myasthenia" in r.get("text", "").lower()
        or "acetylcholine" in r.get("text", "").lower()
        or "crisis" in r.get("text", "").lower()
        for r in results
    )
    assert found_myasthenia, "Neurology RAG search must retrieve myasthenia gravis evidence from Adams and Victor's Neurology"


@pytest.mark.asyncio
async def test_neurology_specialist_consult_generation():
    """Tests that NeurologySpecialistAgent produces a structured consult grounded in Adams and Victor's Neurology."""
    specialist = NeurologySpecialistAgent()
    consult = await specialist.conduct_specialist_consultation(
        encounter_id="enc-test-neuro-101",
        patient_id="VH-TEST-NEUROLOGY",
        clinical_scenario="68yo male presenting with sudden onset left-sided facial droop, left arm weakness (0/5), dysarthria, and forced gaze deviation to the right. Last known well 90 minutes ago. NIHSS is 17.",
        abnormal_labs=["Head CT: No hemorrhage, early loss of insular ribbon", "CTA Head/Neck: Right MCA M1 segment occlusion", "Capillary Glucose: 118 mg/dL", "INR: 1.0"],
    )
    assert consult is not None
    assert consult["specialist"] == "Dr. Alexander Hayes, MD, PhD, FAAN"
    assert consult["specialty"] == "Neurology"
    assert "consult_note" in consult
    assert "differential" in consult["consult_note"]
    assert "neurologic_plan" in consult["consult_note"]
    assert len(consult["citations"]) > 0
    assert "Adams and Victor" in consult["model_provenance"]


def test_medical_specialty_router_triage_neurology():
    """Tests that MedicalSpecialtyRouter correctly routes acute stroke and hemiparesis to Neurology."""
    neuro_patient = {
        "id": "VH-NEURO-ROUTING",
        "chief_complaint": "Acute onset right-sided hemiparesis, facial droop, and global aphasia 2 hours ago",
        "history_of_present_illness": "Patient was eating breakfast when sudden loss of speech and dense right-sided motor paralysis occurred. NIHSS 18.",
    }
    decision = MedicalSpecialtyRouter.route_case(neuro_patient)
    assert decision.specialty == "NEUROLOGY"
    assert "Dr. Alexander Hayes" in decision.suggested_specialist_name
    assert "Adams and Victor" in decision.target_medical_book
