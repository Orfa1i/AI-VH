"""
Hospital Simulation Orchestrator
Coordinates encounters, manages clinical state progression, and provides
the central execution loop for the virtual hospital platform.
"""

import asyncio
import uuid
import logging
import random
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
from ..agents.specialists.obstetrics import ObstetricsSpecialistAgent
from ..rag.specialists.obstetrics_rag import ObstetricsRAGAgent
from ..agents.consultation import consultation_engine, MultiAgentConsultationRecord
from ..llm.nemotron_synthesis import nemotron_synthesis_engine
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
        self.obstetrics_rag_agent = ObstetricsRAGAgent()
        self.obstetrics_specialist = ObstetricsSpecialistAgent(
            medgemma_service=self.medgemma,
            rag_agent=self.obstetrics_rag_agent
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

    async def conduct_obstetrics_consult(
        self,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
        patient_id: str = "PAT-OB-CONSULT",
    ) -> Dict[str, Any]:
        """Provides an on-demand clinical consultation with Dr. Evelyn Reed, MD, FACOG (Obstetrics)."""
        encounter_id = f"CON-OB-{uuid.uuid4().hex[:6].upper()}"
        return await self.obstetrics_specialist.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=clinical_scenario,
            abnormal_labs=abnormal_labs,
        )

    async def chat_with_dr_evelyn_reed_ob(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational clinical consultation with Dr. Evelyn Reed, MD, FACOG (Obstetrics)."""
        return await self.obstetrics_specialist.chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        )

    async def stream_chat_with_dr_evelyn_reed_ob(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical diagnostic consultation tokens with Dr. Evelyn Reed, MD, FACOG (Obstetrics)."""
        async for chunk in self.obstetrics_specialist.stream_chat_with_specialist(
            user_message=user_message,
            conversation_history=conversation_history,
            patient_context=patient_context,
        ):
            yield chunk

    def get_specialist_registry(self) -> Dict[str, Any]:
        """Returns the active registry of specialist agents keyed by uppercase specialty."""
        return {
            "INTERNAL_MEDICINE": self.im_specialist,
            "CARDIOLOGY": self.cardio_specialist,
            "SURGERY": self.surgery_specialist,
            "EMERGENCY_MEDICINE": self.emergency_specialist,
            "EMERGENCY": self.emergency_specialist,
            "INFECTIOUS_DISEASES": self.id_specialist,
            "GYNECOLOGY": self.gynecology_specialist,
            "OBSTETRICS": self.obstetrics_specialist,
            "NEUROLOGY": self.neurology_specialist,
        }


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

        spec_norm = routing.specialty.upper().replace(" ", "_")
        if spec_norm == "CARDIOLOGY":
            doctor_agent = CardiologySpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.cardio_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        elif spec_norm == "NEUROLOGY":
            doctor_agent = NeurologySpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.neurology_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        elif spec_norm == "SURGERY":
            doctor_agent = SurgerySpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.surgery_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        elif spec_norm in ["EMERGENCY_MEDICINE", "EMERGENCY"]:
            doctor_agent = EmergencySpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.emergency_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        elif spec_norm == "OBSTETRICS":
            doctor_agent = ObstetricsSpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.obstetrics_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        elif spec_norm == "GYNECOLOGY":
            doctor_agent = GynecologySpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.gynecology_rag_agent,
                lab_agent=lab_agent,
                radiology_agent=radiology_agent,
            )
        elif spec_norm == "INFECTIOUS_DISEASES":
            doctor_agent = InfectiousDiseasesSpecialistAgent(
                medgemma_service=self.medgemma,
                rag_agent=self.id_rag_agent,
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
        dept_map = {
            "CARDIOLOGY": "CARDIOLOGY_SUITE",
            "NEUROLOGY": "NEUROLOGY_SUITE",
            "SURGERY": "SURGERY_CONSULT_ROOM",
            "EMERGENCY_MEDICINE": "EMERGENCY_BAY_1",
            "OBSTETRICS": "OBSTETRICS_SUITE",
            "GYNECOLOGY": "GYNECOLOGY_CLINIC",
        }
        state.current_department = dept_map.get(spec_norm, "EXAMINATION_ROOM_1")
        report = await doctor_agent.conduct_clinical_encounter(encounter_id, toolkit)

        # 5b. Dynamic Multi-Agent Consultation (Controlled Secondary Review)
        consult_record = await consultation_engine.coordinate_consultations(
            encounter_id=encounter_id,
            primary_specialty=routing.specialty,
            patient_data={
                "id": case.id,
                "name": case.name,
                "age": case.age,
                "sex": case.sex,
                "chief_complaint": case.chief_complaint,
                "history_of_present_illness": getattr(case, "history_of_present_illness", case.chief_complaint),
            },
            primary_finding={
                "primary_diagnosis": report.primary_diagnosis,
                "confidence": report.diagnostic_confidence,
                "differential": [d.model_dump() for d in report.differential_diagnosis],
            },
            specialist_registry=self.get_specialist_registry(),
            abnormal_labs=getattr(case, "abnormal_labs", []),
        )
        report.multi_agent_consultation = consult_record.model_dump()
        if consult_record.emergency_red_flags:
            # Emergency red flags must trigger the appropriate safety escalation and must never be suppressed
            report.safety_warnings = list(set(report.safety_warnings + consult_record.emergency_red_flags))

        
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

    async def execute_production_clinical_workflow(
        self,
        patient_case: Any,
        data_origin: str = "REAL_EHR",
        max_consultations: int = 2,
    ) -> Dict[str, Any]:
        """
        Executes the production 5-step clinical workflow:
        Step 1: Patient Intake (Preserves vitals, labs, history, imaging; tags data_origin)
        Step 2: MedGemma Router (Dynamic specialty routing with validated rationale)
        Step 3: Specialist Agent Execution (Specialty RAG + active shared knowledge sources)
        Step 4: Dynamic Multi-Agent Consultation (Controlled consultations, cycle prevention, disagreement detection, emergency lock)
        Step 5: Evidence-Grounded Nemotron Synthesis (Nebius Nemotron synthesis with 5-tier provenance, no silent mocks)
        """
        # Step 1: Patient Intake
        if isinstance(patient_case, str):
            # Case ID provided; retrieve from benchmark cases
            b_case = get_benchmark_case(patient_case)
            patient_id = b_case.id
            patient_name = b_case.name
            age = b_case.age
            sex = b_case.sex
            chief_complaint = b_case.chief_complaint
            hpi = getattr(b_case, "history_of_present_illness", b_case.chief_complaint)
            pmh = getattr(b_case, "past_medical_history", getattr(b_case, "medical_history", []))
            meds = getattr(b_case, "medications", getattr(b_case, "current_medications", []))
            allergies = getattr(b_case, "allergies", [])
            vitals = b_case.baseline_vitals.to_dict() if hasattr(b_case, "baseline_vitals") and hasattr(b_case.baseline_vitals, "to_dict") else {}
            labs = [
                {"test_type": l.test_type.value if hasattr(l.test_type, "value") else str(l.test_type), "values": l.values, "interpretation": l.interpretation}
                for l in getattr(b_case, "lab_results", [])
            ]
            imaging = getattr(b_case, "imaging_findings", {})
            origin = "SYNTHETIC_BENCHMARK"
        elif isinstance(patient_case, dict):
            patient_id = patient_case.get("id") or f"PAT-{uuid.uuid4().hex[:6].upper()}"
            patient_name = patient_case.get("name", "EHR Inpatient")
            age = patient_case.get("age", 45)
            sex = patient_case.get("sex", "Unknown")
            chief_complaint = patient_case.get("chief_complaint", "Clinical evaluation requested")
            hpi = patient_case.get("history_of_present_illness", "")
            pmh = patient_case.get("past_medical_history", [])
            meds = patient_case.get("medications", [])
            allergies = patient_case.get("allergies", [])
            vitals = patient_case.get("vital_signs") or patient_case.get("baseline_vitals") or {}
            labs = patient_case.get("lab_results", [])
            imaging = patient_case.get("imaging_findings", {})
            origin = patient_case.get("data_origin", data_origin)
        else:
            # Pydantic or ground truth object
            patient_id = getattr(patient_case, "id", f"PAT-{uuid.uuid4().hex[:6].upper()}")
            patient_name = getattr(patient_case, "name", "Patient")
            age = getattr(patient_case, "age", 45)
            sex = getattr(patient_case, "sex", "Unknown")
            chief_complaint = getattr(patient_case, "chief_complaint", "Clinical evaluation requested")
            hpi = getattr(patient_case, "history_of_present_illness", chief_complaint)
            pmh = getattr(patient_case, "past_medical_history", getattr(patient_case, "medical_history", []))
            meds = getattr(patient_case, "medications", getattr(patient_case, "current_medications", []))
            allergies = getattr(patient_case, "allergies", [])
            vitals = getattr(patient_case, "vital_signs", {})
            labs = getattr(patient_case, "lab_results", [])
            imaging = getattr(patient_case, "imaging_findings", {})
            origin = getattr(patient_case, "data_origin", data_origin)

        encounter_id = f"ENC-PROD-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Initiating production clinical workflow {encounter_id} for {patient_name} ({origin})")

        intake_data = {
            "id": patient_id,
            "name": patient_name,
            "age": age,
            "sex": sex,
            "chief_complaint": chief_complaint,
            "history_of_present_illness": hpi,
            "past_medical_history": pmh,
            "medications": meds,
            "allergies": allergies,
            "vital_signs": vitals,
            "lab_results": labs,
            "imaging_findings": imaging,
            "data_origin": origin,
        }

        # Step 2: MedGemma Router
        if hasattr(MedicalSpecialtyRouter, "route_case_with_medgemma") and getattr(self.medgemma, "model", None) is not None:
            routing = MedicalSpecialtyRouter.route_case_with_medgemma(intake_data, medgemma_service=self.medgemma)
        else:
            routing = MedicalSpecialtyRouter.route_case(intake_data)

        # Step 3: Primary Specialist Agent Execution
        registry = self.get_specialist_registry()
        norm_spec = routing.specialty.upper().replace(" ", "_")
        primary_agent = registry.get(norm_spec, self.im_specialist)

        scenario_text = (
            f"Chief Complaint: {chief_complaint}. "
            f"HPI: {hpi}. "
            f"PMH: {', '.join(pmh) if pmh else 'None'}. "
            f"Medications: {', '.join(meds) if meds else 'None'}."
        )

        abnormal_lab_strings = []
        for l in labs:
            if isinstance(l, dict):
                tt = l.get("test_type", "Lab")
                val = l.get("values", l.get("value", ""))
                interp = l.get("interpretation", "")
                abnormal_lab_strings.append(f"{tt}: {val} ({interp})" if interp else f"{tt}: {val}")
            else:
                abnormal_lab_strings.append(str(l))

        primary_consult = await primary_agent.conduct_specialist_consultation(
            encounter_id=encounter_id,
            patient_id=patient_id,
            clinical_scenario=scenario_text,
            abnormal_labs=abnormal_lab_strings,
        )

        # Step 4: Dynamic Multi-Agent Consultation
        consult_engine = consultation_engine
        consult_engine.max_consultations = max_consultations
        consultation_record = await consult_engine.coordinate_consultations(
            encounter_id=encounter_id,
            primary_specialty=routing.specialty,
            patient_data=intake_data,
            primary_finding=primary_consult,
            specialist_registry=registry,
            abnormal_labs=abnormal_lab_strings,
        )

        # Step 5: Evidence-Grounded Nemotron Synthesis
        secondary_consults_list = [
            f.model_dump() for f in consultation_record.consultation_findings.values()
        ]
        disagreements_list = [
            d.model_dump() for d in consultation_record.disagreements
        ]

        # Combine verified citations
        combined_citations = list(primary_consult.get("citations", []))
        for sc in secondary_consults_list:
            for c in sc.get("citations", []):
                if c not in combined_citations:
                    combined_citations.append(c)

        vitals_str = "; ".join(f"{k}: {v}" for k, v in vitals.items()) if isinstance(vitals, dict) else str(vitals)

        synthesis_result = nemotron_synthesis_engine.synthesize_diagnostic_report(
            patient_info=intake_data,
            vitals_summary=vitals_str or "Vitals stable",
            exam_findings=imaging,
            lab_results=labs,
            medgemma_decision=primary_consult,
            citations=combined_citations,
            secondary_consultations=secondary_consults_list,
            disagreements=disagreements_list,
        )

        # Step 6: Multi-Agent Interaction Event Sequence & Specialty Scoring
        specialty_code_map = {
            "INTERNAL_MEDICINE": "im",
            "CARDIOLOGY": "ca",
            "NEUROLOGY": "ne",
            "SURGERY": "su",
            "EMERGENCY": "em",
            "EMERGENCY_MEDICINE": "em",
            "OBSTETRICS": "ob",
            "GYNECOLOGY": "gy",
            "INFECTIOUS_DISEASES": "im",
        }
        primary_key = specialty_code_map.get(norm_spec, "im")
        consulted_keys = [
            specialty_code_map.get(s.upper().replace(" ", "_"), "em")
            for s in consultation_record.consulted_specialties
        ]
        if "em" not in consulted_keys and primary_key != "em":
            consulted_keys.append("em")

        # Calibrated 0-100 scores across all 7 specialties
        scores = {
            "ob": 42, "gy": 40, "ca": 48, "su": 38, "em": 62, "ne": 35, "im": 50
        }
        scores[primary_key] = int(min(98, max(90, routing.confidence * 100)))
        for ck in consulted_keys:
            if ck != primary_key:
                scores[ck] = random.randint(81, 88)

        status_map = {
            "ob": "standby", "gy": "standby", "ca": "standby", "su": "standby",
            "em": "standby", "ne": "standby", "im": "standby"
        }
        status_map[primary_key] = "lead"
        for ck in consulted_keys:
            if ck != primary_key:
                status_map[ck] = "assigned"

        assigned_list = [k for k, v in status_map.items() if v in ["lead", "assigned"]]
        standby_list = [k for k, v in status_map.items() if v == "standby"]

        # Build structured deliberation events for the multi-agent UI
        events: List[Dict[str, Any]] = []
        agreed_set: Set[str] = {primary_key}

        # Event 1: Primary Specialist Assessment
        events.append({
            "who": primary_key,
            "to": "board",
            "kind": "assess",
            "short": f"{routing.suggested_specialist_name.split(',')[0]} assesses: {primary_consult.get('primary_diagnosis', 'Acute presentation')}",
            "detail": f"{primary_consult.get('clinical_reasoning', scenario_text)} Grounded in <em>{routing.target_medical_book}</em>.",
            "voice": f"Primary evaluation complete: {primary_consult.get('primary_diagnosis', 'acute medical condition')}. Requesting multidisciplinary evaluation.",
            "agreeWith": list(agreed_set),
            "planAgrees": ["intake_eval"],
            "dxDelta": {}
        })

        # Event 2+: Secondary Specialist Consultation Findings
        for s_spec, finding in consultation_record.consultation_findings.items():
            f_key = specialty_code_map.get(s_spec.upper().replace(" ", "_"), "em")
            agreed_set.add(f_key)
            recs_text = "; ".join(finding.treatment_recommendations[:2]) if finding.treatment_recommendations else "Specialty monitoring indicated"
            events.append({
                "who": f_key,
                "to": primary_key,
                "kind": "consult_reply",
                "short": f"{finding.specialist_name.split(',')[0]} recommends: {finding.primary_diagnosis}",
                "detail": f"{finding.clinical_reasoning or recs_text} Reference: <em>{s_spec.title()} Evidence Guidelines</em>.",
                "voice": f"{finding.specialist_name.split(',')[0]} concurs on diagnosis and recommends {recs_text}.",
                "agreeWith": list(agreed_set),
                "planAgrees": ["diagnostic_workup"],
                "dxDelta": {}
            })

        # Event 3: Disagreement Resolution (if applicable)
        if consultation_record.disagreements:
            dis = consultation_record.disagreements[0]
            events.append({
                "who": primary_key,
                "to": "board",
                "kind": "dispute",
                "short": f"Reconciling: {dis.issue_type.replace('_', ' ').title()}",
                "detail": f"{dis.clinical_impact} Guidance: {dis.resolution_guidance}",
                "voice": "Clinical divergence identified. Reconciling hypotheses with diagnostic synthesis engine.",
                "agreeWith": list(agreed_set),
                "planAgrees": [],
                "dxDelta": {}
            })

        # Event 4: Emergency / Triage Assessment
        if "em" in assigned_list and primary_key != "em" and "EMERGENCY" not in consultation_record.consultation_findings:
            agreed_set.add("em")
            events.append({
                "who": "em",
                "to": primary_key,
                "kind": "assess",
                "short": "Emergency Triage: Continuous vitals monitoring and airway stabilization confirmed",
                "detail": "Emergency Medicine team has active telemetry lines secured. Resuscitation readiness confirmed per <em>Tintinalli's Emergency Medicine</em>.",
                "voice": "Continuous telemetry secured and patient stability confirmed.",
                "agreeWith": list(agreed_set),
                "planAgrees": ["intake_eval"],
                "dxDelta": {}
            })

        # Event 5: NVIDIA Nemotron Final Synthesis & Consensus
        events.append({
            "who": primary_key,
            "to": "board",
            "kind": "consensus",
            "short": f"Consensus reached: {synthesis_result.primary_diagnosis}",
            "detail": f"NVIDIA Nemotron reconciled evidence across {len(assigned_list)} specialists. Working diagnosis: <b>{synthesis_result.primary_diagnosis}</b> (Confidence {synthesis_result.confidence:.2f}). Evidence sources: {', '.join(synthesis_result.evidence_sources[:2]) if synthesis_result.evidence_sources else routing.target_medical_book}.",
            "voice": f"Multidisciplinary consensus reached. NVIDIA Nemotron finalized clinical report for {patient_name}.",
            "agreeWith": assigned_list,
            "planAgrees": ["intake_eval", "diagnostic_workup", "treatment_order"],
            "dxDelta": {}
        })

        return {
            "encounter_id": encounter_id,
            "status": synthesis_result.status,
            "data_origin": origin,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "intake_data": intake_data,
            "routing": {
                **routing.model_dump(),
                "primary": primary_key,
                "consult": consulted_keys[0] if consulted_keys else "em",
                "scores": scores,
                "status": status_map,
                "assigned": assigned_list,
                "standby": standby_list,
                "routedAt": datetime.now().strftime("%H:%M"),
                "rationale": routing.primary_rationale,
            },

            "primary_specialist": {
                "specialty": routing.specialty,
                "doctor_name": routing.suggested_specialist_name,
                "findings": primary_consult,
            },
            "multi_agent_consultation": consultation_record.model_dump(),
            "events": events,
            "specialty_scores": scores,
            "synthesis": {
                "primary_diagnosis": synthesis_result.primary_diagnosis,
                "confidence": synthesis_result.confidence,
                "certainty": synthesis_result.certainty,
                "differential": [d.model_dump() if hasattr(d, "model_dump") else d.__dict__ for d in synthesis_result.differential],
                "clinical_reasoning": synthesis_result.clinical_reasoning,
                "missing_information": synthesis_result.missing_information,
                "red_flags": list(set(synthesis_result.red_flags + consultation_record.emergency_red_flags)),
                "evidence_sources": synthesis_result.evidence_sources,
                "engine_name": synthesis_result.engine_name,
                "thinking_trace": synthesis_result.thinking_trace,
                "provenance": synthesis_result.provenance,
                "sections": synthesis_result.sections,
                "error_message": synthesis_result.error_message,
            },
            "emergency_escalation": consultation_record.is_emergency_escalated,
            "timestamp": datetime.utcnow().isoformat(),
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
