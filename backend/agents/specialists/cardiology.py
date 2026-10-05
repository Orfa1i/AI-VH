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
from ...clinical.models import LabTestType, DifferentialItem, ClinicalReport
from ...clinical.tools import ClinicalToolkit
from ...llm.medgemma_service import MedGemmaService
from ...rag.specialists.cardiology_rag import CardiologyRAGAgent, EvidenceBrief
from ...clinical.intent import is_clinical_query

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
            "model_provenance": "google/medgemma-4b + Braunwald's Heart Disease (12th Ed)",
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
            yield chunk

    async def conduct_clinical_encounter(self, encounter_id: str, toolkit: ClinicalToolkit) -> ClinicalReport:
        """Cardiology encounter runner integrating Braunwald's RAG and MedGemma synthesis."""
        patient_info = toolkit.get_patient_history()
        patient_id = toolkit.ground_truth.id

        # 1. Doctor Assigned & Starts Examination
        await self.emit_event(
            event_type=EventType.DOCTOR_ASSIGNED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} ({self.specialty}) entered Examination Room for patient {patient_info['name']}",
            payload={"doctor": self.name, "specialty": self.specialty},
        )

        # 2. Targeted Cardiovascular Physical Examination
        exam = toolkit.perform_physical_exam()
        await self.emit_event(
            event_type=EventType.EXAMINATION_STARTED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} completed cardiovascular and systemic physical examination.",
            payload={"exam_summary": f"CV: {exam.get('Cardiovascular', 'Normal S1/S2')}; Resp: {exam.get('Respiratory', 'Clear')}"},
        )

        # 3. Query Braunwald's Specialist RAG Agent
        evidence_brief = self.rag_agent.generate_evidence_brief(
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
        )
        self.active_evidence_brief = evidence_brief

        await self.emit_event(
            event_type=EventType.RAG_QUERY_INITIATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} queried Braunwald's Heart Disease Knowledge Engine: '{evidence_brief.domain}'",
            payload={"domain": evidence_brief.domain},
        )

        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} retrieved {len(evidence_brief.citations)} citations from Braunwald's Heart Disease",
            payload={"citations_count": len(evidence_brief.citations), "top_citation": evidence_brief.citations[0] if evidence_brief.citations else None},
        )

        # 4. Diagnostic Investigations Ordering (Agent-directed based on clinical presentation)
        # Note: We will complete full ground truth isolation in Phase 3
        cardiac_workup = [LabTestType.ECG_12_LEAD, LabTestType.TROPONIN_I, LabTestType.BMP, LabTestType.CBC, LabTestType.CXR]
        lab_results_payload = []

        for test in cardiac_workup:
            is_imaging = test in [LabTestType.ECG_12_LEAD, LabTestType.CXR, LabTestType.CT_CHEST]
            if is_imaging and self.radiology_agent is not None:
                await self.emit_event(
                    event_type=EventType.IMAGING_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.name} ordered STAT cardiovascular study: {test.value}",
                    payload={"study_type": test.value},
                )
                result = await self.radiology_agent.read_imaging_study(encounter_id, test, toolkit)
            elif self.lab_agent is not None:
                await self.emit_event(
                    event_type=EventType.LAB_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.name} ordered STAT laboratory test: {test.value}",
                    payload={"test_type": test.value},
                )
                result = await self.lab_agent.process_lab_order(encounter_id, test, toolkit)
            else:
                result = toolkit.order_lab_test(test)

            lab_results_payload.append(result.model_dump())

        # 5. MedGemma Foundation Model Clinical Synthesis
        vitals = toolkit.get_vital_signs()
        decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
            vitals_summary=vitals.summary(),
            exam_findings=exam,
            lab_results=lab_results_payload,
            rag_context=evidence_brief.citations,
        )

        diff_items = [
            DifferentialItem(
                condition=d["condition"],
                likelihood=d["likelihood"],
                supporting_points=d.get("supporting_points", []),
                opposing_points=d.get("opposing_points", []),
            )
            for d in decision.get("differential", [])
        ]

        # 6. Diagnosis Made Event
        await self.emit_event(
            event_type=EventType.DIAGNOSIS_MADE,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} established primary diagnosis: {decision['primary_diagnosis']} (Confidence: {decision['confidence'] * 100:.1f}%)",
            payload={
                "primary_diagnosis": decision["primary_diagnosis"],
                "confidence": decision["confidence"],
                "differential_count": len(diff_items),
            },
        )

        # 7. Treatment Ordered Event
        await self.emit_event(
            event_type=EventType.TREATMENT_ORDERED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} ordered guideline-directed cardiovascular regimen ({len(decision['treatment_plan'])} interventions)",
            payload={"treatment_plan": decision["treatment_plan"], "disposition": decision.get("recommended_disposition", "")},
        )

        # 8. Clinical Report Generation with Braunwald's Provenance
        report = toolkit.write_clinical_report(
            encounter_id=encounter_id,
            primary_diagnosis=decision["primary_diagnosis"],
            diagnostic_confidence=decision["confidence"],
            differential=diff_items,
            clinical_reasoning=decision["clinical_reasoning"],
            treatment_plan=decision["treatment_plan"],
            citations=evidence_brief.citations,
            ungrounded=False,
        )

        await self.emit_event(
            event_type=EventType.CLINICAL_REPORT_GENERATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"Clinical Report #{report.id} finalized with Braunwald's Heart Disease citations and queued for review",
            payload={"report_id": report.id, "primary_diagnosis": report.primary_diagnosis},
        )

        return report
