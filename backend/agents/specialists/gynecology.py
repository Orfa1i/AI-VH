"""
Gynecology Specialist Agent
Personified as Dr. Evelyn Reed, MD, FACOG (Attending Physician, Gynecology & Minimally Invasive Pelvic Surgery).
Grounded in Williams Gynecology with MedGemma reasoning.
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
from ...rag.specialists.gynecology_rag import (
    GynecologyRAGAgent,
    EvidenceBrief,
)
from ...clinical.intent import is_clinical_query

logger = logging.getLogger("GynecologySpecialistAgent")


class GynecologySpecialistAgent:
    """
    Gynecology Attending Physician Agent.
    Grounded in Williams Gynecology.
    """

    def __init__(
        self,
        name: str = "Dr. Evelyn Reed, MD, FACOG",
        medgemma_service: Optional[Any] = None,
        medgemma_service_instance: Optional[Any] = None,
        rag_agent: Optional[GynecologyRAGAgent] = None,
    ):
        self.name = name
        self.specialty = "Gynecology"
        self.llm = medgemma_service or medgemma_service_instance or default_medgemma_service
        self.rag_agent = rag_agent or GynecologyRAGAgent()
        self.consultation_history: List[Dict[str, Any]] = []
        self.active_evidence_brief: Optional[EvidenceBrief] = None
        logger.info(
            f"{self.name} initialized. Grounded in Williams Gynecology."
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
            sender_agent_id="agent-gynecology",
            department="GYNECOLOGY",
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
        """Provides an expert Gynecology formal consultation on pelvic pathology, bleeding, and surgical management."""
        logger.info(
            f"{self.name} conducting gynecology consult for {patient_id}: '{clinical_scenario[:80]}...'"
        )

        # 1. Generate Evidence Brief from Williams Gynecology
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
            summary=f"{self.name} consulted Williams Gynecology on: '{clinical_scenario[:70]}'",
            payload={"domain": brief.domain, "query": brief.query},
        )

        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} synthesized Gynecology Evidence Brief with {len(brief.citations)} citations",
            payload={"citations_count": len(brief.citations), "top_citation": brief.citations[0] if brief.citations else None},
        )

        # 2. Synthesize Specialist Consult Note combining Williams Gynecology RAG & MedGemma reasoning
        medgemma_decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=clinical_scenario,
            hpi="",
            vitals_summary="Assessed by Gynecology consult service",
            exam_findings={},
            lab_results=[{"test_type": "Abnormal Labs / Pelvic Imaging", "values": abnormal_labs or []}],
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
                "gynecologic_plan": medgemma_decision["treatment_plan"],
            },
            "citations": brief.citations,
            "model_provenance": f"{get_model_id()} + Williams Gynecology",
        }

        self.consultation_history.append(consult_result)
        return consult_result

    async def chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Evelyn Reed, MD, FACOG."""
        logger.info(f"{self.name} received chat message: '{user_message[:80]}...'")

        ctx = dict(patient_context or {})
        ctx.setdefault("attendingDoctor", self.name)
        ctx.setdefault("specialty", self.specialty)

        if is_clinical_query(user_message, ctx):
            citations = self.rag_agent.retrieve_evidence(user_message, top_k=3)
        else:
            citations = []

        chat_history = conversation_history or []
        chat_history_with_msg = chat_history + [{"role": "user", "content": user_message}]

        response = await asyncio.to_thread(
            self.llm.generate_doctor_chat_response,
            messages=chat_history_with_msg,
            rag_context=citations,
            patient_context=ctx,
        )
        response["doctor"] = self.name
        response["title"] = "Attending Physician, Gynecology & Minimally Invasive Pelvic Surgery"
        if "telemetry" in response and isinstance(response["telemetry"], dict):
            response["telemetry"]["knowledge_source"] = "Williams Gynecology"
        return response

    async def stream_chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Asynchronously streams conversational clinical consultation tokens from Dr. Evelyn Reed."""
        logger.info(f"{self.name} streaming chat for message: '{user_message[:80]}...'")
        ctx = dict(patient_context or {})
        ctx.setdefault("attendingDoctor", self.name)
        ctx.setdefault("specialty", self.specialty)

        if is_clinical_query(user_message, ctx):
            citations = self.rag_agent.retrieve_evidence(user_message, top_k=3)
        else:
            citations = []

        chat_history = conversation_history or []
        chat_history_with_msg = chat_history + [{"role": "user", "content": user_message}]

        async for chunk in self.llm.stream_doctor_chat_response(
            messages=chat_history_with_msg,
            rag_context=citations,
            patient_context=ctx,
        ):
            if chunk.get("done") and "telemetry" in chunk and isinstance(chunk["telemetry"], dict):
                chunk["telemetry"]["knowledge_source"] = "Williams Gynecology"
            yield chunk

    def determine_diagnostic_workup(
        self,
        chief_complaint: str,
        hpi: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> List[str]:
        """Returns standard gynecologic laboratory tests, imaging, and procedures."""
        tests = [
            "Urine Pregnancy Test / Serum Quantitative beta-hCG",
            "Complete Blood Count (CBC) with differential",
            "Transvaginal and Transabdominal Pelvic Ultrasound",
            "Urinalysis with reflex culture",
        ]
        complaint_lower = chief_complaint.lower()
        if "bleeding" in complaint_lower or "aub" in complaint_lower or "menorrhagia" in complaint_lower:
            tests.extend([
                "Coagulation Profile (PT/INR, PTT, Fibrinogen)",
                "Serum Ferritin & Iron Studies",
                "Endometrial Biopsy (Pipelle) if age >= 45 or high-risk for hyperplasia",
                "Saline Infusion Sonohysterography (SIS) or Diagnostic Hysteroscopy",
                "Thyroid Stimulating Hormone (TSH) & Prolactin",
            ])
        elif "ectopic" in complaint_lower or "pregnancy" in complaint_lower:
            tests.extend([
                "Serial Quantitative beta-hCG (repeat at 48 hours)",
                "Type and Rh Screen (for Rh D immunoglobulin if indicated)",
                "Hepatic and Renal function panels (baseline prior to methotrexate)",
                "Urgent Pelvic Ultrasound with Doppler evaluation of adnexa",
            ])
        elif "pid" in complaint_lower or "discharge" in complaint_lower or "pelvic inflammatory" in complaint_lower:
            tests.extend([
                "Cervical NAAT for Chlamydia trachomatis & Neisseria gonorrhoeae",
                "Wet Mount & Vaginal pH (Trichomonas, Bacterial Vaginosis, Candida)",
                "C-Reactive Protein (CRP) & Erythrocyte Sedimentation Rate (ESR)",
                "HIV and Syphilis (RPR/Treponemal) Serology",
            ])
        elif "mass" in complaint_lower or "cyst" in complaint_lower or "adnexal" in complaint_lower:
            tests.extend([
                "Pelvic Ultrasound with Color Doppler (assess vascular resistance & mural nodules)",
                "Serum Tumor Markers (CA-125, HE4, ROMA score if postmenopausal)",
                "Pelvic Magnetic Resonance Imaging (MRI) with contrast",
            ])
        elif "endometriosis" in complaint_lower or "dysmenorrhea" in complaint_lower or "pain" in complaint_lower:
            tests.extend([
                "High-resolution Pelvic Transvaginal Ultrasound with bowel/bladder sliding sign",
                "Pelvic MRI for deep infiltrating endometriosis (DIE)",
                "CA-125 (supportive biomarker)",
            ])
        return tests
