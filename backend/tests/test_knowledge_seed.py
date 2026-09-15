"""
Automated Test Suite for Medical Knowledge Seeding & Semantic Retrieval
Tests Harrison's chunk ingestion, embedding computation, idempotent upserts,
cosine vector ranking precision, and knowledge REST endpoints.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.database.connection import DatabaseConnectionManager
from backend.database.repository import DatabaseRepository
from backend.database.seed_knowledge import seed_harrison_knowledge
from backend.main import app


@pytest.fixture
def temp_knowledge_db():
    """Creates an isolated temporary database for knowledge testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    
    manager = DatabaseConnectionManager(sqlite_path=temp_path)
    repo = DatabaseRepository(manager=manager)
    yield repo
    
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def test_seed_knowledge_execution(temp_knowledge_db):
    assert temp_knowledge_db.count_knowledge_chunks() == 0
    res = seed_harrison_knowledge(temp_knowledge_db)
    
    assert res["status"] == "success"
    assert res["seeded_count"] >= 10
    assert temp_knowledge_db.count_knowledge_chunks() == res["seeded_count"]


def test_seed_is_idempotent(temp_knowledge_db):
    res1 = seed_harrison_knowledge(temp_knowledge_db)
    count1 = temp_knowledge_db.count_knowledge_chunks()
    assert count1 > 0

    # Seed a second time
    res2 = seed_harrison_knowledge(temp_knowledge_db)
    count2 = temp_knowledge_db.count_knowledge_chunks()
    assert count1 == count2


def test_semantic_search_accuracy(temp_knowledge_db):
    seed_harrison_knowledge(temp_knowledge_db)

    # 1. Chest pain / Acute Coronary Syndrome
    acs_results = temp_knowledge_db.search_knowledge_chunks("Acute Coronary Syndromes MI troponin", top_k=3)
    assert len(acs_results) > 0
    top_acs = acs_results[0]
    assert "Coronary" in top_acs["topic"] or "Chest" in top_acs["topic"]
    assert top_acs["score"] > 0.3

    # 2. Diabetic Ketoacidosis
    dka_results = temp_knowledge_db.search_knowledge_chunks("Diabetic Ketoacidosis Hyperglycemia insulin", top_k=3)
    assert len(dka_results) > 0
    top_dka = dka_results[0]
    assert "Diabetic" in top_dka["topic"] or "Ketoacidosis" in top_dka["topic"]
    assert top_dka["score"] > 0.3

    # 3. Acute Kidney Injury
    aki_results = temp_knowledge_db.search_knowledge_chunks("Acute Kidney Injury oliguria creatinine", top_k=3)
    assert len(aki_results) > 0
    top_aki = aki_results[0]
    assert "Kidney" in top_aki["topic"] or "AKI" in top_aki["chapter"]
    assert top_aki["score"] > 0.3


def test_specialty_filtering(temp_knowledge_db):
    seed_harrison_knowledge(temp_knowledge_db)
    
    # Test valid filter
    results = temp_knowledge_db.search_knowledge_chunks("chest pain", specialty="INTERNAL_MEDICINE", top_k=3)
    for r in results:
        assert r["specialty"] == "INTERNAL_MEDICINE"

    # Test non-matching filter
    empty_results = temp_knowledge_db.search_knowledge_chunks("chest pain", specialty="PEDIATRICS", top_k=3)
    assert len(empty_results) == 0


def test_knowledge_api_endpoints():
    client = TestClient(app)

    # Seed endpoint
    r_seed = client.post("/api/knowledge/seed")
    assert r_seed.status_code == 200
    seed_data = r_seed.json()
    assert seed_data["status"] == "success"

    # Search endpoint
    r_search = client.get("/api/knowledge/search?q=Acute+Coronary+Syndrome&top_k=2")
    assert r_search.status_code == 200
    search_data = r_search.json()
    assert search_data["count"] > 0
    assert len(search_data["results"]) <= 2
    assert "score" in search_data["results"][0]
