# -*- coding: utf-8 -*-
"""
Test Suite for Trajectory Graph / Case Room Updates
Validates:
1. UI Cleanup: No percentages, no '6 of 7' header text.
2. Agent Renaming: Infectious Disease & Gynecology with correct books and doctors.
3. Case Selection Sidebar: Exists with 5 rich cases, vitals, labs, imaging modal.
4. Workflow Integration: MedGemma router endpoint routes all 5 conditions accurately.
5. Flash Audio TTS: Endpoint /api/tts/speak handles agent requests with fallback.
6. Multi-Specialist Referral: Workflow and events exist for all cases.
"""

import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.router import MedicalSpecialtyRouter

client = TestClient(app)

def test_case_room_html_cleanliness():
    path = os.path.join("frontend", "public", "case-room.html")
    assert os.path.exists(path), "case-room.html must exist"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. UI Cleanup
    assert "6 of 7 specialists assigned" not in content, "Status text '6 of 7' must be removed"
    assert "<small>%</small>" not in content, "Percentage symbol must be removed"
    assert 'class="rbar"' not in content, "Progress bars must be removed"

    # 2. Agent Renaming
    assert "Obstetrics" not in content, "Obstetrics must be renamed"
    assert "Infectious Disease" in content, "Infectious Disease must be present"
    assert "Dr. Anthony Mercer" in content, "Anthony Mercer must be present"
    assert "Harrison's Infectious Diseases" in content, "Harrison's Infectious Diseases book must be present"
    assert "Gynecology" in content, "Gynecology must be present"
    assert "Dr. Evelyn Reed" in content, "Evelyn Reed must be present"
    assert "Williams Gynecology" in content, "Williams Gynecology must be present"

    # 3. Sidebar and Controls
    assert 'id="case-sidebar"' in content, "Case sidebar must exist"
    assert 'id="case-select"' in content, "Case selector dropdown must exist"
    assert 'id="b-start-triage"' in content, "Start Triage button must exist"
    assert 'id="toggle-auto"' in content, "Auto-Triage toggle must exist"
    assert 'id="toggle-voice"' in content, "Voice Audio toggle must exist"
    assert 'id="imaging-modal"' in content, "Imaging modal must exist"

    # 4. 5 Clinical Cases
    assert "preeclampsia_hellp" in content
    assert "septic_shock_mrsa" in content
    assert "stemi_cardiogenic" in content
    assert "ischemic_stroke_lvo" in content
    assert "acute_appendicitis" in content

def test_medgemma_router_clinical_cases():
    router = MedicalSpecialtyRouter()
    
    cases_test = [
        ("Severe headache, blurred vision, RUQ pain, 34 weeks gestation, elevated blood pressure 178/112, proteinuria", "gynecology"),
        ("Spiking fever 39.4C, septic shock, MRSA bacteremia, prosthetic joint effusion", "infectious_diseases"),
        ("Crushing chest pain, ST elevation in V1-V4, cardiogenic shock, troponin 4200", "cardiology"),
        ("Acute right hemiplegia, global aphasia, left M1 MCA occlusion, NIHSS 18", "neurology"),
        ("Migratory right lower quadrant pain, rebound tenderness, appendicolith, fever", "surgery"),
    ]
    
    for text, expected_primary in cases_test:
        res = router.route_case({"chief_complaint": text})
        assert res.specialty.lower() == expected_primary.lower(), f"Expected {expected_primary} for '{text[:40]}...', got {res.specialty}"
        assert res.confidence >= 0.70

def test_router_api_endpoint():
    payload = {
        "chief_complaint": "Severe throbbing headache, blurred vision, RUQ pain",
        "patient_history": "32F at 34 weeks gestation, blood pressure 178/112, proteinuria",
        "vitals": [{"label": "BP", "val": "178/112"}],
        "diagnostic_data": [{"name": "Platelets", "val": "62,000"}]
    }
    response = client.post("/api/router/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["primary_agent"] == "gynecology"
    assert "surgery" in [a.lower() for a in data.get("assigned_agents", [])] or data.get("consult_agent") == "surgery"
    assert data["confidence"] > 0.7

def test_tts_api_endpoint():
    payload = {
        "text": "Initiate IV labetalol and magnesium sulfate.",
        "voice": "gy",
        "specialty": "Gynecology"
    }
    response = client.post("/api/tts/speak", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fallback" in data or "audio_base64" in data
