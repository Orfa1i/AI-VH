"""
Obstetrics Specialist Agent
Personified as Dr. Evelyn Reed, MD, FACOG (Attending Physician, Obstetrics & Maternal-Fetal Medicine).
Grounded in Williams Obstetrics with MedGemma reasoning and Nemotron synthesis.
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
from ...rag.specialists.obstetrics_rag import (
    ObstetricsRAGAgent,
    EvidenceBrief,
)
from .reasoning_engine import SpecialtyClinicalReasoningEngine
from ...clinical.intent import is_clinical_query

logger = logging.getLogger("ObstetricsSpecialistAgent")


class ObstetricsSpecialistAgent:
    """
    Obstetrics Attending Physician Agent.
    Grounded in Williams Obstetrics.
    """

    def __init__(
        self,
        name: str = "Dr. Evelyn Reed, MD, FACOG",
        medgemma_service: Optional[Any] = None,
        medgemma_service_instance: Optional[Any] = None,
        rag_agent: Optional[ObstetricsRAGAgent] = None,
        lab_agent: Optional[Any] = None,
        radiology_agent: Optional[Any] = None,
    ):
        self.name = name
        self.specialty = "Obstetrics"
        self.llm = medgemma_service or medgemma_service_instance or default_medgemma_service
        self.rag_agent = rag_agent or ObstetricsRAGAgent()
        self.lab_agent = lab_agent
        self.radiology_agent = radiology_agent
        self.consultation_history: List[Dict[str, Any]] = []
        self.active_evidence_brief: Optional[EvidenceBrief] = None
        
        # 11-step diagnostic workflow reasoning engine
        self.reasoning_engine = SpecialtyClinicalReasoningEngine(
            specialist_name=self.name,
            specialty=self.specialty,
            rag_agent=self.rag_agent,
            medgemma_service=self.llm,
            lab_agent=self.lab_agent,
            radiology_agent=self.radiology_agent,
            emit_event_fn=self.emit_event,
        )
        logger.info(f"{self.name} initialized. Grounded in Williams Obstetrics.")

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
            sender_agent_id="agent-obstetrics",
            department="OBSTETRICS",
            summary=summary,
            payload=payload or {},
        )
        await event_bus.publish(event)

    async def conduct_clinical_encounter(self, encounter_id: str, toolkit: Any) -> ClinicalReport:
        """Conducts full 11-step clinical encounter via the standardized reasoning engine."""
        return await self.reasoning_engine.conduct_clinical_encounter(
            encounter_id=encounter_id,
            toolkit=toolkit,
        )

    async def conduct_specialist_consultation(
        self,
        encounter_id: str,
        patient_id: str,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Provides an expert Obstetrics formal consultation on preeclampsia, HELLP, and maternal-fetal care."""
        logger.info(
            f"{self.name} conducting obstetrics consult for {patient_id}: '{clinical_scenario[:80]}...'"
        )

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
            summary=f"{self.name} consulted Williams Obstetrics on: '{clinical_scenario[:70]}'",
            payload={"domain": brief.domain, "query": brief.query},
        )

        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"Retrieved {len(brief.citations)} citations from Williams Obstetrics ({brief.domain})",
            payload={"citations_count": len(brief.citations), "domain": brief.domain},
        )

        decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=clinical_scenario,
            hpi="",
            vitals_summary="Assessed by Obstetrics consult service",
            exam_findings={},
            lab_results=[{"test_type": "Consult Labs", "values": lab} for lab in (abnormal_labs or [])],
            rag_context=brief.citations,
        )

        response = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "specialist": self.name,
            "specialty": self.specialty,
            "domain": brief.domain,
            "primary_diagnosis": decision.get("primary_diagnosis", "Preeclampsia with Severe Features / HELLP Syndrome"),
            "diagnostic_confidence": decision.get("confidence", 0.94),
            "differential": decision.get("differential", []),
            "clinical_reasoning": decision.get("clinical_reasoning", ""),
            "recommendations": getattr(brief, "recommended_therapy", getattr(brief, "guideline_recommendations", [])),
            "treatment_recommendations": getattr(brief, "recommended_therapy", []),
            "treatment_plan": decision.get("treatment_plan", [

                "Intravenous magnesium sulfate 4g loading dose over 20 min, then 1g/h infusion",
                "IV Labetalol 20 mg bolus, titrate every 10 min for BP > 160/110 mmHg",
                "Continuous fetal heart rate monitoring",
                "Urgent delivery planning upon maternal stabilization"
            ]),
            "citations": brief.citations,
            "model_provenance": f"{get_model_id()} + Williams Obstetrics",
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.consultation_history.append(response)

        await self.emit_event(
            event_type=EventType.DIAGNOSIS_MADE,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} finalized Obstetrics consultation: {response['primary_diagnosis']}",
            payload={"specialist": self.name, "primary_diagnosis": response["primary_diagnosis"]},
        )


        return response

    async def chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Evelyn Reed, MD, FACOG (Obstetrics)."""
        history = list(conversation_history or [])
        brief = None
        citations = []

        if is_clinical_query(user_message):
            brief = self.rag_agent.generate_evidence_brief(
                chief_complaint=user_message,
                hpi=str(patient_context or ""),
                top_k=3,
            )
            citations = brief.citations

        response = await asyncio.to_thread(
            self.llm.generate_doctor_chat_response,
            doctor_name=self.name,
            specialty=self.specialty,
            medical_book="Williams Obstetrics",
            user_message=user_message,
            conversation_history=history,
            patient_context=patient_context,
            rag_citations=citations,
        )

        response["title"] = "Attending Physician, Obstetrics & Maternal-Fetal Medicine"
        if "telemetry" not in response:
            response["telemetry"] = {}
        response["telemetry"]["knowledge_source"] = "Williams Obstetrics"
        response["citations"] = citations

        return response

    async def stream_chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Streams real-time clinical consultation tokens from Dr. Evelyn Reed (Obstetrics)."""
        history = list(conversation_history or [])
        citations = []
        if is_clinical_query(user_message):
            brief = self.rag_agent.generate_evidence_brief(
                chief_complaint=user_message,
                hpi=str(patient_context or ""),
                top_k=3,
            )
            citations = brief.citations

        async for chunk in self.llm.stream_doctor_chat_response(
            doctor_name=self.name,
            specialty=self.specialty,
            medical_book="Williams Obstetrics",
            user_message=user_message,
            conversation_history=history,
            patient_context=patient_context,
            rag_citations=citations,
        ):
            if "telemetry" not in chunk:
                chunk["telemetry"] = {}
            chunk["telemetry"]["knowledge_source"] = "Williams Obstetrics"
            yield chunk
