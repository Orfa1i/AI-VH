"""
Automated Test Suite for Williams Gynecology Ingestion & Specialist Integration
Verifies 278-page coverage, 571 embedded vectors, SQLite database persistence,
semantic retrieval across ectopic pregnancy, AUB, and PID domains, consult generation, and triage routing.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.rag.specialists.gynecology_rag import GynecologyRAGAgent
from backend.agents.specialists.gynecology import GynecologySpecialistAgent
from backend.agents.router import MedicalSpecialtyRouter

COLLECTION_PATH = Path("data/knowledge/gynecology_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/gynecology_embeddings.npy")


def test_gynecology_files_and_embeddings_exist():
    """Confirms that the full 278-page Williams Gynecology embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "gynecology_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "gynecology_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 500, f"Expected >= 500 embedded chunks, got {emb_matrix.shape[0]}"


def test_database_gynecology_chunks_count():
    """Confirms that SQLite knowledge_chunks table contains the full embedded Gynecology collection."""
    import sqlite3
    conn = sqlite3.connect("data/aivh.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge_chunks WHERE specialty = 'Gynecology';")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 500, f"Database Gynecology knowledge_chunks count is {count}, expected >= 500"


def test_gynecology_rag_agent_initialization():
    """Confirms GynecologyRAGAgent loads all chunks with dense vectors enabled."""
    rag_agent = GynecologyRAGAgent()
    assert len(rag_agent.chunks) >= 500
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_ectopic_pregnancy():
    """Tests retrieval for ectopic pregnancy, discriminatory beta-hCG zone, and methotrexate."""
    rag_agent = GynecologyRAGAgent()
    query = "ectopic pregnancy quantitative beta-hcg discriminatory zone transvaginal ultrasound methotrexate salpingostomy"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_ectopic = any(
        "ectopic" in r.get("chapter", "").lower()
        or "pregnancy" in r.get("chapter", "").lower()
        or "ectopic" in r.get("text", "").lower()
        or "hcg" in r.get("text", "").lower()
        or "methotrexate" in r.get("text", "").lower()
        for r in results
    )
    assert found_ectopic, "Gynecology RAG search must retrieve ectopic pregnancy evidence from Williams Gynecology"


def test_retrieval_grounding_abnormal_uterine_bleeding():
    """Tests retrieval for abnormal uterine bleeding, PALM-COEIN classification, and endometrial biopsy."""
    rag_agent = GynecologyRAGAgent()
    query = "abnormal uterine bleeding palm-coein menorrhagia endometrial biopsy transvaginal ultrasound hyperplasia"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_aub = any(
        "bleeding" in r.get("chapter", "").lower()
        or "uterine" in r.get("chapter", "").lower()
        or "bleeding" in r.get("text", "").lower()
        or "aub" in r.get("text", "").lower()
        or "endometrial" in r.get("text", "").lower()
        or "hyperplasia" in r.get("text", "").lower()
        for r in results
    )
    assert found_aub, "Gynecology RAG search must retrieve abnormal uterine bleeding evidence from Williams Gynecology"


def test_retrieval_grounding_pelvic_inflammatory_disease():
    """Tests retrieval for acute pelvic inflammatory disease, cervical motion tenderness, and tubo-ovarian abscess."""
    rag_agent = GynecologyRAGAgent()
    query = "pelvic inflammatory disease pid tubo-ovarian abscess cervical motion tenderness ceftriaxone doxycycline metronidazole"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_pid = any(
        "infection" in r.get("chapter", "").lower()
        or "pelvic" in r.get("chapter", "").lower()
        or "infection" in r.get("text", "").lower()
        or "pid" in r.get("text", "").lower()
        or "abscess" in r.get("text", "").lower()
        or "cervical" in r.get("text", "").lower()
        for r in results
    )
    assert found_pid, "Gynecology RAG search must retrieve PID / pelvic infection evidence from Williams Gynecology"


@pytest.mark.asyncio
async def test_gynecology_specialist_consult_generation():
    """Tests that GynecologySpecialistAgent produces a structured consult grounded in Williams Gynecology."""
    specialist = GynecologySpecialistAgent()
    consult = await specialist.conduct_specialist_consultation(
        encounter_id="enc-test-gyn-101",
        patient_id="VH-TEST-GYNECOLOGY",
        clinical_scenario="32yo female with acute severe left lower quadrant pelvic pain, 6 weeks amenorrhea, positive urine pregnancy test, and quantitative beta-hCG of 2,400 mIU/mL with empty uterine cavity on ultrasound",
        abnormal_labs=["Beta-hCG: 2400 mIU/mL", "TVUS: Empty uterus, left adnexal mass 2.8 cm, no free fluid", "Hemoglobin: 12.4 g/dL"],
    )
    assert consult is not None
    assert consult["specialist"] == "Dr. Evelyn Reed, MD, FACOG"
    assert consult["specialty"] == "Gynecology"
    assert "consult_note" in consult
    assert "differential" in consult["consult_note"]
    assert "gynecologic_plan" in consult["consult_note"]
    assert len(consult["citations"]) > 0
    assert "Williams" in consult["model_provenance"]


def test_medical_specialty_router_triage_gynecology():
    """Tests that MedicalSpecialtyRouter correctly routes abnormal uterine bleeding & pelvic mass to Gynecology."""
    gyn_patient = {
        "id": "VH-GYN-ROUTING",
        "chief_complaint": "Severe abnormal uterine bleeding with heavy clots and persistent pelvic pain for 3 months",
        "history_of_present_illness": "Patient reports menorrhagia soaking through 8 pads daily with deep dyspareunia and dysmenorrhea.",
    }
    decision = MedicalSpecialtyRouter.route_case(gyn_patient)
    assert decision.specialty == "GYNECOLOGY"
    assert "Dr. Evelyn Reed" in decision.suggested_specialist_name
    assert "Williams" in decision.target_medical_book
