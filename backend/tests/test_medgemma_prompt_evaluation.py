"""
Unit tests for MedGemma clinical evaluation prompt & JSON schema parsing.
Verifies strict JSON output parsing, thought-tag stripping, differential extraction,
and backward-compatible fallbacks.
"""

import json
import pytest
from backend.llm.medgemma_service import MedGemmaService


@pytest.fixture
def service():
    # Instantiate service without GPU requirement for fast unit testing
    return MedGemmaService(enable_gpu=False)


def test_build_evaluation_prompt_structure(service):
    """Verifies that the prompt contains all required sections and strict constraints."""
    prompt = service._build_evaluation_prompt(
        chief_complaint="Severe central chest tightness radiating to left shoulder",
        hpi="62-year-old male with progressive angina over 3 hours",
        vitals_summary="BP 148/92, HR 102, SpO2 96%, RR 20, Temp 37.1C",
        exam_findings={"heart": "S4 gallop present, no murmur", "lungs": "Clear to auscultation"},
        lab_results=[
            {"test_type": "High-Sensitivity Troponin I", "values": "450 ng/L (ref < 14)"},
            {"test_type": "12-Lead ECG", "values": "ST depressions in leads II, III, aVF"}
        ],
        rag_context=[
            {"chapter": "Chapter 273: Acute Coronary Syndromes", "page": 1952, "text": "Immediate aspirin and anticoagulant therapy indicated."}
        ]
    )

    assert "You are an expert Internal Medicine Physician (MedGemma)" in prompt
    assert "### INPUTS" in prompt
    assert "1. Patient Data:" in prompt
    assert "2. Medical Reference (Harrison's):" in prompt
    assert "### STRICT INSTRUCTIONS" in prompt
    assert "DO NOT output any internal thought processes" in prompt
    assert "NO HALLUCINATIONS" in prompt
    assert "PRIMARY DIAGNOSIS: This must be a specific medical disease or condition" in prompt
    assert "### OUTPUT FORMAT" in prompt
    assert '"primary_diagnosis"' in prompt
    assert '"confidence_score"' in prompt
    assert '"differential_diagnoses"' in prompt
    assert '"treatment_regimen"' in prompt
    assert "Severe central chest tightness" in prompt
    assert "Chapter 273: Acute Coronary Syndromes" in prompt


def test_parse_strict_json_output(service):
    """Verifies that clean JSON matching the schema is parsed accurately."""
    raw_json = json.dumps({
        "primary_diagnosis": "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)",
        "confidence_score": "92%",
        "differential_diagnoses": [
            "Acute Coronary Syndrome / NSTEMI",
            "Unstable Angina",
            "Acute Myopericarditis"
        ],
        "treatment_regimen": [
            "Aspirin 325 mg PO chewable stat",
            "Ticagrelor 180 mg PO loading dose",
            "Unfractionated heparin IV bolus and titration",
            "Urgent cardiology consult for coronary angiography"
        ]
    })

    parsed = service._parse_llm_text_to_structured_output(raw_json)

    assert parsed["primary_diagnosis"] == "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)"
    assert parsed["confidence_score"] == "92%"
    assert len(parsed["differential_diagnoses"]) == 3
    assert parsed["differential_diagnoses"][0] == "Acute Coronary Syndrome / NSTEMI"
    assert len(parsed["treatment_plan"]) == 4
    assert parsed["treatment_plan"][0] == "Aspirin 325 mg PO chewable stat"
    assert parsed["treatment_regimen"] == parsed["treatment_plan"]


def test_parse_json_with_leaked_thought_tags(service):
    """Verifies that model thought tags (e.g., <unused94>thought) are stripped and JSON is still parsed."""
    raw_text = (
        "<unused94>thought\n"
        "Patient has substernal chest discomfort and elevated troponin.\n"
        "Harrison Chapter 273 emphasizes antiplatelet therapy.\n"
        "</thought>\n"
        "{\n"
        '  "primary_diagnosis": "Acute Coronary Syndrome (NSTEMI)",\n'
        '  "confidence_score": "88%",\n'
        '  "differential_diagnoses": ["NSTEMI", "Aortic Dissection", "Pulmonary Embolism"],\n'
        '  "treatment_regimen": ["Aspirin 325mg PO", "Heparin IV", "Continuous telemetry"]\n'
        "}"
    )

    parsed = service._parse_llm_text_to_structured_output(raw_text)

    assert parsed["primary_diagnosis"] == "Acute Coronary Syndrome (NSTEMI)"
    assert parsed["confidence_score"] == "88%"
    assert len(parsed["differential_diagnoses"]) == 3
    assert len(parsed["treatment_plan"]) == 3
    assert "<unused94>" not in parsed["clinical_reasoning"]


def test_parse_fallback_prose_phrasing(service):
    """Verifies that prose phrasing is gracefully handled if the model outputs markdown instead of JSON."""
    prose_text = (
        "Based on the clinical presentation and Harrison's reference, there is "
        "high clinical suspicion for acute pulmonary embolism (PE) based on sudden onset dyspnea.\n\n"
        "Treatment Plan:\n"
        "- Supplemental oxygen to keep SpO2 > 94%\n"
        "- Therapeutic anticoagulation with LMWH or unfractionated heparin\n"
        "- CT pulmonary angiography"
    )

    parsed = service._parse_llm_text_to_structured_output(prose_text)

    assert "pulmonary embolism" in parsed["primary_diagnosis"].lower()
    assert len(parsed["treatment_plan"]) >= 2
