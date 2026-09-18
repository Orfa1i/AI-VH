"""
Unit and regression tests for Dr. Marcus Vance clinical intent routing.
Verifies conversational greeting handling without over-medicalization,
suppression of chain-of-thought leakage, and accurate clinical activation.
"""

import pytest
from backend.clinical.intent import is_clinical_query, clean_doctor_dialogue_text
from backend.llm.medgemma_service import MedGemmaService


@pytest.fixture
def service():
    return MedGemmaService(enable_gpu=False)


def test_intent_classification_greetings_and_chatter():
    """Verifies that greetings and non-clinical chatter are classified as non-clinical."""
    greetings = [
        "hi",
        "hi!",
        "hello",
        "hello doctor",
        "hey there",
        "good morning Dr. Vance",
        "how are you today?",
        "who are you?",
        "what is your role?",
        "thanks doctor",
        "مرحبا",
        "السلام عليكم",
        "صباح الخير دكتور",
    ]
    for g in greetings:
        assert is_clinical_query(g) is False, f"Failed for greeting: '{g}'"


def test_intent_classification_clinical_inquiries():
    """Verifies that clinical queries containing symptoms, labs, or cases are classified as clinical."""
    clinical_queries = [
        "62yo male with acute substernal chest pressure and troponin 1.8",
        "Patient with severe abdominal pain and persistent vomiting",
        "What is your differential diagnosis for acute shortness of breath?",
        "How do you manage hyperkalemia with peaked T waves on ECG?",
        "DKA with anion gap 28 and blood glucose 450",
        "Oliguria and rising serum creatinine stage 3 AKI",
        "ألم شديد في الصدر وضيق تنفس",
    ]
    for q in clinical_queries:
        assert is_clinical_query(q) is True, f"Failed for clinical query: '{q}'"


def test_clean_doctor_dialogue_cot_leakage_removal():
    """Verifies that numbered chain-of-thought meta-reasoning steps are stripped."""
    leaked_cot = (
        "1.  **Identify the core clinical problem:** Acute chest pain with diaphoresis.\n"
        "2.  **Formulate a primary diagnosis:** The most likely diagnosis is NSTEMI.\n"
        "3.  **Consider the differential diagnosis:** What other conditions could present similarly?\n"
        "    *   STEMI: Must be ruled out immediately.\n"
        "    *   Aortic dissection: Severe tearing pain.\n\n"
        "Hello, Dr. Marcus Vance here. Based on this presentation, acute ischemic chest pain requires emergent intervention."
    )
    cleaned = clean_doctor_dialogue_text(leaked_cot)
    assert "1.  **Identify the core clinical problem:**" not in cleaned
    assert "2.  **Formulate a primary diagnosis:**" not in cleaned
    assert "Dr. Marcus Vance here" in cleaned


def test_greeting_response_no_over_medicalization(service):
    """
    Verifies that sending 'hi' does NOT produce 'Undifferentiated Acute Medical Presentation',
    does NOT prescribe IV access, and does NOT attach medical textbook citations.
    """
    response = service.generate_doctor_chat_response(
        messages=[{"role": "user", "content": "hi"}],
        rag_context=[{"chapter": "Haemophilus Infections", "text": "Random citation"}]
    )

    assert response["doctor"] == "Dr. Marcus Vance, MD, FACP"
    assert "Dr. Marcus Vance" in response["reply"]
    # No diagnostic UI cards or over-medicalization
    assert response["differential"] == []
    assert response["immediate_workup"] == []
    assert response["guideline_therapy"] == []
    assert response["contraindications"] == []
    assert response["citations"] == []
    assert "IV access" not in response["reply"]
    assert "Undifferentiated" not in response["reply"]


def test_clinical_query_response_generates_full_protocol(service):
    """Verifies that sending a clinical case triggers differential, workup, and citations."""
    response = service.generate_doctor_chat_response(
        messages=[{"role": "user", "content": "62yo male with acute substernal chest pressure radiating to arm, diaphoresis, and elevated Troponin-I"}],
        rag_context=[{
            "chapter": "Harrison's Principles of Internal Medicine - Chapter 273: Non-ST-Segment Elevation Acute Coronary Syndromes",
            "page": 1942,
            "text": "Dual antiplatelet therapy with aspirin and P2Y12 inhibitor indicated."
        }]
    )

    assert response["doctor"] == "Dr. Marcus Vance, MD, FACP"
    assert len(response["differential"]) >= 1
    assert len(response["immediate_workup"]) >= 1
    assert len(response["guideline_therapy"]) >= 1
    assert len(response["contraindications"]) >= 1
    assert len(response["citations"]) >= 1
    assert any("Aspirin" in t for t in response["guideline_therapy"])
