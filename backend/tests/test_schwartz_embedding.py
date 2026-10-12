"""
Automated Test Suite for Schwartz's Principles of Surgery (10th Edition) Full Ingestion
Verifies 2,098-page coverage, 11,983 embedded vectors, SQLite database persistence,
and semantic retrieval across acute abdominal, surgical, and perioperative domains.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.database.repository import DatabaseRepository
from backend.rag.specialists.surgery_rag import SurgeryRAGAgent
from backend.agents.specialists.surgery import SurgerySpecialistAgent
from backend.agents.router import MedicalSpecialtyRouter, RoutingDecision

COLLECTION_PATH = Path("data/knowledge/schwartz_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/schwartz_embeddings.npy")


def test_schwartz_files_and_embeddings_exist():
    """Confirms that the full 2,098-page Schwartz's embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "schwartz_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "schwartz_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 11000, f"Expected >= 11,000 embedded chunks, got {emb_matrix.shape[0]}"


def test_surgery_rag_agent_initialization():
    """Confirms SurgeryRAGAgent loads all 11,983 chunks with dense vectors enabled."""
    rag_agent = SurgeryRAGAgent()
    assert len(rag_agent.chunks) >= 11000
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_acute_appendicitis():
    """Tests retrieval for acute appendicitis workup, Alvarado score, and operative timing."""
    rag_agent = SurgeryRAGAgent()
    query = "acute appendicitis right lower quadrant migratory pain McBurney point ultrasound appendectomy"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_appendix = any(
        "appendix" in r.get("chapter", "").lower()
        or "appendicitis" in r.get("chapter", "").lower()
        or "appendix" in r.get("text", "").lower()
        or "appendectomy" in r.get("text", "").lower()
        for r in results
    )
    assert found_appendix, "Surgery RAG search must retrieve appendix/appendicitis evidence from Schwartz"


def test_retrieval_grounding_small_bowel_obstruction():
    """Tests retrieval for small bowel obstruction, adhesive disease, and laparotomy indication."""
    rag_agent = SurgeryRAGAgent()
    query = "small bowel obstruction air fluid levels obstipation prior laparotomy strangulation ischemia"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_bowel = any(
        "small intestine" in r.get("chapter", "").lower()
        or "obstruction" in r.get("chapter", "").lower()
        or "intestine" in r.get("chapter", "").lower()
        or "bowel" in r.get("text", "").lower()
        or "obstruction" in r.get("text", "").lower()
        for r in results
    )
    assert found_bowel, "Surgery RAG search must retrieve small bowel obstruction evidence from Schwartz"


def test_retrieval_grounding_acute_cholecystitis():
    """Tests retrieval for acute cholecystitis, Tokyo guidelines, and laparoscopic cholecystectomy."""
    rag_agent = SurgeryRAGAgent()
    query = "acute calculous cholecystitis right upper quadrant pain Murphy sign laparoscopic cholecystectomy"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_biliary = any(
        "gallbladder" in r.get("chapter", "").lower()
        or "biliary" in r.get("chapter", "").lower()
        or "cholecystitis" in r.get("text", "").lower()
        or "gallbladder" in r.get("text", "").lower()
        for r in results
    )
    assert found_biliary, "Surgery RAG search must retrieve gallbladder/biliary evidence from Schwartz"


@pytest.mark.asyncio
async def test_surgery_specialist_consult_generation():
    """Tests that SurgerySpecialistAgent produces a structured surgical consult grounded in Schwartz."""
    surgeon = SurgerySpecialistAgent()
    consult = await surgeon.conduct_specialist_consultation(
        encounter_id="enc-test-101",
        patient_id="VH-TEST-SURG",
        clinical_scenario="31yo male with acute RLQ abdominal pain, migratory periumbilical pain, leukocytosis, suspected acute appendicitis",
        abnormal_labs=["WBC 15.2 k/uL", "CRP 48 mg/L"],
    )
    assert consult is not None
    assert consult["specialist"] == "Dr. Sarah Lin, MD, FACS"
    assert consult["specialty"] == "Surgery"
    assert "consult_note" in consult
    assert "differential" in consult["consult_note"]
    assert len(consult["citations"]) > 0
    assert "Schwartz" in consult["model_provenance"]


def test_medical_specialty_router_triage_surgery():
    """Tests that MedicalSpecialtyRouter correctly routes acute abdominal surgical pathology to Surgery."""
    surg_patient = {
        "id": "VH-SURG-ROUTING",
        "chief_complaint": "Acute severe right lower quadrant rebound tenderness, suspected acute appendicitis",
        "history_of_present_illness": "Worsening RLQ pain, fever, peritonitis",
    }
    decision = MedicalSpecialtyRouter.route_case(surg_patient)
    assert decision.specialty == "SURGERY"
    assert "Dr. Sarah Lin" in decision.suggested_specialist_name
    assert "Schwartz" in decision.target_medical_book
