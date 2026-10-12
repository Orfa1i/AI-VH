"""
Doctor Agent Definition (Internal Medicine Attending Physician)
Employs the MedGemma foundation model and Harrison's Internal Medicine RAG
to conduct patient interviews, physical exams, diagnostic workups, and clinical reporting.
"""

from typing import Dict, List, Any, Optional
import logging
from .base import BaseAgent
from ..simulation.events import HospitalEvent, EventType
from ..clinical.tools import ClinicalToolkit
from ..clinical.models import DifferentialItem, ClinicalReport, LabTestType
from ..llm.medgemma_service import MedGemmaService
from ..llm.nemotron_synthesis import nemotron_synthesis_engine

logger = logging.getLogger("DoctorAgent")


class DoctorAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str = "doc_marcus",
        name: str = "Dr. Marcus Vance, MD",
        specialty: str = "Internal Medicine",
        medgemma_service: Optional[MedGemmaService] = None,
        lab_agent: Optional[Any] = None,
        radiology_agent: Optional[Any] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role="ATTENDING_PHYSICIAN",
            department="DOCTOR_STATION"
        )
        self.specialty = specialty
        self.llm = medgemma_service or MedGemmaService(enable_gpu=False)
        self.lab_agent = lab_agent
        self.radiology_agent = radiology_agent

    async def conduct_clinical_encounter(self, encounter_id: str, toolkit: ClinicalToolkit) -> ClinicalReport:
        patient_info = toolkit.get_patient_history()
        patient_id = toolkit.ground_truth.id

        # 1. Doctor Assigned & Starts Examination
        await self.emit_event(
            event_type=EventType.DOCTOR_ASSIGNED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} ({self.specialty}) entered Examination Room 1 for patient {patient_info['name']}",
            payload={"doctor": self.name, "specialty": self.specialty}
        )

        # 2. Targeted Physical Examination
        exam = toolkit.perform_physical_exam()
        await self.emit_event(
            event_type=EventType.EXAMINATION_STARTED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} completed physical examination. Findings noted in CV and pulmonary systems.",
            payload={"exam_summary": f"General: {exam.get('General', '')}; CV: {exam.get('Cardiovascular', '')}"}
        )

        # 3. Evidence-based Medical Knowledge Lookup (Harrison's 21st Ed RAG)
        rag_query = f"{patient_info['chief_complaint']} differential diagnosis evaluation"
        await self.emit_event(
            event_type=EventType.RAG_QUERY_INITIATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} querying Harrison's Principles of Internal Medicine for: '{rag_query}'",
            payload={"query": rag_query}
        )
        rag_citations = toolkit.search_medical_knowledge(rag_query, top_k=3)
        await self.emit_event(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} retrieved {len(rag_citations)} clinical evidence passages from Harrison's (Top chapter: {rag_citations[0]['chapter'] if rag_citations else 'N/A'})",
            payload={"citations_count": len(rag_citations), "top_citation": rag_citations[0] if rag_citations else None}
        )

        # 4. Diagnostic Investigations Ordering (Delegated to Lab & Radiology agents)
        # GROUND TRUTH ISOLATION: workup is derived from the presentation, never from
        # toolkit.ground_truth.recommended_labs.
        from .specialists.reasoning_engine import SpecialtyClinicalReasoningEngine

        recommended_tests = SpecialtyClinicalReasoningEngine(
            specialist_name=self.name, specialty=self.specialty, rag_agent=None, medgemma_service=self.llm
        ).determine_diagnostic_workup(
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
            vitals=toolkit.get_vital_signs(),
            exam=exam,
        )
        lab_results_payload = []

        for test in recommended_tests:
            is_imaging = test in [LabTestType.ECG_12_LEAD, LabTestType.CXR, LabTestType.CT_CHEST]
            
            if is_imaging and self.radiology_agent is not None:
                await self.emit_event(
                    event_type=EventType.IMAGING_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.name} ordered STAT imaging: {test.value}",
                    payload={"study_type": test.value}
                )
                result = await self.radiology_agent.read_imaging_study(encounter_id, test, toolkit)
            elif self.lab_agent is not None:
                await self.emit_event(
                    event_type=EventType.LAB_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.name} ordered STAT laboratory test: {test.value}",
                    payload={"test_type": test.value}
                )
                result = await self.lab_agent.process_lab_order(encounter_id, test, toolkit)
            else:
                await self.emit_event(
                    event_type=EventType.LAB_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.name} ordered STAT: {test.value}",
                    payload={"test_type": test.value}
                )
                result = toolkit.order_lab_test(test)
                await self.emit_event(
                    event_type=EventType.LAB_RESULT_READY,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"Laboratory returned results for {test.value}: {result.interpretation}",
                    payload={"test_type": test.value, "values": result.values, "interpretation": result.interpretation}
                )

            lab_results_payload.append(result.model_dump())

        # 5. MedGemma Foundation Model Clinical Synthesis
        vitals = toolkit.get_vital_signs()
        decision = self.llm.generate_clinical_decision(
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
            vitals_summary=vitals.summary(),
            exam_findings=exam,
            lab_results=lab_results_payload,
            rag_context=rag_citations,
        )

        # 5b. Clinical Reasoning & Diagnostic Synthesis Engine (Nemotron)
        # Synthesizes Patient Data + MedGemma Output + RAG Evidence
        synthesis_result = nemotron_synthesis_engine.synthesize_diagnostic_report(
            patient_info=patient_info,
            vitals_summary=vitals.summary(),
            exam_findings=exam,
            lab_results=lab_results_payload,
            medgemma_decision=decision,
            citations=rag_citations,
        )

        primary_diagnosis = synthesis_result.primary_diagnosis or decision.get("primary_diagnosis", "Clinical Presentation")
        confidence = float(max(0.0, min(1.0, synthesis_result.confidence)))

        # Convert differential items
        diff_items = synthesis_result.differential or [
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
            summary=f"{self.name} established primary diagnosis via {synthesis_result.engine_name}: {primary_diagnosis} (Confidence: {confidence * 100:.1f}%)",
            payload={
                "primary_diagnosis": primary_diagnosis,
                "confidence": confidence,
                "differential_count": len(diff_items),
                "engine": synthesis_result.engine_name,
            }
        )

        # 7. Treatment Ordered Event
        await self.emit_event(
            event_type=EventType.TREATMENT_ORDERED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.name} ordered guideline-directed treatment regimen ({len(decision['treatment_plan'])} interventions)",
            payload={"treatment_plan": decision["treatment_plan"], "disposition": decision.get("recommended_disposition", "")}
        )

        # 8. Clinical Report Generation
        clinical_reasoning = synthesis_result.clinical_reasoning or decision.get("clinical_reasoning", "")
        report = toolkit.write_clinical_report(
            encounter_id=encounter_id,
            primary_diagnosis=primary_diagnosis,
            diagnostic_confidence=confidence,
            differential=diff_items,
            clinical_reasoning=clinical_reasoning,
            treatment_plan=decision["treatment_plan"],
            citations=rag_citations,
        )

        await self.emit_event(
            event_type=EventType.CLINICAL_REPORT_GENERATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"Clinical Report #{report.id} generated and queued for Attending Physician review",
            payload={"report_id": report.id, "primary_diagnosis": report.primary_diagnosis}
        )

        return report

    async def process_event(self, event: HospitalEvent):
        pass
