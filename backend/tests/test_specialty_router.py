"""
Tests for MedicalSpecialtyRouter, CardiologySpecialistAgent, and Braunwald RAG (Phase 2).
"""

import pytest
from backend.agents.router import MedicalSpecialtyRouter, RoutingDecision
from backend.rag.specialists.cardiology_rag import CardiologyRAGAgent


def test_specialty_router_cardiology_triage():
    """Verify router directs acute coronary presentation to Cardiology."""
    cardio_case = {
        "chief_complaint": "Acute substernal crushing chest pressure radiating to left arm and jaw",
        "history_of_present_illness": "62-year-old male with 2 hours of diaphoresis, dyspnea, and ischemic chest pain.",
        "past_medical_history": ["Coronary Artery Disease", "Hypertension"],
    }

    decision: RoutingDecision = MedicalSpecialtyRouter.route_case(cardio_case)

    assert decision.specialty == "CARDIOLOGY"
    assert "Rachel Vance" in decision.suggested_specialist_name
    assert "Braunwald" in decision.target_medical_book
    assert decision.confidence >= 0.75
    assert any("chest pain" in k or "angina" in k or "substernal" in k for k in decision.matched_keywords)


def test_specialty_router_internal_medicine_triage():
    """Verify router directs diabetic ketoacidosis and systemic symptoms to Internal Medicine."""
    im_case = {
        "chief_complaint": "High fever, productive purulent cough, and right-sided pleuritic chest discomfort",
        "history_of_present_illness": "Elderly female with 3 days of shaking chills and rust-colored sputum.",
        "past_medical_history": ["Type 2 Diabetes Mellitus", "COPD"],
    }

    decision: RoutingDecision = MedicalSpecialtyRouter.route_case(im_case)

    assert decision.specialty == "INTERNAL_MEDICINE"
    assert "Marcus Vance" in decision.suggested_specialist_name
    assert "Harrison" in decision.target_medical_book
    assert decision.confidence >= 0.75


def test_braunwald_rag_retrieval():
    """Verify Cardiology RAG agent retrieves evidence from Braunwald's Heart Disease."""
    rag_agent = CardiologyRAGAgent()

    # Query cardiovascular knowledge
    evidence = rag_agent.retrieve_evidence("Acute myocardial infarction troponin elevation and early anticoagulation", top_k=2)

    assert len(evidence) > 0
    assert evidence[0]["book"] == "Braunwald's Heart Disease"
    assert evidence[0]["specialty"] == "Cardiology"
    assert "chapter" in evidence[0]
    assert len(evidence[0]["text"]) > 0


def test_cardiology_evidence_brief_generation():
    """Verify Cardiology RAG agent constructs structured evidence briefs."""
    rag_agent = CardiologyRAGAgent()
    brief = rag_agent.generate_evidence_brief(
        chief_complaint="Substernal chest pain radiating to left shoulder",
        hpi="Elevated troponin on initial assessment",
    )

    assert brief.domain == "Cardiovascular Medicine"
    assert len(brief.citations) > 0
    assert len(brief.recommended_workup) > 0
    assert len(brief.recommended_therapy) > 0
