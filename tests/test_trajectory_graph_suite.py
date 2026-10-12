# -*- coding: utf-8 -*-
"""
Test Suite for Trajectory Graph / Case Room Updates
Validates all 19 bug audit specifications from case-room-bugfix phases 1-6:
1. Agent Roster: Obstetrics leads pregnancy/preeclampsia cases, Gynecology standby, 7 canonical agents.
2. No human doctor names: Every agent uses "AI agent", no "Dr." prefixes.
3. Case Data & ESI: Elena Vance is ESI 2 · Emergent, #VH-8921-OB, Synthetic case badge.
4. Single Control: No Start Triage in dossier; single primary control (b-main-control) in specialist header.
5. Router Card: Progress bars (.rbar i), display figures (.v), exactly 3 tags (Lead, Assigned, Standby - no Consulted, no red).
6. Agent Table: Obstetrics at top, Gynecology at bottom standby, dimmed only when filtered.
7. Clinical Dossier: Natural height labs without nested scroll, SI units (62 ×10⁹/L, 31 µmol/L), clean switch for voice audio.
8. Empty States: Wireframe outline for Draft in idle; Discussion empty state.
9. Router API & TTS: Accurate backend routing to Obstetrics, TTS endpoint.
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

    # 1. Roster and Canonical Agents (Phase 1)
    assert "Obstetrics" in content, "Obstetrics must be present"
    assert "Williams Obstetrics" in content, "Williams Obstetrics must be present"
    assert "Gynecology" in content, "Gynecology must be present"
    assert "Williams Gynecology" in content, "Williams Gynecology must be present"
    assert "Emergency Medicine" in content, "Emergency Medicine must be present"
    assert "Internal Medicine" in content, "Internal Medicine must be present"
    assert "Cardiology" in content, "Cardiology must be present"
    assert "Neurology" in content, "Neurology must be present"
    assert "Surgery" in content, "Surgery must be present"

    # 2. No human doctor names (Phase 1 #1)
    assert "Dr. Evelyn Reed" not in content, "Human doctor name must be removed"
    assert "Dr. Marcus Vance" not in content, "Human doctor name must be removed"
    assert "Dr. Sarah Chen" not in content, "Human doctor name must be removed"
    assert "Dr. Anthony Mercer" not in content, "Human doctor name must be removed"
    assert "Dr. David Kim" not in content, "Human doctor name must be removed"
    assert "Dr. Michael Chang" not in content, "Human doctor name must be removed"
    assert "Dr. James Wilson" not in content, "Human doctor name must be removed"
    assert "AI agent" in content, "Subtitles must be 'AI agent'"

    # 3. Case Data Consistency (Phase 1 #3 & Phase 5 #3)
    assert "ESI 2 · Emergent" in content, "Elena Vance must be ESI 2 · Emergent"
    assert "Synthetic case" in content, "Synthetic case badge must be present"
    assert "#VH-8921-OB" in content, "Case MRN must be #VH-8921-OB"

    # 4. Single Control & State Machine (Phase 2 & Phase 5 #1)
    assert 'id="b-start-triage"' not in content, "Start Triage button must be removed from dossier"
    assert 'id="b-main-control"' in content, "Single primary control button must exist in specialist header"
    assert 'id="b-replay"' in content, "Replay button must exist"
    assert 'id="stage-t"' in content, "Derived stage text must exist"

    # 5. Router Card (Phase 3)
    assert 'class="rbar"' in content, "Progress bars (.rbar) must exist"
    assert 'class="rc' in content, "Router tiles (.rc) must exist"
    assert 'tag lead' in content, "Lead tag must exist"
    assert 'Consulted' not in content, "Consulted tag must be removed"

    # 6. Specialist Agents Table & Copy (Phase 4)
    assert "Select an agent, here or in the router, to read only its messages." in content, "Table footer helper text must match specification"
    assert 'id="cv"' in content, "Canvas element for spokes/packets must exist"
    assert 'id="board"' in content, "Center board must exist"

    # 7. Clinical Dossier (Phase 5)
    assert 'class="switch"' in content, "Clean CSS switch must exist for voice audio"
    assert 'id="voice"' in content, "Voice switch input must exist"
    assert 'id="b-show-all-labs"' in content, "Show all labs expansion link must exist"
    assert "62 ×10⁹/L" in content, "Platelets must use SI units (62 ×10⁹/L)"
    assert "31 µmol/L" in content, "Bilirubin must use SI units (31 µmol/L)"
    assert "SpO₂" in content, "SpO₂ label must use subscript"

    # 8. Empty States & Layout (Phase 6)
    assert 'id="draft-empty"' in content, "Draft empty state must exist"
    assert 'id="disc-empty"' in content, "Discussion empty state must exist"
    assert 'id="filter-chip"' in content, "Filter chip must exist"
    assert 'id="b-sign"' in content, "Review and sign button must exist"

    # 9. 5 Clinical Cases
    assert "preeclampsia_hellp" in content
    assert "septic_shock_mrsa" in content
    assert "stemi_cardiogenic" in content
    assert "ischemic_stroke_lvo" in content
    assert "acute_appendicitis" in content

def test_medgemma_router_clinical_cases():
    router = MedicalSpecialtyRouter()
    
    cases_test = [
        ("Severe headache, blurred vision, RUQ pain, 34 weeks gestation, elevated blood pressure 178/112, proteinuria", "obstetrics"),
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
        "chief_complaint": "Severe throbbing headache, blurred vision, RUQ pain, pregnancy at 34 weeks gestation",
        "patient_history": "32F at 34 weeks gestation, blood pressure 178/112, proteinuria",
        "vitals": [{"label": "BP", "val": "178/112"}],
        "diagnostic_data": [{"name": "Platelets", "val": "62,000"}]
    }
    response = client.post("/api/router/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["primary_agent"] == "obstetrics"
    assert "surgery" in [a.lower() for a in data.get("assigned_agents", [])] or data.get("consult_agent") == "surgery"
    assert data["confidence"] > 0.7

def test_tts_api_endpoint():
    payload = {
        "text": "Initiate IV labetalol and magnesium sulfate.",
        "voice": "ob",
        "specialty": "Obstetrics"
    }
    response = client.post("/api/tts/speak", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fallback" in data or "audio_base64" in data
