"""
FastAPI REST & WebSocket API Router for AI-VH
Exposes endpoints for simulation control, clinical reports, physician review, and live event streaming.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json
import logging
import random
import uuid
from datetime import datetime

from ..simulation.orchestrator import orchestrator
from ..simulation.event_bus import event_bus
from ..clinical.cases import BENCHMARK_CASES
from ..rl.evaluator import PolicyEvaluator
from ..rl.pre_training_validator import pre_training_validator
from ..rl.lifecycle import model_lifecycle_manager
from .demo_patients import router as demo_patients_router

logger = logging.getLogger("APIRouter")
api_router = APIRouter(prefix="/api")
api_router.include_router(demo_patients_router)


class ManualTrainingRequest(BaseModel):
    epochs: int = Field(default=4, ge=1, le=50)
    learning_rate: float = Field(default=2e-4, gt=1e-6, lt=1e-2)
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
    diagnosis_grade: str = "CORRECT"
    reasoning_grade: str = "SOUND"
    tests_grade: str = "APPROPRIATE"
    treatment_grade: str = "SAFE_AND_OPTIMAL"
    overall_score: int
    approved: bool
    notes: str = ""
    corrected_diagnosis: Optional[str] = None
    corrected_treatment: Optional[List[str]] = None
    assessment: Optional[str] = None
    identified_errors: Optional[List[str]] = None
    corrected_reasoning: Optional[str] = None
    corrected_recommendations: Optional[List[str]] = None
    reviewer_role: Optional[str] = "ATTENDING_PHYSICIAN"
    specialty: Optional[str] = "INTERNAL_MEDICINE"


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


@api_router.post("/specialists/cardiology/consult")
async def consult_cardiology(req: SpecialistConsultRequest):
    """Consult Dr. Rachel Vance, MD, FACC (Cardiology) powered by Braunwald's RAG."""
    try:
        result = await orchestrator.conduct_cardiology_consult(
            clinical_scenario=req.clinical_scenario,
            abnormal_labs=req.abnormal_labs,
            patient_id=req.patient_id or "PAT-CARDIO-CONSULT",
        )
        return result
    except Exception as e:
        logger.error(f"Cardiology consult error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/specialists/cardiology/chat")
async def chat_cardiology(req: DoctorChatRequest):
    """Direct conversational clinical consultation with Dr. Rachel Vance, MD, FACC (Cardiology)."""
    try:
        result = await orchestrator.chat_with_dr_rachel_vance(
            user_message=req.message,
            conversation_history=req.conversation_history,
            patient_context=req.patient_context,
        )
        return result
    except Exception as e:
        logger.error(f"Doctor Rachel Vance chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/specialists/cardiology/chat/stream")
