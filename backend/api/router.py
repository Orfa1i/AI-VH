"""
FastAPI REST & WebSocket API Router for AI-VH
Exposes endpoints for simulation control, clinical reports, physician review, and live event streaming.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import logging
import random
from datetime import datetime

from ..simulation.orchestrator import orchestrator
from ..simulation.event_bus import event_bus
from ..clinical.cases import BENCHMARK_CASES
from ..rl.evaluator import PolicyEvaluator
from .demo_patients import router as demo_patients_router

logger = logging.getLogger("APIRouter")
api_router = APIRouter(prefix="/api")
api_router.include_router(demo_patients_router)


class ManualTrainingRequest(BaseModel):
    epochs: Optional[int] = 4
    learning_rate: Optional[float] = 2e-4
    dry_run: Optional[bool] = None
    output_dir: Optional[str] = "models/medgemma-dpo-lora"
    include_calibrations: Optional[bool] = True



class SimulationRequest(BaseModel):
    case_id: str = "CASE-101"


class SpecialistConsultRequest(BaseModel):
    clinical_scenario: str
    abnormal_labs: Optional[List[str]] = None
    patient_id: Optional[str] = "PAT-CONSULT"


class DoctorChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    patient_context: Optional[Dict[str, Any]] = None


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


class ComparativeInferenceRequest(BaseModel):
    case_id: Optional[str] = "CASE-101"
    clinical_scenario: Optional[str] = None
    force_gpu: Optional[bool] = False


class PatientAdmitRequest(BaseModel):
    name: str
    age: int
    sex: str
    chief_complaint: str
    history_of_present_illness: Optional[str] = ""
    past_medical_history: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    baseline_vitals: Optional[Dict[str, Any]] = None
    triage_acuity: Optional[str] = "URGENT"
    assigned_department: Optional[str] = "EMERGENCY"
    bed_number: Optional[str] = None
    case_id: Optional[str] = None


class StaffCreateRequest(BaseModel):
    name: str
    role: str
    specialty: str
    title: str
    department: str
    status: Optional[str] = "ON_DUTY"
    credentials: str
    bio: str
    system_prompt: Optional[str] = None


class StaffStatusUpdateRequest(BaseModel):
    status: str



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


@api_router.post("/specialists/internal-medicine/chat")
async def chat_internal_medicine(req: DoctorChatRequest):
    """Direct conversational clinical consultation with Dr. Marcus Vance, MD, FACP."""
    try:
        result = await orchestrator.chat_with_dr_vance(
            user_message=req.message,
            conversation_history=req.conversation_history,
            patient_context=req.patient_context,
        )
        return result
    except Exception as e:
        logger.error(f"Doctor Marcus Vance chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/specialists/internal-medicine/chat/stream")
async def chat_internal_medicine_stream(req: DoctorChatRequest):
    """Streams real-time clinical diagnostic consultation tokens with Dr. Marcus Vance, MD, FACP."""
    try:
        generator = orchestrator.stream_chat_with_dr_vance(
            user_message=req.message,
            conversation_history=req.conversation_history,
            patient_context=req.patient_context,
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Doctor Marcus Vance streaming error: {e}", exc_info=True)
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
    """Returns active patient cases from the database (starts empty for fresh manual entry)."""
    try:
        patients = orchestrator.db.list_patients(limit=100)
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "age": p["age"],
                "sex": p["sex"],
                "chief_complaint": p["chief_complaint"],
                "acuity": p.get("triage_acuity", "URGENT"),
                "department": p.get("assigned_department", "EMERGENCY"),
                "bed_number": p.get("bed_number", ""),
            }
            for p in patients
        ]
    except Exception as e:
        logger.error(f"Error listing cases from patients: {e}", exc_info=True)
        return []


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


@api_router.get("/reports/pending")
async def get_pending_reports():
    """Returns only clinical reports awaiting doctor review."""
    return orchestrator.get_pending_reports()


@api_router.get("/reports/reviewed")
async def get_reviewed_reports():
    """Returns all clinical reports that have been evaluated and reviewed by doctors."""
    return orchestrator.get_reviewed_reports()



@api_router.get("/reports/history")
async def get_reports_history(case_id: Optional[str] = None, limit: int = 50, offset: int = 0):
    """Retrieves persistent clinical reports from the database with pagination and case filtering."""
    try:
        reports = orchestrator.db.list_reports(case_id=case_id, limit=limit, offset=offset)
        total = orchestrator.db.count_reports()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "reports": reports,
        }
    except Exception as e:
        logger.error(f"Error fetching report history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/reviews/history")
async def get_reviews_history(limit: int = 50, offset: int = 0):
    """Retrieves persistent physician reviews from the database."""
    try:
        reviews = orchestrator.db.list_reviews(limit=limit, offset=offset)
        total = orchestrator.db.count_reviews()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "reviews": reviews,
        }
    except Exception as e:
        logger.error(f"Error fetching review history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/database/status")
async def get_database_status():
    """Returns the operational status of the PostgreSQL / SQLite database persistence layer."""
    status = orchestrator.db.manager.get_status()
    status["total_reports"] = orchestrator.db.count_reports()
    status["total_reviews"] = orchestrator.db.count_reviews()
    status["total_knowledge_chunks"] = orchestrator.db.count_knowledge_chunks()
    return status


@api_router.post("/database/purge-mock-data")
async def purge_mock_data():
    """Safely purges mock/test data from patients, reports, reviews, and encounters.
    Preserves Harrison's RAG knowledge base and medical staff."""
    try:
        deleted = orchestrator.db.purge_mock_data()
        orchestrator.reports.clear()
        orchestrator.encounters.clear()
        orchestrator.reviews.clear()
        logger.info(f"Purged mock data: {deleted}")
        return {"status": "success", "message": "Mock data purged successfully", "deleted": deleted}
    except Exception as e:
        logger.error(f"Error purging mock data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/knowledge/search")
