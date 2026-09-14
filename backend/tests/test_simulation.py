"""
Automated Test Suite for AI Virtual Hospital Backend
Tests event bus, Harrison RAG semantic index, agents, and clinical simulation loop.
"""

import pytest
import asyncio
from backend.simulation.events import HospitalEvent, EventType
from backend.simulation.event_bus import HospitalEventBus
from backend.clinical.cases import get_benchmark_case
from backend.clinical.tools import ClinicalToolkit
from backend.rag.vector_index import MedicalKnowledgeIndex
from backend.simulation.orchestrator import HospitalOrchestrator


def test_rag_semantic_search():
    sample_chunks = [
        {
            "id": "CHUNK_1",
            "topic": "Chest Discomfort & Angina",
            "chapter": "Cardiology",
            "page": 115,
            "text": "Angina pectoris presents with retrosternal pressure radiating to the left shoulder, diaphoresis, and relief with sublingual nitroglycerin.",
        },
        {
            "id": "CHUNK_2",
            "topic": "Diabetic Ketoacidosis",
            "chapter": "Endocrinology",
            "page": 2840,
            "text": "DKA is characterized by hyperglycemia, metabolic acidosis with elevated anion gap, Kussmaul respirations, and ketonuria.",
        }
    ]
    index = MedicalKnowledgeIndex(sample_chunks)
    results = index.search("retrosternal pressure diaphoresis left shoulder", top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "CHUNK_1"
    assert results[0]["relevance_score"] > 0


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = HospitalEventBus()
    received = []

    async def listener(evt: HospitalEvent):
        received.append(evt)

    bus.subscribe(EventType.PATIENT_ARRIVED, listener)

    event = HospitalEvent(
        id="EVT-TEST",
        event_type=EventType.PATIENT_ARRIVED,
        encounter_id="ENC-TEST",
        patient_id="PAT-TEST",
        sender_agent_id="agent_1",
        summary="Test arrival"
    )
    await bus.publish(event)
    await asyncio.sleep(0.02)

    assert len(received) == 1
    assert received[0].summary == "Test arrival"


@pytest.mark.asyncio
async def test_clinical_simulation_end_to_end():
    orch = HospitalOrchestrator(enable_gpu=False)
    result = await orch.run_encounter_simulation("CASE-101")

    assert result["encounter_id"].startswith("ENC-")
    assert result["primary_diagnosis"] == "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)"
    assert result["confidence"] > 0.8
    assert result["report_id"].startswith("REP-")
    assert result["events_count"] >= 15

    # Test submitting physician review
    review = orch.submit_physician_review(
        report_id=result["report_id"],
        physician_name="Dr. Sarah Attending, MD",
        diagnosis_grade="CORRECT",
        reasoning_grade="SOUND",
        tests_grade="APPROPRIATE",
        treatment_grade="SAFE_AND_OPTIMAL",
        overall_score=5,
        approved=True,
        notes="Accurate diagnosis and guideline-directed medical therapy.",
    )
    assert review.approved is True
    assert review.overall_score == 5