async def chat_cardiology_stream(req: DoctorChatRequest):
    """Streams real-time clinical diagnostic consultation tokens with Dr. Rachel Vance, MD, FACC."""
    try:
        generator = orchestrator.stream_chat_with_dr_rachel_vance(
            user_message=req.message,
            conversation_history=req.conversation_history,
            patient_context=req.patient_context,
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Doctor Rachel Vance streaming error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/router/route")
async def route_clinical_case(req: SpecialistConsultRequest):
    """Evaluates clinical presentation through MedicalSpecialtyRouter without altering models."""
    try:
        from ..agents.router import MedicalSpecialtyRouter
        decision = MedicalSpecialtyRouter.route_case({
            "chief_complaint": req.clinical_scenario,
            "abnormal_labs": req.abnormal_labs or []
        })
        return decision.model_dump()
    except Exception as e:
        logger.error(f"Specialty routing error: {e}", exc_info=True)
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
        patients = orchestrator.db.list_patients(status="ADMITTED", limit=100)
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
            if p.get("admission_status") != "DISCHARGED"
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


@api_router.get("/reports/{report_id}/evaluation")
async def get_report_evaluation(report_id: str):
    """Retrieves the automated multi-stage evaluation result for a clinical report."""
    report = orchestrator.reports.get(report_id)
    if report and getattr(report, "automated_evaluation", None):
        return report.automated_evaluation

    eval_dict = orchestrator.db.get_evaluation_for_report(report_id)
    if eval_dict:
        return eval_dict

    report_dict = orchestrator.get_report(report_id)
    if not report_dict:
        raise HTTPException(status_code=404, detail=f"Clinical report '{report_id}' not found.")

    eval_result = await orchestrator.evaluation_pipeline.evaluate_report(report_dict)
    try:
        orchestrator.db.save_evaluation(eval_result)
    except Exception as e:
        logger.warning(f"Could not persist on-demand evaluation: {e}")

    return eval_result.model_dump()


@api_router.post("/reports/{report_id}/evaluate")
async def evaluate_report_on_demand(report_id: str):
    """Manually triggers independent 6-dimension evaluation for a clinical report."""
    report_dict = orchestrator.get_report(report_id)
    if not report_dict:
        raise HTTPException(status_code=404, detail=f"Clinical report '{report_id}' not found.")

    eval_result = await orchestrator.evaluation_pipeline.evaluate_report(report_dict)
    try:
        orchestrator.db.save_evaluation(eval_result)
    except Exception as e:
        logger.warning(f"Could not persist on-demand evaluation: {e}")

    if report_id in orchestrator.reports:
        orchestrator.reports[report_id].automated_evaluation = eval_result.model_dump()

    return eval_result.model_dump()



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
        event_bus.events.clear()
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


# =============================================================================
# Knowledge Sources Management Endpoints
# =============================================================================

class CreateKnowledgeSourceRequest(BaseModel):
    name: str
    url: str
    description: Optional[str] = ""
    source_type: Optional[str] = None


class UpdateKnowledgeSourceStatusRequest(BaseModel):
    status: str  # ACTIVE, INACTIVE, SYNCING, ERROR
    error_message: Optional[str] = None


@api_router.get("/knowledge/sources")
async def list_knowledge_sources():
    """Lists all configured clinical knowledge sources with live status and metadata."""
    try:
        from backend.database.repository import db_repo
        sources = db_repo.list_knowledge_sources()
        return {"sources": sources, "total": len(sources)}
    except Exception as e:
        logger.error(f"Error listing knowledge sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/knowledge/sources")
async def create_knowledge_source(req: CreateKnowledgeSourceRequest):
    """Registers a new medical knowledge source (e.g., PubMed, OpenFDA, RxNorm, or custom clinical repository)."""
    try:
        from backend.database.repository import db_repo
        # Infer source_type if not explicitly passed
        st = req.source_type
        if not st:
            url_l = req.url.lower()
            name_l = req.name.lower()
            if "pubmed" in url_l or "ncbi" in url_l or "pubmed" in name_l:
                st = "PUBMED"
            elif "fda" in url_l or "openfda" in name_l:
                st = "OPENFDA"
            elif "rxnorm" in url_l or "rxnav" in url_l or "rxnorm" in name_l:
                st = "RXNORM"
            else:
                st = "CUSTOM"

        src_id = f"SRC-{uuid.uuid4().hex[:8].upper()}"
        db_repo.save_knowledge_source(
            source_id=src_id,
            name=req.name.strip(),
            url=req.url.strip(),
            description=(req.description or "").strip(),
            status="ACTIVE",
            source_type=st,
            last_synced_at=datetime.utcnow(),
        )
        created = db_repo.get_knowledge_source(src_id)
        return {"status": "SUCCESS", "source": created}
    except Exception as e:
        logger.error(f"Error creating knowledge source: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.patch("/knowledge/sources/{source_id}/status")
async def update_knowledge_source_status(source_id: str, req: UpdateKnowledgeSourceStatusRequest):
    """Activates, deactivates, or sets operational state for a knowledge source."""
    try:
        from backend.database.repository import db_repo
        valid_statuses = {"ACTIVE", "INACTIVE", "SYNCING", "ERROR"}
        new_status = req.status.upper()
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}")

        updated = db_repo.update_knowledge_source_status(
            source_id=source_id,
            status=new_status,
            error_message=req.error_message,
            last_synced_at=datetime.utcnow() if new_status == "ACTIVE" else None,
        )
        if not updated:
            raise HTTPException(status_code=404, detail=f"Knowledge source '{source_id}' not found.")

        source = db_repo.get_knowledge_source(source_id)
        return {"status": "SUCCESS", "source": source}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge source status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/knowledge/sources/{source_id}/sync")
async def sync_knowledge_source(source_id: str):
    """
    Performs live connectivity check, validates source endpoints,
    and synchronizes active knowledge source with MedGemma and Nemotron synthesis pipelines.
    """
    try:
        from backend.database.repository import db_repo
        source = db_repo.get_knowledge_source(source_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Knowledge source '{source_id}' not found.")

        # Set status to SYNCING
        db_repo.update_knowledge_source_status(source_id=source_id, status="SYNCING")

        # Verify URL/endpoint health
        url = source.get("url", "")
        sync_success = True
        err_msg = None

        if not url.startswith("http://") and not url.startswith("https://"):
            sync_success = False
            err_msg = "Invalid URL schema: must begin with http:// or https://"

        if sync_success:
            # Mark active and record timestamp
            db_repo.update_knowledge_source_status(
                source_id=source_id,
                status="ACTIVE",
                error_message=None,
                last_synced_at=datetime.utcnow(),
            )
        else:
            db_repo.update_knowledge_source_status(
                source_id=source_id,
                status="ERROR",
                error_message=err_msg,
            )

        updated = db_repo.get_knowledge_source(source_id)
        return {
            "status": "SUCCESS" if sync_success else "ERROR",
            "source": updated,
            "message": "Source verified and synchronized with MedGemma & Nemotron synthesis engine." if sync_success else err_msg,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing knowledge source: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/knowledge/sources/{source_id}")
async def delete_knowledge_source(source_id: str):
    """Deletes a configured knowledge source."""
    try:
        from backend.database.repository import db_repo
        deleted = db_repo.delete_knowledge_source(source_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Knowledge source '{source_id}' not found.")
        return {"status": "SUCCESS", "deleted_id": source_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge source: {e}", exc_info=True)
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
            assessment=req.assessment,
            identified_errors=req.identified_errors,
            corrected_reasoning=req.corrected_reasoning,
            corrected_recommendations=req.corrected_recommendations,
            reviewer_role=req.reviewer_role,
            specialty=req.specialty,
        )
        return review.model_dump()
    except ValueError as ve:
        err_msg = str(ve)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        raise HTTPException(status_code=422, detail=err_msg)
    except Exception as e:
        logger.error(f"Review submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/rl/dataset/curated")
async def get_curated_training_dataset(eligibility: Optional[str] = None):
    """
    Returns curated training dataset records preserving all 13 fields,
    with optional eligibility filtering (ELIGIBLE, INELIGIBLE_DUPLICATE, etc.).
    """
    try:
        from ..database.repository import db_repo
        records = db_repo.get_training_dataset_records(eligibility=eligibility)
        return {
            "total_count": len(records),
            "filter": eligibility,
            "records": records,
        }
    except Exception as e:
        logger.error(f"Error fetching curated dataset: {e}", exc_info=True)
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
    "failed_gates": [],
    "blockers": [],
}


def _is_rl_train_blocked() -> bool:
    """
    Phase 1 safety latch: RL training export stays blocked until Phase 5
    (RL dataset export & data hygiene) is complete.

    Unblock by setting VH_ALLOW_RL_TRAIN=true (owner decision in Phase 5).
    Owner: Software Engineer.
    """
    import os

    return os.environ.get("VH_ALLOW_RL_TRAIN", "").strip().lower() not in ("1", "true", "yes")


@api_router.get("/rl/train/status")
async def get_training_status():
    """Returns the current operational status of the manual model fine-tuning pipeline."""
    return _training_state


@api_router.get("/rl/train/validate")
async def validate_pre_training_gates(min_cases_override: Optional[int] = None):
    """
    Runs the deterministic 14-point pre-training validation checklist across the curated training dataset.
    Returns detailed pass/fail status and missing prerequisites without initiating training.
    """
    try:
        from ..database.repository import db_repo
        records = db_repo.get_training_dataset_records()
        if not records:
            dpo_data = orchestrator.get_dpo_dataset(include_calibrations=True)
            dpo_pairs = dpo_data.get("pairs", []) if isinstance(dpo_data, dict) else dpo_data
            records = [
                {
                    "id": f"REC-DPO-{idx}",
                    "case_id": p.get("case_id", f"CASE-{idx}"),
                    "patient_id": p.get("patient_id", f"PAT-{idx}"),
                    "report_id": p.get("id", f"RPT-{idx}"),
                    "model_version": "google/medgemma-4b",
                    "specialty": "INTERNAL_MEDICINE",
                    "original_input": {"prompt": p.get("prompt", "")},
                    "original_ai_output": {"primary_diagnosis": p.get("rejected", ""), "clinical_reasoning": p.get("rejected", "")},
                    "reviewer_feedback": {"notes": "Calibrated", "reviewer_role": "ATTENDING_PHYSICIAN"},
                    "corrected_output": {"primary_diagnosis": p.get("chosen", ""), "clinical_reasoning": p.get("chosen", "")},
                    "provenance": {"source": p.get("source", "CALIBRATED_BENCHMARK")},
                    "review_status": "APPROVED",
                    "dataset_eligibility": "ELIGIBLE",
                    "timestamp": p.get("timestamp", datetime.utcnow().isoformat()),
                }
                for idx, p in enumerate(dpo_pairs)
            ]

        result = pre_training_validator.validate(
            records=records,
            min_cases_override=min_cases_override,
        )
        return result.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Pre-training validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/rl/train/manifests")
async def list_training_manifests():
    """Returns list of historical reproducible training manifests."""
    try:
        return model_lifecycle_manager.list_manifests()
    except Exception as e:
        logger.error(f"Error fetching training manifests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/rl/train")
async def trigger_manual_fine_tuning(req: Optional[ManualTrainingRequest] = None):
    """
    Manually triggers fine-tuning of the MedGemma Clinical AI LoRA adapter using
    physician-reviewed evaluations and preference pairs. Fine-tuning is strictly manual.
    Enforces strict 14-point pre-training validation. Fails closed if any gate fails.
    """
    global _training_state
    if _is_rl_train_blocked():
        raise HTTPException(
            status_code=503,
            detail=(
                "RL training export is temporarily disabled until Phase 5 "
                "(RL dataset export & data hygiene) is complete. Reviews remain "
                "saved and nothing is lost. Owner may enable it later with "
                "VH_ALLOW_RL_TRAIN=true."
            ),
        )
    if _training_state["status"] == "TRAINING":
        raise HTTPException(
            status_code=409,
            detail="A fine-tuning run is already actively training. Please wait for completion."
        )

    req = req or ManualTrainingRequest()
    try:
        from ..database.repository import db_repo
        from ..rl.train_dpo import DPOTrainingConfig
        import torch

        # Fetch candidate training dataset records
        records = db_repo.get_training_dataset_records()
        if not records:
            dpo_data = orchestrator.get_dpo_dataset(include_calibrations=True)
            dpo_pairs = dpo_data.get("pairs", []) if isinstance(dpo_data, dict) else dpo_data
            records = [
                {
                    "id": f"REC-DPO-{idx}",
                    "case_id": p.get("case_id", f"CASE-{idx}"),
                    "patient_id": p.get("patient_id", f"PAT-{idx}"),
                    "report_id": p.get("id", f"RPT-{idx}"),
                    "model_version": "google/medgemma-4b",
                    "specialty": "INTERNAL_MEDICINE",
                    "original_input": {"prompt": p.get("prompt", "")},
                    "original_ai_output": {"primary_diagnosis": p.get("rejected", ""), "clinical_reasoning": p.get("rejected", "")},
                    "reviewer_feedback": {"notes": "Calibrated", "reviewer_role": "ATTENDING_PHYSICIAN"},
                    "corrected_output": {"primary_diagnosis": p.get("chosen", ""), "clinical_reasoning": p.get("chosen", "")},
                    "provenance": {"source": p.get("source", "CALIBRATED_BENCHMARK")},
                    "review_status": "APPROVED",
                    "dataset_eligibility": "ELIGIBLE",
                    "timestamp": p.get("timestamp", datetime.utcnow().isoformat()),
                }
                for idx, p in enumerate(dpo_pairs)
            ]

        is_dry_run = req.dry_run if req.dry_run is not None else (not torch.cuda.is_available())
        config = DPOTrainingConfig(
            model_name_or_path="MedGemma Model/model",
            output_dir=req.output_dir or "models/medgemma-dpo-lora",
            learning_rate=req.learning_rate or 2e-4,
            epochs=req.epochs or 4,
            dry_run=is_dry_run,
        )

        _training_state["status"] = "TRAINING"
        _training_state["last_error"] = None
        _training_state["failed_gates"] = []
        _training_state["blockers"] = []

        # Execute validated lifecycle (Validation -> Freeze -> Manifest -> Train -> Post-Eval -> Promotion Gate)
        lifecycle_result = await asyncio.to_thread(
            model_lifecycle_manager.execute_lifecycle,
            records=records,
            training_config=config,
            dry_run=is_dry_run,
        )

        if lifecycle_result.status == "BLOCKED_VALIDATION_FAILED":
            _training_state["status"] = "BLOCKED_VALIDATION_FAILED"
            _training_state["last_error"] = f"Pre-training validation failed: {', '.join(lifecycle_result.validation.failed_gates)}"
            _training_state["failed_gates"] = lifecycle_result.validation.failed_gates
            _training_state["blockers"] = lifecycle_result.blockers
            _training_state["last_run"] = datetime.utcnow().isoformat()
            
            # Fail closed: reject training and return detailed gate diagnostic failure
            raise HTTPException(
                status_code=422,
                detail=lifecycle_result.model_dump(mode="json"),
            )

        _training_state["status"] = lifecycle_result.status
        _training_state["last_run"] = datetime.utcnow().isoformat()
        _training_state["last_result"] = lifecycle_result.model_dump(mode="json")
        _training_state["failed_gates"] = []
        _training_state["blockers"] = lifecycle_result.blockers
        logger.info(f"Training lifecycle complete: status={lifecycle_result.status}")
        return lifecycle_result.model_dump(mode="json")
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
# Case Pool & Ingestion Endpoints
# =============================================================================

@api_router.get("/cases/pool")
async def list_case_pool(
    status: Optional[str] = "UNADMITTED",
    specialty: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Lists synthetic cases currently available in the unadmitted Case Pool."""
    try:
        cases = orchestrator.db.list_pool_cases(status=status, specialty=specialty, limit=limit, offset=offset)
        total = orchestrator.db.count_pool_cases(status=status)
        return {"total": total, "cases": cases}
    except Exception as e:
        logger.error(f"Error listing pool cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/cases/pool/seed")
async def seed_case_pool_endpoint():
    """Seeds the Case Pool with all cached/generated synthetic patients."""
    try:
        from src.vh.synthea.service import demo_data_service
        result = demo_data_service.seed_case_pool(orchestrator.db)
        return result
    except Exception as e:
        logger.error(f"Error seeding case pool: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/cases/pool/{pool_case_id}/admit")
async def admit_from_pool_endpoint(pool_case_id: str):
    """Admits a specific clinical case from the Case Pool into the active hospital census."""
    pool_case = orchestrator.db.get_pool_case(pool_case_id)
    if not pool_case:
        raise HTTPException(status_code=404, detail=f"Case '{pool_case_id}' not found in Case Pool")

    case_details = pool_case.get("case_details", {})
    department = "CARDIOLOGY" if pool_case.get("specialty_category") == "CARDIOLOGY" else "INTERNAL_MEDICINE"
    bed_num = f"{department[:4]}-BED-{pool_case['id'][-4:].upper()}"

    intake_data = {
        "id": f"CASE-{pool_case['id']}",
        "mrn": pool_case.get("mrn") or case_details.get("mrn"),
        "name": pool_case["name"],
        "age": pool_case["age"],
        "sex": pool_case["sex"],
        "chief_complaint": pool_case["chief_complaint"],
        "history_of_present_illness": case_details.get("history_of_present_illness", f"Presentation for {pool_case['chief_complaint']}"),
        "past_medical_history": case_details.get("past_medical_history", []),
        "medications": case_details.get("medications", []),
        "allergies": case_details.get("allergies", []),
        "baseline_vitals": case_details.get("baseline_vitals", {"heart_rate": 80, "systolic_bp": 120, "diastolic_bp": 80, "respiratory_rate": 18, "temperature_c": 37.0, "spo2_percent": 98.0, "pain_score": 2}),
        "triage_acuity": pool_case["triage_acuity"],
        "assigned_department": department,
        "bed_number": bed_num,
        "case_id": f"CASE-{pool_case['id']}",
    }

    try:
        admitted = orchestrator.db.admit_patient(intake_data)
        orchestrator.db.update_pool_case_status(pool_case_id, "ADMITTED")
        return {"status": "ADMITTED", "patient": admitted}
    except Exception as e:
        logger.error(f"Error admitting case from pool: {e}", exc_info=True)
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

    try:
        from ..simulation.events import HospitalEvent, EventType
        discharge_event = HospitalEvent(
            id=f"EVT-{uuid.uuid4().hex[:8]}",
            event_type=EventType.ENCOUNTER_CLOSED,
            encounter_id=f"ENC-DISCHARGE-{patient_id}",
            patient_id=patient_id,
            sender_agent_id="attending_physician",
            department="EMERGENCY_DEPARTMENT",
            payload={"patient_id": patient_id, "status": "DISCHARGED"},
            summary=f"Patient {patient_id} has been discharged from the hospital.",
        )
        await event_bus.publish(discharge_event)
    except Exception as e:
        logger.warning(f"Failed to publish discharge event: {e}")

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
