"""
Neurology Specialist Agent
Personified as Dr. Alexander Hayes, MD, PhD, FAAN (Attending Neurologist, Comprehensive Stroke Center & Clinical Neurophysiology).
Grounded in Adams and Victor's Principles of Neurology (8th Edition) with MedGemma reasoning.
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
from ...rag.specialists.neurology_rag import (
    NeurologyRAGAgent,
    EvidenceBrief,
)
from ...clinical.intent import is_clinical_query

logger = logging.getLogger("NeurologySpecialistAgent")


class NeurologySpecialistAgent:
    """
    Neurology Attending Physician Agent.
    Grounded in Adams and Victor's Principles of Neurology.
    """

    def __init__(
        self,
        name: str = "Dr. Alexander Hayes, MD, PhD, FAAN",
        medgemma_service: Optional[Any] = None,
        medgemma_service_instance: Optional[Any] = None,
        rag_agent: Optional[NeurologyRAGAgent] = None,
    ):
        self.name = name
        self.specialty = "Neurology"
        self.llm = medgemma_service or medgemma_service_instance or default_medgemma_service
        self.rag_agent = rag_agent or NeurologyRAGAgent()
        self.consultation_history: List[Dict[str, Any]] = []
        self.active_evidence_brief: Optional[EvidenceBrief] = None
        logger.info(
            f"{self.name} initialized. Grounded in Adams and Victor's Principles of Neurology."
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
            sender_agent_id="agent-neurology",
            department="NEUROLOGY",
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
        """Provides an expert Neurology formal consultation on stroke, seizures, neuromuscular disease, and neuro-critical care."""
        logger.info(
            f"{self.name} conducting neurology consult for {patient_id}: '{clinical_scenario[:80]}...'"
        )

        # 1. Generate Evidence Brief from Adams & Victor's Principles of Neurology
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
            summary=f"{self.name} consulted Adams & Victor's Neurology on: '{clinical_scenario[:70]}'",
            payload={"domain": brief.domain, "query": brief.query},
        )

        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} synthesized Neurology Evidence Brief with {len(brief.citations)} citations",
            payload={"citations_count": len(brief.citations), "top_citation": brief.citations[0] if brief.citations else None},
        )

        # 2. Synthesize Specialist Consult Note combining Adams & Victor's RAG & MedGemma reasoning
        medgemma_decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=clinical_scenario,
            hpi="",
            vitals_summary="Assessed by Neurology consult service",
            exam_findings={},
            lab_results=[{"test_type": "Abnormal Labs / Neuroimaging", "values": abnormal_labs or []}],
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
                "neurologic_plan": medgemma_decision["treatment_plan"],
            },
            "citations": brief.citations,
            "model_provenance": f"{get_model_id()} + Adams and Victor's Principles of Neurology",
        }

        self.consultation_history.append(consult_result)
        return consult_result

    async def chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provides direct conversational communication with Dr. Alexander Hayes, MD, PhD, FAAN."""
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
        response["title"] = "Attending Neurologist, Comprehensive Stroke Center & Clinical Neurophysiology"
        if "telemetry" in response and isinstance(response["telemetry"], dict):
            response["telemetry"]["knowledge_source"] = "Adams and Victor's Principles of Neurology (8th Ed)"
        return response

    async def stream_chat_with_specialist(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        """Asynchronously streams conversational clinical consultation tokens from Dr. Alexander Hayes."""
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
                chunk["telemetry"]["knowledge_source"] = "Adams and Victor's Principles of Neurology (8th Ed)"
            yield chunk

    def determine_diagnostic_workup(
        self,
        chief_complaint: str,
        hpi: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> List[str]:
        """Returns standard neurologic laboratory tests, imaging, and neurophysiologic studies."""
        tests = [
            "Non-contrast Head CT STAT",
            "Point-of-care capillary blood glucose",
            "Complete Blood Count (CBC) with differential & Basic Metabolic Panel",
            "12-Lead Electrocardiogram & Continuous telemetry",
        ]
        complaint_lower = chief_complaint.lower()
        if any(w in complaint_lower for w in ["stroke", "ischemic", "tpa", "hemiparesis", "aphasia"]):
            tests.extend([
                "CT Angiography (CTA) of Head and Neck with CT Perfusion",
                "NIH Stroke Scale (NIHSS) standardized score",
                "Coagulation Profile (PT/INR, aPTT, Thrombin Time)",
                "Transthoracic Echocardiogram with bubble study",
                "Lipid Panel & Glycated Hemoglobin (HbA1c)",
                "Brain MRI with Diffusion Weighted Imaging (DWI/ADC)",
            ])
        elif any(w in complaint_lower for w in ["seizure", "epilepsy", "convulsion", "status"]):
            tests.extend([
                "Continuous video-Electroencephalography (vEEG)",
                "Serum Antiepileptic Drug (AED) levels (Phenytoin, Keppra, Valproate)",
                "Serum Magnesium, Phosphorus, Calcium, and venous blood gas",
                "Brain MRI with epilepsy protocol (thin-cut coronal T2/FLAIR of hippocampi)",
            ])
        elif any(w in complaint_lower for w in ["myasthenia", "gbs", "guillain", "weakness"]):
            tests.extend([
                "Forced Vital Capacity (FVC) and Negative Inspiratory Force (NIF) serial monitoring",
                "Serum Acetylcholine Receptor (AChR) Antibodies & Anti-MuSK Antibodies",
                "Repetitive Nerve Stimulation (RNS) and Electromyography (EMG/NCS)",
                "Diagnostic Lumbar Puncture (evaluate albuminocytologic dissociation)",
                "Contrast-enhanced Chest CT (rule out thymoma)",
            ])
        elif any(w in complaint_lower for w in ["headache", "sah", "subarachnoid", "thunderclap"]):
            tests.extend([
                "Emergent Non-contrast Head CT within 6 hours of onset",
                "Diagnostic Lumbar Puncture with opening pressure and CSF spectrophotometry (xanthochromia)",
                "CT Angiography (CTA) or Catheter Digital Subtraction Angiography (DSA)",
                "Erythrocyte Sedimentation Rate (ESR) and CRP if age >= 50 (rule out giant cell arteritis)",
            ])
        elif any(w in complaint_lower for w in ["meningitis", "encephalitis", "fever", "stiff neck"]):
            tests.extend([
                "Diagnostic Lumbar Puncture: CSF cell count, glucose, protein, gram stain, viral PCR panel (HSV/VZV/enterovirus)",
                "Blood cultures x 2 before or concurrently with empiric antibiotics",
                "Contrast-enhanced Brain MRI",
            ])
        return tests
