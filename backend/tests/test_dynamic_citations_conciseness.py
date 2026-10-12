import pytest
import pytest_asyncio
from backend.simulation.orchestrator import HospitalOrchestrator
from backend.clinical.cases import PatientGroundTruth


@pytest.mark.asyncio
async def test_dynamic_citations_cardiology():
    """Verify that a cardiology patient case dynamically cites Braunwald's Heart Disease."""
    orch = HospitalOrchestrator(enable_gpu=False)
    
    cardio_patient = {
        "id": "TEST-CARDIO-01",
        "name": "David Miller",
        "age": 64,
        "sex": "Male",
        "chief_complaint": "Severe substernal crushing chest pain with radiation to left arm and diaphoresis",
        "hpi": "64yo male presents with 2 hours of acute substernal chest pressure, NSTEMI suspected with elevated troponin.",
        "past_medical_history": ["Hypertension", "Dyslipidemia"],
        "medications": ["Amlodipine", "Atorvastatin"],
        "allergies": ["NKDA"],
        "vital_signs": {"hr": 92, "bp": "154/92", "rr": 20, "spo2": 96},
        "lab_results": [{"test_type": "High-Sensitivity Troponin I", "values": "2.45 ng/mL", "interpretation": "Elevated"}],
        "imaging_findings": {"12-Lead ECG": "ST depression in V4-V6"},
    }

    result = await orch.execute_production_clinical_workflow(cardio_patient, data_origin="REAL_EHR")
    report = result["report"]
    citations = report.get("medical_knowledge_citations", [])

    assert len(citations) > 0, "Report must contain medical knowledge citations"
    
    # Assert that citations dynamically cite Braunwald's Heart Disease and contain evidence text
    c0 = citations[0]
    assert "Braunwald" in c0["book"] or "Cardiovascular" in c0["book"], f"Expected Braunwald's Heart Disease, got {c0['book']}"
    assert len(c0.get("text", "") or c0.get("excerpt", "")) > 10, "Citation must contain verbatim evidence text snippet"
    assert c0.get("specialty") in ["Cardiology", "CARDIOLOGY"], f"Expected Cardiology specialty, got {c0.get('specialty')}"

    # Assert that report summary is concise (not excessive)
    summary = report.get("clinical_summary", "")
    assert len(summary) > 0, "Clinical summary must be populated"
    assert len(summary.split("\n\n")) <= 3, "Summary must be concise without excessive paragraphs"


@pytest.mark.asyncio
async def test_dynamic_citations_obstetrics():
    """Verify that an obstetrics patient case dynamically cites Williams Obstetrics."""
    orch = HospitalOrchestrator(enable_gpu=False)

    ob_patient = {
        "id": "TEST-OB-01",
        "name": "Maria Santos",
        "age": 28,
        "sex": "Female",
        "chief_complaint": "Severe persistent headache and blurred vision in 34-week pregnancy with severe hypertension",
        "hpi": "G1P0 at 34 weeks gestation presenting with severe features of preeclampsia, BP 172/112, proteinuria 3+.",
        "past_medical_history": ["Nulliparous"],
        "medications": ["Prenatal vitamins"],
        "allergies": ["NKDA"],
        "vital_signs": {"hr": 88, "bp": "172/112", "rr": 18, "spo2": 99},
        "lab_results": [
            {"test_type": "Urine Protein Dipstick", "values": "3+", "interpretation": "Severe proteinuria"},
            {"test_type": "Platelet Count", "values": "88,000 /uL", "interpretation": "Thrombocytopenia"}
        ],
        "imaging_findings": {"Bedside Obstetric Ultrasound": "Single active intrauterine pregnancy, cephalic"},
    }

    result = await orch.execute_production_clinical_workflow(ob_patient, data_origin="REAL_EHR")
    report = result["report"]
    citations = report.get("medical_knowledge_citations", [])

    assert len(citations) > 0, "Report must contain obstetrics citations"
    c0 = citations[0]
    assert "Williams" in c0["book"] or "Obstetrics" in c0["book"], f"Expected Williams Obstetrics, got {c0['book']}"
    assert len(c0.get("text", "") or c0.get("excerpt", "")) > 10, "Citation must contain verbatim evidence text snippet"
    assert c0.get("specialty") in ["Obstetrics", "OBSTETRICS"], f"Expected Obstetrics specialty, got {c0.get('specialty')}"
