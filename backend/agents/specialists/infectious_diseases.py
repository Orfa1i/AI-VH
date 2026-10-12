"""
Infectious Diseases Specialist Agent
Personified as Dr. Anthony Mercer, MD, FIDSA (Attending Physician, Infectious Diseases & Antimicrobial Stewardship).
Grounded in Harrison's Infectious Diseases (Fauci & Kasper) with MedGemma reasoning.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...clinical.models import ClinicalReport
from ...llm.medgemma_service import medgemma_service as default_medgemma_service
from ...llm.model_config import get_model_id
from ...simulation.events import HospitalEvent, EventType
from ...simulation.event_bus import event_bus
from ...rag.specialists.infectious_diseases_rag import (
    InfectiousDiseasesRAGAgent,
    EvidenceBrief,
)
from ...clinical.intent import is_clinical_query

logger = logging.getLogger("InfectiousDiseasesSpecialistAgent")


class InfectiousDiseasesSpecialistAgent:
    """
    Infectious Diseases Attending Physician Agent.
    Grounded in Harrison's Infectious Diseases (Fauci & Kasper).
    """

    def __init__(
        self,
        name: str = "Dr. Anthony Mercer, MD, FIDSA",
        medgemma_service: Optional[Any] = None,
        medgemma_service_instance: Optional[Any] = None,
        rag_agent: Optional[InfectiousDiseasesRAGAgent] = None,
    ):
        self.name = name
        self.specialty = "Infectious Diseases"
        self.llm = medgemma_service or medgemma_service_instance or default_medgemma_service
        self.rag_agent = rag_agent or InfectiousDiseasesRAGAgent()
        self.consultation_history: List[Dict[str, Any]] = []
        self.active_evidence_brief: Optional[EvidenceBrief] = None
        logger.info(
            f"{self.name} initialized. Grounded in Harrison's Infectious Diseases."
        )

    async def emit_event(
        self,
        event_type: EventType,
        encounter_id: str,
        patient_id: str,
        summary: str,
        payload: Optional[Dict[str, Any]] = None,
    ):
        event = HospitalEvent(
            id=f"EVT-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            encounter_id=encounter_id,
            patient_id=patient_id,
            sender_agent_id="agent-infectious-diseases",
            department="INFECTIOUS_DISEASES",
            summary=summary,
            payload=payload or {},
        )
        await event_bus.publish(event)

    async def conduct_specialist_consultation(
        self,
        encounter_id: str,
        patient_id: str,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Provides an expert Infectious Diseases formal consult on complex infections and antimicrobial therapy."""
        logger.info(
            f"{self.name} conducting infectious diseases consult for {patient_id}: '{clinical_scenario[:80]}...'"
        )

        # 1. Generate Evidence Brief from Harrison's Infectious Diseases
        brief = self.rag_agent.generate_evidence_brief(
            chief_complaint=clinical_scenario,
            hpi="",
            abnormal_labs=abnormal_labs or [],
        )
        self.active_evidence_brief = brief

        await self.emit_event(
            event_type=EventType.RAG_QUERY_INITIATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} consulted Harrison's Infectious Diseases on: '{clinical_scenario[:70]}'",
            payload={"domain": brief.domain, "query": brief.query},
        )

        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} synthesized Infectious Diseases Evidence Brief with {len(brief.citations)} citations",
            payload={"citations_count": len(brief.citations), "top_citation": brief.citations[0] if brief.citations else None},
        )

        # 2. Synthesize Specialist Consult Note combining Harrison's RAG & MedGemma reasoning
        medgemma_decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=clinical_scenario,
            hpi="",
            vitals_summary="Assessed by Infectious Diseases consult service",
            exam_findings={},
            lab_results=[{"test_type": "Abnormal Labs / Cultures", "values": abnormal_labs or []}],
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
                "antimicrobial_plan": medgemma_decision["treatment_plan"],
            },
            "citations": brief.citations,
            "model_provenance": f"{get_model_id()} + Harrison's Infectious Diseases",
        }

        self.consultation_history.append(consult_result)
        return consult_result

    async def chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Anthony Mercer, MD, FIDSA."""
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
        response["title"] = "Attending Physician, Infectious Diseases & Antimicrobial Stewardship"
        if "telemetry" in response and isinstance(response["telemetry"], dict):
            response["telemetry"]["knowledge_source"] = "Harrison's Infectious Diseases"
        return response

    async def stream_chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Asynchronously streams conversational clinical consultation tokens from Dr. Anthony Mercer."""
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
                chunk["telemetry"]["knowledge_source"] = "Harrison's Infectious Diseases"
            yield chunk

    def determine_diagnostic_workup(
        self,
        chief_complaint: str,
        hpi: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> List[str]:
        """Returns standard infectious diseases laboratory tests and microbiological cultures."""
        tests = [
            "Complete Blood Count (CBC) with differential",
            "Serum Lactate",
            "C-Reactive Protein (CRP) & Procalcitonin",
            "Blood Cultures (2-3 sets from separate sites)",
            "Urinalysis with reflex Urine Culture",
        ]
        complaint_lower = chief_complaint.lower()
        if "cough" in complaint_lower or "sputum" in complaint_lower or "pneumonia" in complaint_lower:
            tests.extend(["Sputum Gram stain and culture", "Legionella and Streptococcus pneumoniae urine antigens", "Chest Radiograph / CT Chest"])
        elif "endocarditis" in complaint_lower or "murmur" in complaint_lower:
            tests.extend(["Transthoracic / Transesophageal Echocardiogram", "ESR and Rheumatoid Factor", "Serial Blood Cultures"])
        elif "fuo" in complaint_lower or "fever of unknown" in complaint_lower:
            tests.extend(["Chest/Abdomen/Pelvis Contrast CT", "HIV 4th Gen Antigen/Antibody", "EBV / CMV / Viral Hepatitis Panel", "ANA / ANCA / Serum Protein Electrophoresis"])
        elif "diarrhea" in complaint_lower or "c diff" in complaint_lower:
            tests.extend(["Clostridioides difficile toxin B PCR & EIA", "Gastrointestinal pathogen PCR panel", "Fecal Calprotectin"])
        return tests
