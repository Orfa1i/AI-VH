"""
FastAPI REST & WebSocket API Router for AI-VH
Exposes endpoints for simulation control, clinical reports, physician review, and live event streaming.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json
import logging

from ..simulation.orchestrator import orchestrator
from ..simulation.event_bus import event_bus
from ..clinical.cases import BENCHMARK_CASES
from ..rl.evaluator import PolicyEvaluator

logger = logging.getLogger("APIRouter")
api_router = APIRouter(prefix="/api")


class SimulationRequest(BaseModel):
    case_id: str = "CASE-101"


class SpecialistConsultRequest(BaseModel):
    clinical_scenario: str
    abnormal_labs: Optional[List[str]] = None
    patient_id: Optional[str] = "PAT-CONSULT"


class PharmacyReviewRequest(BaseModel):
    prescriptions: List[str]
    patient_id: Optional[str] = "CASE-101"
    diagnosis: Optional[str] = "Acute Inpatient Admission"


class PhysicianReviewRequest(BaseModel):
    report_id: str
    physician_name: str = "Dr. Attending Physician, MD"
    diagnosis_grade: str
    reasoning_grade: str
    tests_grade: str
    treatment_grade: str
    overall_score: int
    approved: bool
    notes: str
    corrected_diagnosis: Optional[str] = None
    corrected_treatment: Optional[List[str]] = None


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Virtual Hospital Platform"}


@api_router.post("/specialists/internal-medicine/consult")
async def consult_internal_medicine(req: SpecialistConsultRequest):
    """Consult Dr. Marcus Vance, MD (Internal Medicine) powered by Harrison's RAG."""
    try:
        result = await orchestrator.conduct_specialist_consult(
            clinical_scenario=req.clinical_scenario,
            abnormal_labs=req.abnormal_labs,
            patient_id=req.patient_id or "PAT-CONSULT",
        )
        return result
    except Exception as e:
        logger.error(f"Specialist consult error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/pharmacy/review")
async def review_medications_pharmacy(req: PharmacyReviewRequest):
    """Reconciles medication orders with Dr. Elena Rostova, PharmD."""
    try:
        result = await orchestrator.review_medication_orders(
            prescriptions=req.prescriptions,
            patient_id=req.patient_id or "CASE-101",
            diagnosis=req.diagnosis or "Acute Inpatient Admission",
        )
        return result
    except Exception as e:
        logger.error(f"Pharmacy review error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/cases")
async def list_cases():
    return [
        {
            "id": c.id,
            "name": c.name,
            "age": c.age,
            "sex": c.sex,
            "chief_complaint": c.chief_complaint,
            "acuity": c.triage_acuity.value,
        }
        for c in BENCHMARK_CASES
    ]


@api_router.post("/simulation/run")
async def run_simulation(req: SimulationRequest):
    try:
        result = await orchestrator.run_encounter_simulation(req.case_id)
        return result
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/simulation/events")
async def get_recent_events(limit: int = 50):
    events = event_bus.get_recent_events(limit)
    return [e.to_dict() for e in events]


@api_router.get("/reports")
async def get_reports():
    return orchestrator.get_all_reports()


@api_router.get("/reports/{report_id}")
async def get_report_detail(report_id: str):
    report = orchestrator.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@api_router.post("/reviews")
async def submit_review(req: PhysicianReviewRequest):
    try:
        review = orchestrator.submit_physician_review(
            report_id=req.report_id,
            physician_name=req.physician_name,
            diagnosis_grade=req.diagnosis_grade,
            reasoning_grade=req.reasoning_grade,
            tests_grade=req.tests_grade,
            treatment_grade=req.treatment_grade,
            overall_score=req.overall_score,
            approved=req.approved,
            notes=req.notes,
            corrected_diagnosis=req.corrected_diagnosis,
            corrected_treatment=req.corrected_treatment,
        )
        return review.model_dump()
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Review submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics")
async def get_analytics():
    return orchestrator.get_analytics()


@api_router.get("/rl/dataset")
async def get_rl_dpo_dataset(include_calibrations: bool = True):
    """Returns the compiled DPO preference dataset with clinical reward statistics."""
    try:
        return orchestrator.get_dpo_dataset(include_calibrations=include_calibrations)
    except Exception as e:
        logger.error(f"Error fetching DPO dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/rl/dataset/export")
async def export_rl_dpo_dataset(filepath: Optional[str] = "data/dpo_preference_dataset.jsonl"):
    """Compiles and exports the DPO preference dataset to a HuggingFace-compatible JSONL file."""
    try:
        target_path = filepath or "data/dpo_preference_dataset.jsonl"
        return orchestrator.export_dpo_dataset(output_path=target_path)
    except Exception as e:
        logger.error(f"Error exporting DPO dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/rl/benchmark")
