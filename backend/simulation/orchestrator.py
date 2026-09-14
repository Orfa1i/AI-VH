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
from ..clinical.models import ClinicalReport, PhysicianReview, DiagnosisFeedback, ReasoningFeedback, TestAppropriatenessFeedback, TreatmentSafetyFeedback
from ..clinical.cases import PatientGroundTruth, get_benchmark_case, BENCHMARK_CASES
from ..clinical.tools import ClinicalToolkit
from ..rag.book_parser import HarrisonParser
from ..rag.vector_index import MedicalKnowledgeIndex
from ..llm.medgemma_service import MedGemmaService
from ..agents.patient import PatientAgent
from ..agents.nurse import NurseAgent
from ..agents.doctor import DoctorAgent
from ..agents.lab import LaboratoryAgent
from ..agents.radiology import RadiologyAgent

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
        
        # Load Harrison's RAG index once
        logger.info("Initializing medical knowledge base from Harrison's Internal Medicine...")
        parser = HarrisonParser()
        chunks = parser.load_or_extract_chunks(max_pages_per_chapter=2)
        self.rag_index = MedicalKnowledgeIndex(chunks)

        # Initialize shared MedGemma service
        self.medgemma = MedGemmaService(enable_gpu=enable_gpu)

    async def run_encounter_simulation(self, case_id: str = "CASE-101") -> Dict[str, Any]:
        """Runs the complete clinical loop from patient arrival to report generation."""
        encounter_id = f"ENC-{uuid.uuid4().hex[:8].upper()}"
        case = get_benchmark_case(case_id)
        state = EncounterState(encounter_id, case)
        self.encounters[encounter_id] = state

        logger.info(f"Starting simulated encounter {encounter_id} for {case.name} ({case.true_diagnosis})")

        # 1. Setup Agents and Toolkit
        toolkit = ClinicalToolkit(ground_truth=case, rag_index=self.rag_index)
        patient_agent = PatientAgent(ground_truth=case)
        nurse_agent = NurseAgent()
        lab_agent = LaboratoryAgent()
        radiology_agent = RadiologyAgent()
        doctor_agent = DoctorAgent(
            medgemma_service=self.medgemma,
            lab_agent=lab_agent,
            radiology_agent=radiology_agent
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

        # 4. Doctor Encounter in Examination Room
        state.status = "EXAMINATION"
        state.current_department = "EXAMINATION_ROOM_1"
        report = await doctor_agent.conduct_clinical_encounter(encounter_id, toolkit)
        
        # 5. Finalize Encounter
        state.status = "REPORT_READY"
        state.report = report
        self.reports[report.id] = report
        logger.info(f"Encounter {encounter_id} completed. Report ID: {report.id}")

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
    ) -> PhysicianReview:
        """Records structured expert physician evaluation and creates dataset entry."""
        if report_id not in self.reports:
            raise ValueError(f"Report {report_id} not found")

        report = self.reports[report_id]
        review = PhysicianReview(
            id=f"REV-{uuid.uuid4().hex[:6].upper()}",
            report_id=report_id,
            encounter_id=report.encounter_id,
            physician_name=physician_name,
            reviewed_at=datetime.utcnow(),
            diagnosis_grade=DiagnosisFeedback(diagnosis_grade),
            reasoning_grade=ReasoningFeedback(reasoning_grade),
            tests_grade=TestAppropriatenessFeedback(tests_grade),
            treatment_grade=TreatmentSafetyFeedback(treatment_grade),
            overall_score=overall_score,
            approved=approved,
            corrected_diagnosis=corrected_diagnosis,
            corrected_treatment=corrected_treatment,
            physician_feedback_notes=notes,
        )

        self.reviews[review.id] = review
        if report.encounter_id in self.encounters:
            self.encounters[report.encounter_id].review = review

        logger.info(f"Physician review recorded for {report_id}. Approved: {approved}, Score: {overall_score}/5")
        return review

    def get_all_reports(self) -> List[Dict[str, Any]]:
        return [r.model_dump() for r in self.reports.values()]

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        report = self.reports.get(report_id)
        return report.model_dump() if report else None

    def get_analytics(self) -> Dict[str, Any]:
        total_reports = len(self.reports)
        total_reviews = len(self.reviews)
        approved_count = sum(1 for r in self.reviews.values() if r.approved)
        avg_score = (sum(r.overall_score for r in self.reviews.values()) / max(total_reviews, 1)) if total_reviews > 0 else 0.0

        return {
            "total_encounters": len(self.encounters),
            "total_reports": total_reports,
            "total_reviews": total_reviews,
            "approval_rate": round(approved_count / max(total_reviews, 1) * 100, 1) if total_reviews > 0 else 0.0,
            "average_physician_score": round(avg_score, 2),
            "available_cases": [
                {"id": c.id, "name": c.name, "age": c.age, "complaint": c.chief_complaint, "acuity": c.triage_acuity.value}
                for c in BENCHMARK_CASES
            ]
        }


# Global Orchestrator Singleton
orchestrator = HospitalOrchestrator(enable_gpu=False)
