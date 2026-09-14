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