async def get_policy_benchmark_report():
    """
    Executes and returns comparative policy evaluation benchmark report:
    Base MedGemma (v0.1) vs Physician-Guided RL DPO-Aligned Agent (v0.3)
    across all clinical benchmark cases.
    """
    try:
        report = PolicyEvaluator.run_full_benchmark()
        return report.model_dump()
    except Exception as e:
        logger.error(f"Error running policy benchmark: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/rl/benchmark/cases/{case_id}")
async def get_case_policy_evaluation(case_id: str):
    """
    Returns comparative evaluation metrics for a specific clinical case.
    """
    case = next((c for c in BENCHMARK_CASES if c.id == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found in benchmark cases")
    try:
        comparison = PolicyEvaluator.evaluate_case(case)
        return comparison.model_dump()
    except Exception as e:
        logger.error(f"Error evaluating case {case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inpatient/rooms")
async def get_inpatient_rooms():
    """
    Returns telemetry and clinical monitoring status for the 4 inpatient rooms
    in the East Inpatient Wing.
    """
    rooms = [
        {
            "room_number": "101",
            "room_name": "Inpatient Suite 101 - Cardiac Telemetry",
            "patient_name": "Robert Miller",
            "age": 62,
            "sex": "Male",
            "diagnosis": "Acute NSTEMI (Post-Angiography)",
            "acuity": "URGENT",
            "heart_rate": 76,
            "systolic_bp": 128,
            "diastolic_bp": 82,
            "respiratory_rate": 16,
            "spo2": 98.0,
            "rhythm_strip": "Normal Sinus Rhythm with resolving ST depression",
            "active_infusion": "Unfractionated Heparin 18 units/kg/hr IV",
            "diet": "Cardiac / Low Sodium",
            "nurse_assigned": "Sarah Jenkins, RN",
            "status": "STABLE_MONITORED",
        },
        {
            "room_number": "102",
            "room_name": "Inpatient Suite 102 - Medical ICU Bed",
            "patient_name": "Elena Rostova",
            "age": 24,
            "sex": "Female",
            "diagnosis": "Diabetic Ketoacidosis (Closing Anion Gap)",
            "acuity": "EMERGENT",
            "heart_rate": 96,
            "systolic_bp": 110,
            "diastolic_bp": 70,
            "respiratory_rate": 20,
            "spo2": 99.0,
            "rhythm_strip": "Sinus Rhythm without ectopy",
            "active_infusion": "Regular Insulin 5 units/hr + D5W 0.45% NS with 20 mEq KCl",
            "diet": "NPO (strict)",
            "nurse_assigned": "Sarah Jenkins, RN",
            "status": "ACUTE_IMPROVING",
        },
        {
            "room_number": "103",
            "room_name": "Inpatient Suite 103 - Step-Down Bed",
            "patient_name": "Arthur Pendelton",
            "age": 68,
            "sex": "Male",
            "diagnosis": "Acute Kidney Injury Stage 3 (Resolving)",
            "acuity": "URGENT",
            "heart_rate": 80,
            "systolic_bp": 118,
            "diastolic_bp": 74,
            "respiratory_rate": 16,
            "spo2": 97.0,
            "rhythm_strip": "Sinus Rhythm with first-degree AV block",
            "active_infusion": "Plasmalyte @ 125 mL/hr IV Maintenance",
            "diet": "Renal Diet (Low Potassium / Phosphorus)",
            "nurse_assigned": "Sarah Jenkins, RN",
            "status": "DIURESIS_RECOVERY",
        },
        {
            "room_number": "104",
            "room_name": "Inpatient Suite 104 - Step-Down Bed",
            "patient_name": "Clara Vance",
            "age": 52,
            "sex": "Female",
            "diagnosis": "Submassive Pulmonary Embolism",
            "acuity": "EMERGENT",
            "heart_rate": 92,
            "systolic_bp": 116,
            "diastolic_bp": 76,
            "respiratory_rate": 20,
            "spo2": 96.0,
            "rhythm_strip": "Sinus Tachycardia with S1Q3T3 morphology",
            "active_infusion": "Enoxaparin 80 mg SC q12h + 2L Nasal Cannula O2",
            "diet": "Regular as tolerated",
            "nurse_assigned": "Sarah Jenkins, RN",
            "status": "STABLE_ANTICOAGULATED",
        },
    ]
    return rooms


