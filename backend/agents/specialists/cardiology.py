"""
Cardiology Specialist Agent (Dr. Rachel Vance, MD, FACC)
Specialized clinical agent for cardiovascular emergencies, ACS, heart failure, and arrhythmias.
Grounded by Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine (12th Edition)
and powered by the platform-wide shared MedGemma 4B base model.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from ..base import BaseAgent
from ..doctor import DoctorAgent
from ...simulation.events import HospitalEvent, EventType
from ...clinical.models import LabTestType, DifferentialItem, ClinicalReport, VitalSigns
from ...clinical.tools import ClinicalToolkit
from ...llm.medgemma_service import MedGemmaService
from ...llm.model_config import get_model_id
from ...rag.specialists.cardiology_rag import CardiologyRAGAgent, EvidenceBrief
from ...rag.shared_sources import shared_knowledge_service
from ...clinical.intent import is_clinical_query
from .reasoning_engine import SpecialtyClinicalReasoningEngine

logger = logging.getLogger("CardiologyAgent")


class CardiologySpecialistAgent(DoctorAgent):
    def __init__(
        self,
        agent_id: str = "doc_rachel_vance",
        name: str = "Dr. Rachel Vance, MD, FACC",
        medgemma_service: Optional[MedGemmaService] = None,
        rag_agent: Optional[CardiologyRAGAgent] = None,
        lab_agent: Optional[Any] = None,
        radiology_agent: Optional[Any] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="Cardiology",
            medgemma_service=medgemma_service,
            lab_agent=lab_agent,
            radiology_agent=radiology_agent,
        )
        self.rag_agent = rag_agent or CardiologyRAGAgent()
        self.active_evidence_brief: Optional[EvidenceBrief] = None
        self.consultation_history: List[Dict[str, Any]] = []
        self.reasoning_engine = SpecialtyClinicalReasoningEngine(
            specialist_name=self.name,
            specialty=self.specialty,
            rag_agent=self.rag_agent,
            medgemma_service=self.llm,
            shared_sources=shared_knowledge_service,
            lab_agent=self.lab_agent,
            radiology_agent=self.radiology_agent,
            emit_event_fn=self.emit_event,
        )

    async def conduct_specialist_consultation(
        self,
        encounter_id: str,
        patient_id: str,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Provides an expert Cardiology formal consult on any patient scenario."""
        logger.info(f"{self.name} conducting specialist consult for {patient_id}: '{clinical_scenario[:80]}...'")

        # 1. Generate Evidence Brief from Braunwald's Heart Disease
        brief = self.rag_agent.generate_evidence_brief(
            chief_complaint=clinical_scenario,
            abnormal_labs=abnormal_labs or [],
        )
        self.active_evidence_brief = brief

        await self.emit_event(
            event_type=EventType.RAG_QUERY_INITIATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} consulted Braunwald's Heart Disease on: '{clinical_scenario[:70]}'",
            payload={"domain": brief.domain, "query": brief.query},
        )

        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} synthesized Cardiology Evidence Brief with {len(brief.citations)} citations",
            payload={"citations_count": len(brief.citations), "top_citation": brief.citations[0] if brief.citations else None},
        )

        # 2. Synthesize Specialist Consult Note combining Braunwald RAG & MedGemma reasoning
        medgemma_decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=clinical_scenario,
            hpi="",
            vitals_summary="Assessed during cardiology consult",
            exam_findings={},
            lab_results=[{"test_type": "Abnormal Labs", "values": abnormal_labs or []}],
            rag_context=brief.citations,
        )

        consult_result = {
            "specialist": self.name,
            "specialty": self.specialty,
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "clinical_scenario": clinical_scenario,
            "evidence_brief": brief.to_dict(),
            "consult_note": {
                "impression": medgemma_decision["primary_diagnosis"],
                "confidence": medgemma_decision["confidence"],
                "reasoning": medgemma_decision["clinical_reasoning"],
                "differential": medgemma_decision["differential"],
                "cardiac_recommendations": medgemma_decision["treatment_plan"],
            },
            "citations": brief.citations,
            "model_provenance": f"{get_model_id()} + Braunwald's Heart Disease (12th Ed)",
        }

        self.consultation_history.append(consult_result)
        return consult_result

    async def chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Rachel Vance, MD, FACC."""
        logger.info(f"{self.name} received chat message: '{user_message[:80]}...'")

        if is_clinical_query(user_message, patient_context):
            citations = self.rag_agent.retrieve_evidence(user_message, top_k=3)
        else:
            citations = []

        chat_history = conversation_history or []
        chat_history_with_msg = chat_history + [{"role": "user", "content": user_message}]

        response = await asyncio.to_thread(
            self.llm.generate_doctor_chat_response,
            messages=chat_history_with_msg,
            rag_context=citations,
            patient_context=patient_context,
        )
        response["doctor"] = self.name
        response["title"] = "Attending Cardiologist, Cardiovascular Medicine"
        if "telemetry" in response and isinstance(response["telemetry"], dict):
            response["telemetry"]["knowledge_source"] = "Braunwald's Heart Disease (12th Ed)"
        return response

    async def stream_chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Asynchronously streams conversational clinical consultation tokens from Dr. Rachel Vance."""
        logger.info(f"{self.name} streaming chat for message: '{user_message[:80]}...'")
        if is_clinical_query(user_message, patient_context):
            citations = self.rag_agent.retrieve_evidence(user_message, top_k=3)
        else:
            citations = []

        chat_history = conversation_history or []
        chat_history_with_msg = chat_history + [{"role": "user", "content": user_message}]

        async for chunk in self.llm.stream_doctor_chat_response(
            messages=chat_history_with_msg,
            rag_context=citations,
            patient_context=patient_context,
        ):
            if chunk.get("done") and "telemetry" in chunk and isinstance(chunk["telemetry"], dict):
                chunk["telemetry"]["knowledge_source"] = "Braunwald's Heart Disease (12th Ed)"
            yield chunk

    def determine_diagnostic_workup(
        self,
        chief_complaint: str,
        hpi: str,
        vitals: Optional[VitalSigns] = None,
        exam: Optional[Dict[str, str]] = None,
    ) -> List[LabTestType]:
        """
        Autonomously determines the appropriate diagnostic laboratory and imaging workup
        based strictly on clinical presentation, vital signs, and examination findings.
        GROUND TRUTH ISOLATION RULE: Ground truth is never accessed during diagnostic workup.
        """
        return self.reasoning_engine.determine_diagnostic_workup(
            chief_complaint=chief_complaint,
            hpi=hpi,
            vitals=vitals,
            exam=exam,
        )

    async def conduct_clinical_encounter(self, encounter_id: str, toolkit: ClinicalToolkit) -> ClinicalReport:
        """Enhanced encounter runner executing the unified 11-step clinical reasoning workflow."""
        report = await self.reasoning_engine.execute_diagnostic_workflow(
            encounter_id=encounter_id,
            toolkit=toolkit,
        )
        self.active_evidence_brief = getattr(self.reasoning_engine, "active_evidence_brief", None)
        return report

