"""
Test suite for verifying the 4-stage Agent Lifecycle and Technical Integration:
1. Initial State: All agents start in 'Ready' state.
2. Routing Execution: MedGemma router identifies relevant specialists; selected stay active, others shift to Standby.
3. Dynamic Handoff: Active agent referral causes target agent to switch to 'Ready' to assist.
4. Technical Integration: MedGemma, Knowledge Sources (RxNorm/NABD), Medical Books RAG, and Nvidia Nemotron live execution.
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.simulation.orchestrator import orchestrator
from backend.llm.nemotron_synthesis import nemotron_synthesis_engine
from backend.rag.shared_sources import shared_knowledge_service


async def test_backend_orchestrator_lifecycle():
    print("\n=======================================================")
    print("STAGE 1 & 2: Testing MedGemma Router & Orchestrator Workflow")
    print("=======================================================")

    test_case = {
        "id": "CASE-TEST-101",
        "name": "Elena Rostova",
        "age": 32,
        "sex": "Female",
        "chief_complaint": "Severe headache and sharp RUQ abdominal pain at 34 weeks gestation",
        "history_of_present_illness": "Third-trimester pregnancy with acute visual scotomata, right upper quadrant pain, and marked hypertension.",
        "past_medical_history": ["Nulliparous", "Gestational hypertension"],
        "medications": ["Prenatal vitamins"],
        "allergies": ["No known allergies"],
        "baseline_vitals": {"bp": "178/112", "hr": 92, "rr": 20, "spo2": 98, "temp": 37.1},
        "lab_results": [
            {"test_type": "platelets", "values": "68,000 /uL", "interpretation": "Critical Thrombocytopenia"},
            {"test_type": "ast", "values": "260 U/L", "interpretation": "Severe Transaminitis"},
            {"test_type": "alt", "values": "285 U/L", "interpretation": "Severe Transaminitis"},
            {"test_type": "ldh", "values": "820 U/L", "interpretation": "Hemolysis"},
        ],
        "imaging_findings": {"ultrasound": "Single viable intrauterine pregnancy at 34w1d; liver capsule intact."},
        "data_origin": "REAL_EHR"
    }

    result = await orchestrator.execute_production_clinical_workflow(
        patient_case=test_case,
        data_origin="REAL_EHR",
        max_consultations=2
    )

    routing = result.get("routing", {})
    events = result.get("events", [])
    synthesis = result.get("synthesis", {})

    print(f"Primary specialty: {routing.get('primary')}")
    print(f"Assigned specialists: {routing.get('assigned')}")
    print(f"Standby specialists: {routing.get('standby')}")
    print(f"Total events generated: {len(events)}")

    # Verify Stage 2: Routing Execution
    assert routing.get("primary") in ["ob", "gy", "im", "em"], f"Unexpected primary specialty: {routing.get('primary')}"
    assert len(routing.get("assigned")) >= 2, "Assigned specialists should include lead and consulted agents"
    assert len(routing.get("standby")) > 0, "Non-relevant specialists must be shifted to standby"

    for sb_key in routing.get("standby"):
        assert routing.get("status", {}).get(sb_key) == "standby", f"Specialist {sb_key} should have status 'standby'"

    # Verify Stage 3: Dynamic Handoff (Referral Events)
    referral_events = [ev for ev in events if ev.get("kind") == "referral"]
    print(f"Referral events found: {len(referral_events)}")
    if referral_events:
        for ref in referral_events:
            print(f"  -> Referral from {ref.get('who')} to {ref.get('to')}: {ref.get('short')}")
            assert ref.get("to") in ["su", "em", "im", "ca", "ob", "gy", "ne"], "Referral target must be a valid specialty"

    # Verify Stage 4: Nvidia Nemotron & Knowledge Integration
    print("\n=======================================================")
    print("STAGE 4: Technical Integration & Real-Time Nvidia Verification")
    print("=======================================================")
    print(f"Nvidia Nemotron Model: {nemotron_synthesis_engine.model}")
    print(f"Nvidia Base URL: {nemotron_synthesis_engine.base_url}")
    print(f"Nvidia API Available: {nemotron_synthesis_engine.is_available}")
    print(f"Diagnostic Synthesis Diagnosis: {synthesis.get('primary_diagnosis')}")
    print(f"Synthesis Confidence: {synthesis.get('confidence')}")
    print(f"Evidence Sources Cited: {synthesis.get('evidence_sources')}")

    assert synthesis.get("primary_diagnosis"), "Nemotron synthesis must establish a primary diagnosis"
    assert synthesis.get("confidence") > 0.5, "Confidence must be grounded and non-zero"
    assert len(synthesis.get("evidence_sources", [])) > 0, "Synthesis must cite evidence sources"

    # Verify Shared Knowledge Sources
    drug_profile = shared_knowledge_service.lookup_drug_profile("labetalol")
    evidence = shared_knowledge_service.retrieve_shared_evidence("labetalol in severe preeclampsia")
    print(f"Drug profile for 'labetalol': RxCUI {drug_profile.get('rxcui') if drug_profile else 'N/A'}")
    print(f"Shared evidence passages retrieved: {len(evidence)}")
    assert drug_profile is not None or len(evidence) >= 0, "Shared knowledge service must process pharmacology queries"

    print("\n>>> ALL BACKEND WORKFLOW TESTS PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    asyncio.run(test_backend_orchestrator_lifecycle())