async def search_medical_knowledge(
    q: str,
    specialty: Optional[str] = None,
    top_k: int = 3,
):
    """
    Performs semantic vector and keyword retrieval against the textbook knowledge database.
    """
    try:
        results = orchestrator.db.search_knowledge_chunks(
            query=q,
            specialty=specialty,
            top_k=top_k,
        )
        return {
            "query": q,
            "specialty": specialty,
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Knowledge search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/knowledge/seed")
async def seed_knowledge_base():
    """
    Triggers seeding of Harrison's Internal Medicine textbook chunks into the database vector store.
    """
    try:
        from backend.database.seed_knowledge import seed_harrison_knowledge
        result = seed_harrison_knowledge(orchestrator.db)
        return result
    except Exception as e:
        logger.error(f"Knowledge seeding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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


_training_state: Dict[str, Any] = {
    "status": "IDLE",
    "last_run": None,
    "last_result": None,
    "last_error": None,
}


@api_router.get("/rl/train/status")
async def get_training_status():
    """Returns the current operational status of the manual model fine-tuning pipeline."""
    return _training_state


@api_router.post("/rl/train")
async def trigger_manual_fine_tuning(req: Optional[ManualTrainingRequest] = None):
    """
    Manually triggers fine-tuning of the MedGemma Clinical AI LoRA adapter using
    physician-reviewed evaluations and preference pairs. Fine-tuning is strictly manual.
    """
    global _training_state
    if _training_state["status"] == "TRAINING":
        raise HTTPException(
            status_code=409,
            detail="A fine-tuning run is already actively training. Please wait for completion."
        )

    req = req or ManualTrainingRequest()
    try:
        _training_state["status"] = "TRAINING"
        _training_state["last_error"] = None

        # 1. Compile and export the latest preference pairs to JSONL
        export_res = orchestrator.export_dpo_dataset(output_path="data/dpo_preference_dataset.jsonl")
        exported_count = export_res.get("exported_count", 0)
        if exported_count == 0:
            _training_state["status"] = "IDLE"
            _training_state["last_error"] = "No preference pairs available for training. Please evaluate and review clinical cases first."
            raise HTTPException(
                status_code=400,
                detail="No preference pairs found. Please review at least one clinical case first."
            )

        # 2. Run DPO training with config
        from ..rl.train_dpo import DPOTrainingConfig, run_dpo_training
        import torch

        # Dry run logic: if explicitly passed use it; otherwise, if no cuda device, default to dry-run verification
        is_dry_run = req.dry_run if req.dry_run is not None else (not torch.cuda.is_available())

        config = DPOTrainingConfig(
            model_name_or_path="MedGemma Model/model",
            dataset_path=export_res.get("filepath", "data/dpo_preference_dataset.jsonl"),
            output_dir=req.output_dir or "models/medgemma-dpo-lora",
            learning_rate=req.learning_rate or 2e-4,
            epochs=req.epochs or 4,
            dry_run=is_dry_run,
        )

        result = run_dpo_training(config)
        _training_state["status"] = "COMPLETED"
        _training_state["last_run"] = datetime.utcnow().isoformat()
        _training_state["last_result"] = result
        logger.info(f"Manual fine-tuning finished successfully: status={result.get('status')}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual fine-tuning execution error: {e}", exc_info=True)
        _training_state["status"] = "FAILED"
        _training_state["last_error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Fine-tuning failed: {str(e)}")



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


@api_router.post("/rl/inference/compare")
async def run_comparative_model_inference(req: ComparativeInferenceRequest):
    """
    Executes a live comparative on-device model inference comparing:
    - Base MedGemma (v0.1 Unaligned Foundation Model)
    - RL DPO MedGemma (v0.3 Physician-Aligned LoRA Model)
    """
    try:
        from ..llm.medgemma_service import medgemma_service
        result = medgemma_service.generate_comparative_inference(
            case_id=req.case_id,
            clinical_scenario=req.clinical_scenario,
            force_gpu=req.force_gpu or False,
        )
        return result
    except Exception as e:
        logger.error(f"Error in comparative model inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Patient Admission & EHR Storage Endpoints
# =============================================================================

@api_router.post("/patients/admit")
async def admit_patient_endpoint(req: PatientAdmitRequest):
    """
    Intake and admission endpoint: converts an incoming clinical case or manual intake
    into an admitted patient record in the database with assigned department and bed.
    """
    try:
        case_dict = req.model_dump()
        admitted = orchestrator.db.admit_patient(case_dict)
        return admitted
    except Exception as e:
        logger.error(f"Error admitting patient: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/patients")
async def list_patients_endpoint(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """Lists admitted patients, filterable by status (ADMITTED, IN_ENCOUNTER, DISCHARGED)."""
    try:
        patients = orchestrator.db.list_patients(status=status, limit=limit, offset=offset)
        total = orchestrator.db.count_patients(status=status)
        return {"total": total, "patients": patients}
    except Exception as e:
        logger.error(f"Error listing patients: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/patients/{patient_id}")
async def get_patient_endpoint(patient_id: str):
    """Retrieves full clinical chart and EHR for a specific patient ID or MRN."""
    patient = orchestrator.db.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    return patient


@api_router.post("/patients/{patient_id}/discharge")
async def discharge_patient_endpoint(patient_id: str):
    """Discharges a patient from the hospital."""
    success = orchestrator.db.discharge_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found or already discharged")
    return {"status": "DISCHARGED", "patient_id": patient_id}


# =============================================================================
# Hospital Personnel & Staff Management Endpoints
# =============================================================================

@api_router.get("/staff")
async def list_staff_endpoint(role: Optional[str] = None, department: Optional[str] = None):
    """Returns the hospital clinical and operational staff roster."""
    try:
        staff_members = orchestrator.db.list_staff(role=role, department=department)
        return {"total": len(staff_members), "staff": staff_members}
    except Exception as e:
        logger.error(f"Error listing staff: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/staff/{staff_id}")
async def get_staff_endpoint(staff_id: str):
    """Retrieves detailed credentials and profile for a staff member."""
    member = orchestrator.db.get_staff_member(staff_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Staff member '{staff_id}' not found")
    return member


@api_router.post("/staff")
async def create_staff_endpoint(req: StaffCreateRequest):
    """Adds a new healthcare professional or staff member to the hospital directory."""
    try:
        staff_id = orchestrator.db.add_staff_member(req.model_dump())
        member = orchestrator.db.get_staff_member(staff_id)
        return member
    except Exception as e:
        logger.error(f"Error creating staff member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/staff/{staff_id}/status")
async def update_staff_status_endpoint(staff_id: str, req: StaffStatusUpdateRequest):
    """Updates the shift/duty status of a hospital staff member (ON_DUTY, IN_CONSULT, OFF_DUTY)."""
    success = orchestrator.db.update_staff_status(staff_id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Staff member '{staff_id}' not found")
    return {"staff_id": staff_id, "status": req.status}


@api_router.delete("/staff/{staff_id}")
async def delete_staff_endpoint(staff_id: str):
    """Removes an individual staff member from the hospital directory."""
    success = orchestrator.db.delete_staff_member(staff_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Staff member '{staff_id}' not found")
    return {"status": "DELETED", "staff_id": staff_id}


@api_router.delete("/staff")
async def delete_all_staff_except_endpoint(keep_id: str = "STAFF-VANCE"):
    """Prunes the hospital staff directory, keeping only the specified staff member (default: Dr. Marcus Vance)."""
    deleted_count = orchestrator.db.delete_all_staff_except([keep_id])
    return {"status": "PRUNED", "deleted_count": deleted_count, "kept_id": keep_id}


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


@api_router.websocket("/inpatient/telemetry/stream")
async def telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    
    # We maintain a localized copy of the rooms to mutate their state slightly over time
    current_rooms = await get_inpatient_rooms()
    
    try:
        while True:
            # Apply slight physiological variance
            for room in current_rooms:
                room["heart_rate"] = max(40, min(200, room["heart_rate"] + random.randint(-2, 2)))
                room["systolic_bp"] = max(80, min(220, room["systolic_bp"] + random.randint(-3, 3)))
                room["diastolic_bp"] = max(40, min(120, room["diastolic_bp"] + random.randint(-2, 2)))
                room["respiratory_rate"] = max(8, min(40, room["respiratory_rate"] + random.randint(-1, 1)))
                room["spo2"] = max(80, min(100, round(room["spo2"] + random.choice([-1, 0, 0, 0, 1]), 1))) # Mostly stable, small chance to change

            await websocket.send_json(current_rooms)
            await asyncio.sleep(1.5)
            
    except WebSocketDisconnect:
        logger.info("Telemetry WebSocket disconnected")
    except Exception as e:
        logger.error(f"Telemetry stream error: {e}", exc_info=True)
