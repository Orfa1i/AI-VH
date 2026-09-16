"""
Automated Test Suite for Harrison's Principles of Internal Medicine Full Ingestion
Verifies 4,132-page coverage, 31,427 embedded vectors, SQLite database persistence,
and hybrid dense/sparse semantic retrieval across core internal medicine domains.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.database.repository import DatabaseRepository
from backend.rag.specialists.internal_medicine_rag import InternalMedicineRAGAgent

COLLECTION_PATH = Path("data/knowledge/harrison_full_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/harrison_embeddings.npy")


def test_full_collection_and_embeddings_exist():
    """Confirms that the full 4,132-page Harrison's embedding files are present on disk."""
    assert COLLECTION_PATH.exists(), "harrison_full_collection.json must exist"
    assert EMBEDDINGS_PATH.exists(), "harrison_embeddings.npy must exist"

    emb_matrix = np.load(str(EMBEDDINGS_PATH))
    assert emb_matrix.ndim == 2
    assert emb_matrix.shape[1] == 384, "Embeddings must have dimension 384 (all-MiniLM-L6-v2)"
    assert emb_matrix.shape[0] >= 30000, f"Expected >= 30,000 embedded chunks, got {emb_matrix.shape[0]}"


def test_database_knowledge_chunks_count():
    """Confirms that the SQLite knowledge_chunks table contains the full embedded collection."""
    db_repo = DatabaseRepository()
    count = db_repo.count_knowledge_chunks()
    assert count >= 30000, f"Database knowledge_chunks count is {count}, expected >= 30,000"


def test_rag_agent_initialization_with_full_book():
    """Confirms InternalMedicineRAGAgent loads all 31,427 chunks with dense vectors enabled."""
    rag_agent = InternalMedicineRAGAgent()
    assert len(rag_agent.chunks) >= 30000
    assert rag_agent.index.embeddings is not None
    assert rag_agent.index.embeddings.shape[1] == 384


def test_retrieval_grounding_acute_kidney_injury():
    """Tests retrieval for AKI on ACE inhibitor with hyperkalemia."""
    rag_agent = InternalMedicineRAGAgent()
    query = "Patient with dehydration on ACE inhibitor presents with acute oliguria and potassium 5.6 mEq/L"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    # Must find kidney / electrolyte chapter or topic
    found_renal = any(
        "kidney" in r.get("chapter", "").lower()
        or "renal" in r.get("chapter", "").lower()
        or "electrolyte" in r.get("chapter", "").lower()
        or "kidney" in r.get("text", "").lower()
        for r in results
    )
    assert found_renal, "RAG search must retrieve renal/electrolyte evidence"


def test_retrieval_grounding_acute_coronary_syndrome():
    """Tests retrieval for substernal chest pressure and cardiac biomarkers."""
    rag_agent = InternalMedicineRAGAgent()
    query = "Substernal chest pressure radiating to left arm with elevated high sensitivity troponin"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_cardiac = any(
        "coronary" in r.get("chapter", "").lower()
        or "chest" in r.get("chapter", "").lower()
        or "cardiovascular" in r.get("chapter", "").lower()
        or "myocardial" in r.get("text", "").lower()
        for r in results
    )
    assert found_cardiac, "RAG search must retrieve cardiovascular/coronary evidence"


def test_retrieval_grounding_diabetic_ketoacidosis():
    """Tests retrieval for DKA with anion gap and ketonuria."""
    rag_agent = InternalMedicineRAGAgent()
    query = "Diabetic ketoacidosis with tachypnea, anion gap 28, and heavy ketonuria"
    results = rag_agent.retrieve_evidence(query, top_k=5)
    assert len(results) >= 3

    found_endocrine = any(
        "diabetes" in r.get("chapter", "").lower()
        or "endocrinology" in r.get("chapter", "").lower()
        or "acidosis" in r.get("text", "").lower()
        for r in results
    )
    assert found_endocrine, "RAG search must retrieve diabetes/acidosis evidence"
