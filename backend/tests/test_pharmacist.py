"""
Unit and Integration Tests for Clinical Pharmacist Agent (Phase 7)
Verifies medication reconciliation, allergy cross-matching, renal dose adjustments,
and REST endpoint functionality.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.pharmacist import PharmacistAgent
from backend.clinical.cases import get_benchmark_case, BENCHMARK_CASES
from backend.clinical.models import MedicationSafetyReport


@pytest.mark.asyncio
async def test_pharmacist_clears_safe_medications():
    pharmacist = PharmacistAgent()
    case = get_benchmark_case("CASE-101")  # Robert Miller: NSTEMI, allergy to penicillin
    safe_prescriptions = [
        "Aspirin 325mg chewable STAT",
        "Sublingual Nitroglycerin 0.4mg",
        "Ticagrelor 90mg BID",
        "Atorvastatin 80mg daily"
    ]
    report: MedicationSafetyReport = await pharmacist.review_medication_order(
        encounter_id="ENC-TEST-SAFE",
        prescriptions=safe_prescriptions,
        patient=case,
        diagnosis="Non-ST-Elevation Myocardial Infarction",
    )
    assert report.safety_cleared is True
    assert report.dispensing_status == "READY_FOR_ADMINISTRATION"
    assert len(report.approved_medications) == 4
    assert len(report.flagged_contraindications) == 0


@pytest.mark.asyncio
async def test_pharmacist_catches_allergy():
    pharmacist = PharmacistAgent()
    case = get_benchmark_case("CASE-101")  # Allergy: Penicillin (hives)
    prescriptions = [
        "Aspirin 325mg",
        "Amoxicillin / Clavulanate 875mg PO BID"  # Penicillin derivative
    ]
    report = await pharmacist.review_medication_order(
        encounter_id="ENC-TEST-ALLERGY",
        prescriptions=prescriptions,
        patient=case,
        diagnosis="Bacterial Infection",
    )
    # Robert Miller is allergic to Penicillin
    assert report.safety_cleared is False
    assert report.dispensing_status == "HOLD_FOR_PHYSICIAN_CLARIFICATION"
    assert any("ALLERGY ALERT" in flag for flag in report.flagged_contraindications)


@pytest.mark.asyncio
async def test_pharmacist_catches_contraindicated_treatment():
    pharmacist = PharmacistAgent()
    case = get_benchmark_case("CASE-101")  # Contraindicated: NSAIDs other than Aspirin
    prescriptions = [
        "Aspirin 325mg",
        "Ibuprofen 600mg TID"
    ]
    report = await pharmacist.review_medication_order(
        encounter_id="ENC-TEST-CONTRA",
        prescriptions=prescriptions,
        patient=case,
        diagnosis="Acute Coronary Syndrome",
    )
    assert report.safety_cleared is False
    assert any("CONTRAINDICATION" in flag for flag in report.flagged_contraindications)


@pytest.mark.asyncio
async def test_pharmacist_renal_dosing_adjustment():
    pharmacist = PharmacistAgent()
    case = get_benchmark_case("CASE-102")  # Severe sepsis / AKI with elevated creatinine
    prescriptions = [
        "Enoxaparin 1 mg/kg Q12H subcutaneous",
        "Ketorolac 30mg IV STAT"
    ]
    report = await pharmacist.review_medication_order(
        encounter_id="ENC-TEST-RENAL",
        prescriptions=prescriptions,
        patient=case,
        diagnosis="Acute Kidney Injury / Sepsis",
    )
    # Ketorolac is an NSAID and should be flagged for nephrotoxicity
    assert any("NEPHROTOXICITY RISK" in flag for flag in report.flagged_contraindications)
    assert any("RENAL DOSE ADJUSTMENT" in adj for adj in report.renal_adjustments)


def test_api_pharmacy_review_endpoint():
    client = TestClient(app)
    response = client.post(
        "/api/pharmacy/review",
        json={
            "prescriptions": ["Aspirin 325mg", "Atorvastatin 80mg"],
            "patient_id": "CASE-101",
            "diagnosis": "Acute Myocardial Infarction"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pharmacist_name"] == "Dr. Elena Rostova, PharmD, BCPS"
    assert data["safety_cleared"] is True
    assert "Aspirin 325mg" in data["approved_medications"]
