"""
Hospital Simulation Orchestrator
Coordinates encounters, manages clinical state progression, and provides
the central execution loop for the virtual hospital platform.
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .events import HospitalEvent, EventType
from .event_bus import event_bus
from ..clinical.models import (
    ClinicalReport,
    PhysicianReview,
    DiagnosisFeedback,
    ReasoningFeedback,
    TestAppropriatenessFeedback,
    TreatmentSafetyFeedback,
    ReviewAssessment,
    ReviewErrorTaxonomy,
)
from ..clinical.cases import PatientGroundTruth, get_benchmark_case, BENCHMARK_CASES
from ..clinical.tools import ClinicalToolkit
from ..rag.book_parser import HarrisonParser
from ..rag.vector_index import MedicalKnowledgeIndex
from ..llm.medgemma_service import medgemma_service
from ..agents.patient import PatientAgent
from ..agents.nurse import NurseAgent
from ..agents.doctor import DoctorAgent
from ..agents.lab import LaboratoryAgent
from ..agents.radiology import RadiologyAgent
from ..agents.pharmacist import PharmacistAgent
from ..agents.specialists.internal_medicine import InternalMedicineSpecialistAgent
from ..rag.specialists.internal_medicine_rag import InternalMedicineRAGAgent
from ..agents.specialists.cardiology import CardiologySpecialistAgent
from ..rag.specialists.cardiology_rag import CardiologyRAGAgent
from ..agents.specialists.surgery import SurgerySpecialistAgent
from ..rag.specialists.surgery_rag import SurgeryRAGAgent
from ..agents.specialists.emergency import EmergencySpecialistAgent
from ..rag.specialists.emergency_rag import EmergencyMedicineRAGAgent
from ..agents.specialists.infectious_diseases import InfectiousDiseasesSpecialistAgent
from ..rag.specialists.infectious_diseases_rag import InfectiousDiseasesRAGAgent
from ..agents.specialists.gynecology import GynecologySpecialistAgent
from ..rag.specialists.gynecology_rag import GynecologyRAGAgent
from ..agents.specialists.neurology import NeurologySpecialistAgent
from ..rag.specialists.neurology_rag import NeurologyRAGAgent
from ..agents.router import MedicalSpecialtyRouter
from ..rl.dpo_generator import DPOPreferenceGenerator, DPOPreferencePair
from ..rl.dataset_curator import dataset_curator
from ..database.repository import db_repo
from ..evaluation import evaluation_pipeline

logger = logging.getLogger("SimulationOrchestrator")


class EncounterState:
    def __init__(self, encounter_id: str, case: PatientGroundTruth):
        self.encounter_id = encounter_id
        self.case = case
        self.start_time = datetime.utcnow()
        self.status = "INITIALIZING"
        self.current_department = "RECEPTION"
        self.report: Optional[ClinicalReport] = None
        self.review: Optional[PhysicianReview] = None
        self.events: List[HospitalEvent] = []


class HospitalOrchestrator:
    def __init__(self, enable_gpu: bool = False):
        self.enable_gpu = enable_gpu
        self.encounters: Dict[str, EncounterState] = {}
        self.reports: Dict[str, ClinicalReport] = {}
        self.reviews: Dict[str, PhysicianReview] = {}
        
        # Database persistence layer (PostgreSQL / SQLite)
        self.db = db_repo
        
        # Restore any persisted reports and reviews from database
        restored_reports = 0
        for r_dict in self.db.list_reports(limit=500):
            try:
                rep_obj = ClinicalReport.model_validate(r_dict)
                self.reports[rep_obj.id] = rep_obj
                restored_reports += 1
            except Exception as e:
                logger.warning(f"Could not restore report from DB: {e}")

        restored_reviews = 0
        for rev_dict in self.db.list_reviews(limit=500):
            try:
                rev_obj = PhysicianReview.model_validate(rev_dict)
                self.reviews[rev_obj.id] = rev_obj
                restored_reviews += 1
            except Exception as e:
                logger.warning(f"Could not restore review from DB: {e}")

        if restored_reports or restored_reviews:
            logger.info(f"Restored {restored_reports} clinical reports and {restored_reviews} reviews from persistent database.")

        # Load Harrison's RAG index once
        logger.info("Initializing medical knowledge base from Harrison's Internal Medicine...")
        parser = HarrisonParser()
        chunks = parser.load_or_extract_chunks(max_pages_per_chapter=2)
        self.rag_index = MedicalKnowledgeIndex(chunks)

        # Reuse the module-level MedGemma singleton (loaded once at FastAPI startup in
        # main.py) instead of constructing a separate, never-loaded instance -- a
        # previous version of this line created its own `MedGemmaService(enable_gpu=...)`
        # whose self.model always stayed None, so every real clinical encounter silently
        # ran the 2-branch keyword heuristic engine instead of the real GPU model, even
        # though live GPU inference had been verified working for the RL benchmark
        # endpoints (which used this same singleton directly).
        self.medgemma = medgemma_service
        self.im_rag_agent = InternalMedicineRAGAgent()
        self.im_specialist = InternalMedicineSpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.im_rag_agent
        )
        self.cardio_rag_agent = CardiologyRAGAgent()
        self.cardio_specialist = CardiologySpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.cardio_rag_agent
        )
        self.surgery_rag_agent = SurgeryRAGAgent()
        self.surgery_specialist = SurgerySpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.surgery_rag_agent
        )
        self.emergency_rag_agent = EmergencyMedicineRAGAgent()
        self.emergency_specialist = EmergencySpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.emergency_rag_agent
        )
        self.id_rag_agent = InfectiousDiseasesRAGAgent()
        self.id_specialist = InfectiousDiseasesSpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.id_rag_agent
        )
        self.gynecology_rag_agent = GynecologyRAGAgent()
        self.gynecology_specialist = GynecologySpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.gynecology_rag_agent
        )
        self.neurology_rag_agent = NeurologyRAGAgent()
        self.neurology_specialist = NeurologySpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.neurology_rag_agent
        )
        self.pharmacist = PharmacistAgent()
        self.evaluation_pipeline = evaluation_pipeline

    async def conduct_specialist_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Marcus Vance, MD (Internal Medicine)."""
        encounter_id = f"CON-{uuid.uuid4().hex[:6].upper()}"
        return await self.im_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_vance(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Marcus Vance, MD, FACP."""
        return await self.im_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_vance(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Marcus Vance."""
        async for chunk in self.im_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def conduct_cardiology_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-CARDIO-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Rachel Vance, MD, FACC (Cardiology)."""
        encounter_id = f"CON-CARDIO-{uuid.uuid4().hex[:6].upper()}"
        return await self.cardio_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_rachel_vance(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Rachel Vance, MD, FACC (Cardiology)."""
        return await self.cardio_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_rachel_vance(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Rachel Vance (Cardiology)."""
        async for chunk in self.cardio_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def conduct_surgery_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-SURGERY-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Sarah Lin, MD, FACS (Surgery)."""
        encounter_id = f"CON-SURGERY-{uuid.uuid4().hex[:6].upper()}"
        return await self.surgery_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_sarah_lin(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Sarah Lin, MD, FACS (Surgery)."""
        return await self.surgery_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_sarah_lin(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Sarah Lin (Surgery)."""
        async for chunk in self.surgery_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def conduct_emergency_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-EMERGENCY-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. David Kim, MD, FACEP (Emergency Medicine)."""
        encounter_id = f"CON-EMERGENCY-{uuid.uuid4().hex[:6].upper()}"
        return await self.emergency_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_david_kim(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. David Kim, MD, FACEP (Emergency Medicine)."""
        return await self.emergency_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_david_kim(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. David Kim (Emergency Medicine)."""
        async for chunk in self.emergency_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def conduct_infectious_diseases_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-ID-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Anthony Mercer, MD, FIDSA (Infectious Diseases)."""
        encounter_id = f"CON-ID-{uuid.uuid4().hex[:6].upper()}"
        return await self.id_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_anthony_mercer(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Anthony Mercer, MD, FIDSA (Infectious Diseases)."""
        return await self.id_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_anthony_mercer(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Anthony Mercer (Infectious Diseases)."""
        async for chunk in self.id_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def conduct_gynecology_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-GYN-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Evelyn Reed, MD, FACOG (Gynecology)."""
        encounter_id = f"CON-GYN-{uuid.uuid4().hex[:6].upper()}"
        return await self.gynecology_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_evelyn_reed(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Evelyn Reed, MD, FACOG (Gynecology)."""
        return await self.gynecology_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_evelyn_reed(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Evelyn Reed (Gynecology)."""
        async for chunk in self.gynecology_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def conduct_neurology_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-NEURO-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Alexander Hayes, MD, PhD, FAAN (Neurology)."""
        encounter_id = f"CON-NEURO-{uuid.uuid4().hex[:6].upper()}"
        return await self.neurology_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_alexander_hayes(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Alexander Hayes, MD, PhD, FAAN (Neurology)."""
        return await self.neurology_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_alexander_hayes(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Alexander Hayes (Neurology)."""
        async for chunk in self.neurology_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    async def review_medication_orders(
        self,
        prescriptions: List[str],
        patient_id: str = "CASE-101",
        diagnosis: str = "Clinical Encounter Diagnosis",
    ) -> Dict[str, Any]:
        """On-demand medication reconciliation by Dr. Elena Rostova, PharmD."""
        case = None
        for c in BENCHMARK_CASES:
            if c.id == patient_id:
                case = c
                break
        if not case:
            case = BENCHMARK_CASES[0]

        encounter_id = f"PHARM-REV-{uuid.uuid4().hex[:6].upper()}"
        report = await self.pharmacist.review_medication_order(
            encounter_id=encounter_id,
            prescriptions=prescriptions,
            patient=case,
            diagnosis=diagnosis,
        )
        return report.model_dump()

    async def run_encounter_simulation(self, case_id: str = "CASE-101") -> Dict[str, Any]:
        """Runs the complete clinical loop from patient arrival to report generation."""
        encounter_id = f"ENC-{uuid.uuid4().hex[:8].upper()}"
        case = get_benchmark_case(case_id)
        state = EncounterState(encounter_id, case)
        self.encounters[encounter_id] = state

        logger.info(f"Starting simulated encounter {encounter_id} for {case.name} ({case.true_diagnosis})")

        # 1. Setup Agents, Router, and Toolkit
        toolkit = ClinicalToolkit(ground_truth=case, rag_index=self.rag_index)
        patient_agent = PatientAgent(ground_truth=case)
        nurse_agent = NurseAgent()
        lab_agent = LaboratoryAgent()
        radiology_agent = RadiologyAgent()

        # Specialty Routing (determines specialty only; not the model being trained)
        routing = MedicalSpecialtyRouter.route_case(case)
        logger.info(f"Encounter {encounter_id} routed to {routing.specialty} ({routing.suggested_specialist_name}): {routing.primary_rationale}")

        if routing.specialty == "CARDIOLOGY":
            doctor_agent = CardiologySpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.cardio_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        else:
            doctor_agent = InternalMedicineSpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.im_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )

        # 2. Patient Arrival at Reception & Waiting Area
        state.status = "ARRIVED"
        state.current_department = "RECEPTION"
        await patient_agent.arrive(encounter_id)
        await asyncio.sleep(0.05)

        # 3. Nurse Triage at Nurse Station / Triage Bay
        state.status = "TRIAGE"
        state.current_department = "NURSE_STATION"
        await nurse_agent.triage_patient(encounter_id, toolkit)
        await asyncio.sleep(0.05)

        # 4. Specialty Routing Notification
        await event_bus.publish(
            HospitalEvent(
                id=f"EVT-{uuid.uuid4().hex[:8]}",
                event_type=EventType.SPECIALTY_ROUTED,
                encounter_id=encounter_id,
                patient_id=case.id,
                sender_agent_id="specialty_router",
                department="NURSE_STATION",
                payload=routing.model_dump(),
                summary=f"Specialty Router assigned case to {routing.specialty} ({routing.suggested_specialist_name}): {routing.primary_rationale}",
            )
        )

        # 5. Specialist Doctor Encounter in Examination Room
        state.status = "EXAMINATION"
        state.current_department = "CARDIOLOGY_SUITE" if routing.specialty == "CARDIOLOGY" else "EXAMINATION_ROOM_1"
        report = await doctor_agent.conduct_clinical_encounter(encounter_id, toolkit)
        
        # 5. Pharmacist Medication Safety Review & Dispensing in Pharmacy
        state.status = "PHARMACY_REVIEW"
        state.current_department = "PHARMACY"
        if report.treatment_plan:
            pharm_report = await self.pharmacist.review_medication_order(
                encounter_id=encounter_id,
                prescriptions=report.treatment_plan,
                patient=case,
                diagnosis=report.primary_diagnosis,
            )
            report.pharmacist_review = pharm_report
            await asyncio.sleep(0.05)

        # 6. Independent Multi-Stage Evaluation Pipeline
        # Every generated diagnosis report must pass through independent evaluation before entering the human Review Page.
        state.status = "EVALUATION"
        state.current_department = "AUDIT_AND_SAFETY"
        eval_result = await self.evaluation_pipeline.evaluate_report(
            report=report,
            patient_presentation={
                "age": case.age,
                "sex": case.sex,
                "chief_complaint": case.chief_complaint,
                "history_of_present_illness": getattr(case, "history_of_present_illness", case.chief_complaint),
                "past_medical_history": getattr(case, "past_medical_history", getattr(case, "medical_history", [])),
                "medications": getattr(case, "medications", getattr(case, "current_medications", [])),
                "allergies": getattr(case, "allergies", []),
                "vital_signs": toolkit.get_vital_signs(),
            },
            ground_truth={
                "true_diagnosis": getattr(case, "true_diagnosis", ""),
                "contraindications": getattr(case, "contraindicated_treatments", getattr(case, "contraindications", [])),
                "optimal_treatment": getattr(case, "optimal_treatment", []),
            },
        )
        report.automated_evaluation = eval_result.model_dump()
        try:
            self.db.save_evaluation(eval_result)
        except Exception as eval_err:
            logger.error(f"Failed to persist report evaluation to database: {eval_err}", exc_info=True)

        # 7. Finalize Encounter
        state.status = "REPORT_READY"
        state.report = report
        self.reports[report.id] = report

        # Persist report to database
        try:
            self.db.save_report(report, case_id=case.id)
        except Exception as db_err:
            logger.error(f"Failed to persist clinical report to database: {db_err}", exc_info=True)

        logger.info(f"Encounter {encounter_id} completed. Report ID: {report.id}. Evaluation Status: {eval_result.final_status.value}")

        return {
            "encounter_id": encounter_id,
            "patient": case.name,
            "chief_complaint": case.chief_complaint,
            "primary_diagnosis": report.primary_diagnosis,
            "confidence": report.diagnostic_confidence,
            "report_id": report.id,
            "report": report.model_dump(),
            "events_count": len(event_bus.get_encounter_events(encounter_id))
        }

    def submit_physician_review(
        self,
        report_id: str,
        physician_name: str,
        diagnosis_grade: str,
        reasoning_grade: str,
        tests_grade: str,
        treatment_grade: str,
        overall_score: int,
        approved: bool,
        notes: str,
        corrected_diagnosis: Optional[str] = None,
        corrected_treatment: Optional[List[str]] = None,
        assessment: Optional[str] = None,
        identified_errors: Optional[List[str]] = None,
        corrected_reasoning: Optional[str] = None,
        corrected_recommendations: Optional[List[str]] = None,
        reviewer_role: Optional[str] = "ATTENDING_PHYSICIAN",
        specialty: Optional[str] = "INTERNAL_MEDICINE",
    ) -> PhysicianReview:
        """Records structured expert physician evaluation and creates dataset entry."""
        if report_id not in self.reports:
            # Check database if not in active memory
            db_rep = self.db.get_report(report_id)
            if db_rep:
                try:
                    self.reports[report_id] = ClinicalReport.model_validate(db_rep)
                except Exception:
                    pass
            if report_id not in self.reports:
                raise ValueError(f"Report {report_id} not found")

        report = self.reports[report_id]

        parsed_assessment = ReviewAssessment.CORRECT
        if assessment:
            try:
                parsed_assessment = ReviewAssessment(assessment)
            except Exception:
                parsed_assessment = ReviewAssessment.CORRECT
        elif not approved or overall_score <= 2:
            parsed_assessment = ReviewAssessment.INCORRECT
        elif overall_score == 3 or corrected_diagnosis or corrected_treatment:
            parsed_assessment = ReviewAssessment.PARTIALLY_CORRECT

        parsed_errors: List[ReviewErrorTaxonomy] = []
        if identified_errors:
            for err in identified_errors:
                try:
                    parsed_errors.append(ReviewErrorTaxonomy(err))
                except Exception:
                    parsed_errors.append(ReviewErrorTaxonomy.OTHER)

        review = PhysicianReview(
            id=f"REV-{uuid.uuid4().hex[:6].upper()}",
            report_id=report_id,
            encounter_id=report.encounter_id,
            physician_name=physician_name,
            reviewer_role=reviewer_role or "ATTENDING_PHYSICIAN",
            specialty=specialty or getattr(report, "specialty", "INTERNAL_MEDICINE"),
            reviewed_at=datetime.utcnow(),
            assessment=parsed_assessment,
            identified_errors=parsed_errors,
            diagnosis_grade=DiagnosisFeedback(diagnosis_grade),
            reasoning_grade=ReasoningFeedback(reasoning_grade),
            tests_grade=TestAppropriatenessFeedback(tests_grade),
            treatment_grade=TreatmentSafetyFeedback(treatment_grade),
            overall_score=overall_score,
            approved=approved,
            corrected_diagnosis=corrected_diagnosis,
            corrected_reasoning=corrected_reasoning,
            corrected_treatment=corrected_treatment,
            corrected_recommendations=corrected_recommendations,
            physician_feedback_notes=notes,
            provenance={
                "source": "HUMAN_PHYSICIAN_REVIEW",
                "model_version": getattr(report, "model_provenance", "google/medgemma-4b"),
                "submitted_at": datetime.utcnow().isoformat(),
            },
        )

        self.reviews[review.id] = review
        if report.encounter_id in self.encounters:
            self.encounters[report.encounter_id].review = review

        # Persist review separately (original clinical_reports is NEVER overwritten)
        try:
            self.db.save_review(review)
            case = get_benchmark_case(report.patient_id)
            if not case:
                case = next((c for c in BENCHMARK_CASES if c.name == report.patient_name), None)

            # Curate and persist TrainingDatasetRecord (immutable 13 fields, deduplicated)
            dataset_curator.process_review_submission(
                report=report,
                review=review,
                case=case,
            )

            # Backward-compatible DPO preference pair generation (strictly manual training)
            if case:
                dpo_pair = DPOPreferenceGenerator.build_preference_pair(report, review, case)
                self.db.save_dpo_pair(dpo_pair)
        except Exception as db_err:
            logger.error(f"Failed to persist physician review/training dataset record: {db_err}", exc_info=True)

        logger.info(f"Physician review recorded for {report_id}. Approved: {approved}, Score: {overall_score}/5")
        return review

    def get_all_reports(self) -> List[Dict[str, Any]]:
        return [r.model_dump() for r in self.reports.values()]

    def get_reviewed_reports(self) -> List[Dict[str, Any]]:
        """Returns all reports that have been evaluated and reviewed by doctors."""
        results = []
        for rev_id, review in self.reviews.items():
            report_dict = self.get_report(review.report_id)
            if report_dict:
                rev_dict = review.model_dump() if hasattr(review, "model_dump") else dict(review)
                results.append({
                    "id": rev_id,
                    "report_id": review.report_id,
                    "encounter_id": review.encounter_id,
                    "physician_name": review.physician_name,
                    "reviewed_at": rev_dict.get("reviewed_at", ""),
                    "diagnosis_grade": getattr(review.diagnosis_grade, "value", str(review.diagnosis_grade)),
                    "reasoning_grade": getattr(review.reasoning_grade, "value", str(review.reasoning_grade)),
                    "tests_grade": getattr(review.tests_grade, "value", str(review.tests_grade)),
                    "treatment_grade": getattr(review.treatment_grade, "value", str(review.treatment_grade)),
                    "overall_score": review.overall_score,
                    "approved": review.approved,
                    "notes": review.physician_feedback_notes,
                    "corrected_diagnosis": review.corrected_diagnosis,
                    "corrected_treatment": review.corrected_treatment,
                    "report": report_dict,
                })
        results.sort(key=lambda x: str(x.get("reviewed_at", "")), reverse=True)
        return results

    def get_pending_reports(self) -> List[Dict[str, Any]]:
        """Returns only unreviewed reports pending physician review."""
        reviewed_report_ids = {rev.report_id for rev in self.reviews.values()}
        return [
            r.model_dump()
            for r in self.reports.values()
            if r.id not in reviewed_report_ids
        ]

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        report = self.reports.get(report_id)
        if report:
            return report.model_dump()
        return self.db.get_report(report_id)

    def get_analytics(self) -> Dict[str, Any]:
        total_reports = max(len(self.reports), self.db.count_reports())
        total_reviews = max(len(self.reviews), self.db.count_reviews())
        approved_count = sum(1 for r in self.reviews.values() if r.approved)
        avg_score = (sum(r.overall_score for r in self.reviews.values()) / max(total_reviews, 1)) if total_reviews > 0 else 0.0

        return {
            "total_encounters": len(self.encounters),
            "total_reports": total_reports,
            "total_reviews": total_reviews,
            "approval_rate": round(approved_count / max(total_reviews, 1) * 100, 1) if total_reviews > 0 else 0.0,
            "average_physician_score": round(avg_score, 2),
            "database_status": self.db.manager.get_status(),
            "available_cases": [
                {"id": c.id, "name": c.name, "age": c.age, "complaint": c.chief_complaint, "acuity": c.triage_acuity.value}
                for c in BENCHMARK_CASES
            ]
        }

    def get_dpo_dataset(self, include_calibrations: bool = True) -> Dict[str, Any]:
        """Compiles DPO preference pairs from physician reviews and benchmark cases."""
        cases_map = {c.id: c for c in BENCHMARK_CASES}
        pairs = DPOPreferenceGenerator.compile_dpo_corpus(
            reports=self.reports,
            reviews=self.reviews,
            cases_map=cases_map,
            include_calibrations=include_calibrations,
        )
        stats = DPOPreferenceGenerator.get_dataset_statistics(pairs)
        return {
            "statistics": stats,
            "pairs": [p.model_dump() for p in pairs],
        }

    def export_dpo_dataset(self, output_path: str = "data/dpo_preference_dataset.jsonl") -> Dict[str, Any]:
        """Exports preference pairs to standard JSONL format for HuggingFace DPOTrainer."""
        import os
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        cases_map = {c.id: c for c in BENCHMARK_CASES}
        pairs = DPOPreferenceGenerator.compile_dpo_corpus(
            reports=self.reports,
            reviews=self.reviews,
            cases_map=cases_map,
            include_calibrations=True,
        )
        count = DPOPreferenceGenerator.export_jsonl(pairs, output_path, merge=True)
        stats = DPOPreferenceGenerator.get_file_statistics(output_path)
        return {
            "exported_count": count,
            "filepath": output_path,
            "statistics": stats,
        }


# Global Orchestrator Singleton
orchestrator = HospitalOrchestrator(enable_gpu=False)
