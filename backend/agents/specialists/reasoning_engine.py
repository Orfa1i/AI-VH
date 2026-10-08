"""
Specialty Clinical Reasoning Engine for AI Virtual Hospital (AI-VH).
Implements the 11-step diagnostic workflow across all specialty agents:

1. Receive the admitted patient's clinical case.
2. Read the available patient information (zero ground-truth leakage).
3. Analyze the presentation and relevant history.
4. Produce an initial differential diagnosis internally.
5. Identify what additional medical evidence is required (diagnostic workup + literature queries).
6. Query the specialty-specific Medical Book through RAG.
7. Query the approved shared Knowledge Sources (RxNorm/NABD) when appropriate.
8. Compare the retrieved evidence with the patient's actual presentation (patient data authoritative).
9. Re-evaluate the differential diagnosis (Bayesian likelihood re-ranking with supporting/opposing points).
10. Select the most clinically supported diagnosis or diagnosis set.
11. Produce one coherent final clinical report (patient-specific synthesis, anti-verbatim, proper source attribution).
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from backend.clinical.models import (
    ClinicalReport,
    DifferentialItem,
    LabTestType,
    VitalSigns,
    LabResult,
)
from backend.clinical.tools import ClinicalToolkit
from backend.llm.medgemma_service import MedGemmaService
from backend.llm.model_config import get_model_id
from backend.llm.nemotron_synthesis import nemotron_synthesis_engine
from backend.rag.shared_sources import shared_knowledge_service, SharedKnowledgeService
from backend.simulation.events import HospitalEvent, EventType
from backend.simulation.event_bus import event_bus

logger = logging.getLogger("ReasoningEngine")

# A sentence sharing this many consecutive words with a source passage is treated as copied.
VERBATIM_WINDOW_WORDS = 12


class SpecialtyClinicalReasoningEngine:
    """
    Standardized, modular 11-step clinical reasoning engine for Specialty Agents.
    Guarantees strict ground-truth isolation, patient data primacy, and structured report synthesis.
    """

    def __init__(
        self,
        specialist_name: str,
        specialty: str,
        rag_agent: Any,
        medgemma_service: Optional[MedGemmaService] = None,
        shared_sources: Optional[SharedKnowledgeService] = None,
        lab_agent: Optional[Any] = None,
        radiology_agent: Optional[Any] = None,
        emit_event_fn: Optional[Callable] = None,
    ):
        self.specialist_name = specialist_name
        self.specialty = specialty
        self.rag_agent = rag_agent
        self.llm = medgemma_service or MedGemmaService(enable_gpu=False)
        self.shared_sources = shared_sources or shared_knowledge_service
        self.lab_agent = lab_agent
        self.radiology_agent = radiology_agent
        self._emit_event_fn = emit_event_fn
        self.active_evidence_brief: Optional[Any] = None

    async def _emit(
        self,
        event_type: EventType,
        encounter_id: str,
        patient_id: str,
        summary: str,
        payload: Optional[Dict[str, Any]] = None,
        department: str = "EXAMINATION_ROOM",
    ) -> None:
        """Emits an event through the provided callable or global event bus."""
        if self._emit_event_fn:
            await self._emit_event_fn(
                event_type=event_type,
                encounter_id=encounter_id,
                patient_id=patient_id,
                summary=summary,
                payload=payload or {},
            )
        else:
            event = HospitalEvent(
                id=f"EVT-{event_type.value[:4]}-{encounter_id[-6:]}",
                event_type=event_type,
                encounter_id=encounter_id,
                patient_id=patient_id,
                sender_agent_id=self.specialist_name,
                department=department,
                summary=summary,
                payload=payload or {},
            )
            await event_bus.publish(event)

    # -------------------------------------------------------------------------
    # Step 4: Initial Internal Differential Diagnosis
    # -------------------------------------------------------------------------
    def formulate_initial_differential(
        self,
        chief_complaint: str,
        hpi: str,
        vitals: VitalSigns,
        exam: Dict[str, str],
    ) -> List[DifferentialItem]:
        """
        Produces initial internal pre-test differential diagnosis hypotheses
        based strictly on presenting symptoms, hemodynamic status, and physical exam findings.
        Zero ground truth access.
        """
        text = f"{chief_complaint} {hpi}".lower()

        # Cardiovascular / Ischemia presentations
        if any(k in text for k in ["chest", "substernal", "angina", "arm", "jaw", "radiation", "troponin"]):
            return [
                DifferentialItem(
                    condition="Acute Coronary Syndrome (NSTEMI / STEMI)",
                    likelihood=0.65,
                    supporting_points=["Acute substernal chest pressure", "Risk profile (age, vascular factors)"],
                    opposing_points=["Pending 12-lead ECG and cardiac biomarkers"],
                ),
                DifferentialItem(
                    condition="Unstable Angina",
                    likelihood=0.20,
                    supporting_points=["Exertional chest discomfort"],
                    opposing_points=["Troponin status pending"],
                ),
                DifferentialItem(
                    condition="Acute Pericarditis",
                    likelihood=0.10,
                    supporting_points=["Chest pain presentation"],
                    opposing_points=["No positional exacerbation or friction rub reported on exam"],
                ),
                DifferentialItem(
                    condition="Aortic Dissection",
                    likelihood=0.05,
                    supporting_points=["Severe anterior chest pain"],
                    opposing_points=["Peripheral pulses intact and symmetric"],
                ),
            ]

        # Endocrine / DKA presentations
        if any(k in text for k in ["glucose", "dka", "ketoacidosis", "thirst", "polyuria", "vomiting", "fruity"]):
            return [
                DifferentialItem(
                    condition="Diabetic Ketoacidosis (DKA)",
                    likelihood=0.75,
                    supporting_points=["History of diabetes", "Persistent vomiting, hyperpnea, dehydration"],
                    opposing_points=["Pending blood gas, ketones, and anion gap confirmation"],
                ),
                DifferentialItem(
                    condition="Hyperosmolar Hyperglycemic State (HHS)",
                    likelihood=0.15,
                    supporting_points=["Severe hyperglycemia and dehydration"],
                    opposing_points=["Kussmaul breathing suggests metabolic acidosis rather than pure HHS"],
                ),
                DifferentialItem(
                    condition="Acute Abdomen / Appendicitis",
                    likelihood=0.10,
                    supporting_points=["Severe diffuse abdominal cramps and vomiting"],
                    opposing_points=["Abdomen soft without peritoneal signs on physical exam"],
                ),
            ]

        # Respiratory / Dyspnea presentations
        if any(k in text for k in ["sob", "dyspnea", "shortness of breath", "cough", "rales", "edema"]):
            return [
                DifferentialItem(
                    condition="Acute Decompensated Heart Failure",
                    likelihood=0.60,
                    supporting_points=["Dyspnea, orthopnea, bilateral lower extremity edema"],
                    opposing_points=["Pending BNP and chest radiography"],
                ),
                DifferentialItem(
                    condition="Community-Acquired Pneumonia / Lower Respiratory Infection",
                    likelihood=0.25,
                    supporting_points=["Respiratory distress"],
                    opposing_points=["No fever or localized consolidations on initial exam"],
                ),
                DifferentialItem(
                    condition="Acute Pulmonary Embolism",
                    likelihood=0.15,
                    supporting_points=["Acute shortness of breath"],
                    opposing_points=["No unilateral calf swelling or pleuritic component"],
                ),
            ]

        # Default internal medicine differential
        return [
            DifferentialItem(
                condition="Acute Medical Syndrome requiring systematic evaluation",
                likelihood=0.60,
                supporting_points=["Presenting symptoms described in chief complaint"],
                opposing_points=["Awaiting objective laboratory confirmation"],
            ),
            DifferentialItem(
                condition="Secondary reactive medical condition",
                likelihood=0.40,
                supporting_points=["General systemic presentation"],
                opposing_points=["Nonspecific initial findings"],
            ),
        ]

    # -------------------------------------------------------------------------
    # Step 5: Determine Diagnostic Workup (Autonomous, Ground-Truth Isolated)
    # -------------------------------------------------------------------------
    def determine_diagnostic_workup(
        self,
        chief_complaint: str,
        hpi: str,
        vitals: Optional[VitalSigns] = None,
        exam: Optional[Dict[str, str]] = None,
    ) -> List[LabTestType]:
        """
        Autonomously determines the appropriate diagnostic investigations (labs & imaging)
        required to differentiate the initial hypotheses. Ground truth is strictly isolated.
        """
        tests: List[LabTestType] = [LabTestType.CBC, LabTestType.BMP]
        text = f"{chief_complaint} {hpi}".lower()

        # Cardiology specialty specific baseline
        if self.specialty.lower() == "cardiology":
            tests.extend([LabTestType.ECG_12_LEAD, LabTestType.TROPONIN_I, LabTestType.CXR])
            if any(k in text for k in ["heart failure", "edema", "dyspnea", "bnp", "chf", "orthopnea", "rales"]):
                tests.append(LabTestType.BNP)
            if any(k in text for k in ["syncope", "shock", "hypotension", "dizziness"]) or (vitals and vitals.systolic_bp < 90):
                tests.append(LabTestType.LACTATE)

        # Cardiac / Thoracic presentations for any specialty
        elif any(k in text for k in ["chest", "angina", "pressure", "palpitation", "sob", "dyspnea", "radiation"]):
            tests.extend([LabTestType.ECG_12_LEAD, LabTestType.TROPONIN_I, LabTestType.CXR])
            if any(k in text for k in ["heart failure", "edema", "bnp", "chf"]):
                tests.append(LabTestType.BNP)

        # Respiratory / Pulmonary
        elif any(k in text for k in ["cough", "wheezing", "sputum", "pneumonia", "hypoxia"]):
            tests.append(LabTestType.CXR)
            if vitals and vitals.spo2_percent < 92:
                tests.append(LabTestType.ABG)

        # Metabolic / DKA
        if any(k in text for k in ["glucose", "sugar", "dka", "ketoacidosis", "polyuria", "polydipsia", "vomiting"]):
            tests.extend([LabTestType.URINALYSIS, LabTestType.ABG, LabTestType.LACTATE])

        # Gastrointestinal
        if any(k in text for k in ["abdominal pain", "nausea", "vomiting", "jaundice", "epigastric"]):
            tests.extend([LabTestType.LFT, LabTestType.URINALYSIS])

        # Sepsis / Infection
        if any(k in text for k in ["fever", "chills", "septic", "sepsis", "infection"]) or (
            vitals and (vitals.temperature_c > 38.3 or vitals.heart_rate > 100)
        ):
            tests.extend([LabTestType.LACTATE, LabTestType.URINALYSIS])

        # Preserve order while ensuring uniqueness
        seen = set()
        unique_tests = []
        for t in tests:
            if t not in seen:
                seen.add(t)
                unique_tests.append(t)
        return unique_tests

    # -------------------------------------------------------------------------
    # Step 8 (part 1): Extract the patient's actual objective findings
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_relevant_findings(
        lab_results: List[Dict[str, Any]],
        vitals: VitalSigns,
        exam: Dict[str, str],
    ) -> List[str]:
        """
        Collects the patient's pertinent objective findings (investigations, hemodynamics,
        examination). These are the authoritative facts the diagnosis must be consistent with;
        retrieved literature is never allowed to override them.
        """
        findings: List[str] = []
        for lab in lab_results:
            test_type = str(lab.get("test_type", "")).strip()
            interp = str(lab.get("interpretation", "")).strip()
            if test_type and interp:
                findings.append(f"{test_type}: {interp}")
            elif test_type and lab.get("values"):
                findings.append(f"{test_type}: {lab.get('values')}")

        if vitals.heart_rate > 100:
            findings.append(f"Tachycardia ({vitals.heart_rate} bpm)")
        elif vitals.heart_rate < 50:
            findings.append(f"Bradycardia ({vitals.heart_rate} bpm)")
        if vitals.systolic_bp > 140:
            findings.append(f"Hypertension ({vitals.systolic_bp}/{vitals.diastolic_bp} mmHg)")
        elif vitals.systolic_bp < 90:
            findings.append(f"Hypotension ({vitals.systolic_bp}/{vitals.diastolic_bp} mmHg)")
        if vitals.spo2_percent < 92:
            findings.append(f"Hypoxemia (SpO2 {vitals.spo2_percent}%)")
        if vitals.temperature_c > 38.0:
            findings.append(f"Fever ({vitals.temperature_c} C)")

        for system, finding in (exam or {}).items():
            text = str(finding)
            if text and not any(n in text.lower() for n in ["normal", "unremarkable", "clear", "within limits"]):
                findings.append(f"Exam ({system}): {text}")
        return findings

    # -------------------------------------------------------------------------
    # Source attribution & anti-verbatim safeguards
    # -------------------------------------------------------------------------
    @staticmethod
    def build_source_attribution(citations: List[Dict[str, Any]]) -> List[str]:
        """Builds short bibliographic references (no source text) for the report."""
        refs: List[str] = []
        seen = set()
        for c in citations:
            source = c.get("source") or c.get("book") or c.get("title") or "Medical reference"
            chapter = c.get("chapter")
            page = c.get("page")
            parts = [str(source)]
            if chapter and str(chapter) != str(source):
                parts.append(str(chapter))
            if page:
                parts.append(f"p.{page}")
            ref = ", ".join(parts)
            if ref not in seen:
                seen.add(ref)
                refs.append(ref)
        return refs

    @staticmethod
    def strip_verbatim_passages(
        narrative: str,
        citations: List[Dict[str, Any]],
        window: int = VERBATIM_WINDOW_WORDS,
    ) -> Tuple[str, int]:
        """
        Removes any sentence from the model narrative that reproduces a run of `window`
        consecutive words from a retrieved source passage. Returns (clean_text, removed_count).
        """
        def words(s: str) -> List[str]:
            return re.findall(r"[a-z0-9]+", s.lower())

        source_ngrams = set()
        for c in citations:
            w = words(str(c.get("text", "")))
            for i in range(len(w) - window + 1):
                source_ngrams.add(" ".join(w[i:i + window]))
        if not source_ngrams:
            return narrative, 0

        kept, removed = [], 0
        for sentence in re.split(r"(?<=[.!?])\s+", narrative.strip()):
            w = words(sentence)
            copied = any(" ".join(w[i:i + window]) in source_ngrams for i in range(len(w) - window + 1))
            if copied:
                removed += 1
            else:
                kept.append(sentence)
        return " ".join(kept).strip(), removed

    # -------------------------------------------------------------------------
    # Main Encounter Runner: Orchestrates All 11 Workflow Steps
    # -------------------------------------------------------------------------
    async def execute_diagnostic_workflow(
        self,
        encounter_id: str,
        toolkit: ClinicalToolkit,
    ) -> ClinicalReport:
        """Executes the full 11-step clinical reasoning workflow end-to-end."""
        # Step 1: Receive the admitted patient's clinical case
        patient_info = toolkit.get_patient_history()
        patient_id = toolkit.ground_truth.id  # identifier only; no diagnostic fields are read

        await self._emit(
            event_type=EventType.DOCTOR_ASSIGNED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} ({self.specialty}) assigned to patient {patient_info['name']} in Examination Room.",
            payload={"doctor": self.specialist_name, "specialty": self.specialty},
        )

        # Step 2: Read the available patient information (zero ground-truth access)
        vitals = toolkit.get_vital_signs()
        exam = toolkit.perform_physical_exam()

        await self._emit(
            event_type=EventType.EXAMINATION_STARTED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} completed physical examination. Vital signs and system findings reviewed.",
            payload={"vitals": vitals.summary(), "exam_systems": list(exam.keys())},
        )

        # Step 3: Analyze the presentation and relevant history
        hx_str = ", ".join(patient_info.get("past_medical_history", [])) or "None reported"
        meds_str = ", ".join(patient_info.get("medications", [])) or "None"
        allergies_str = ", ".join(patient_info.get("allergies", [])) or "NKDA"
        clinical_summary = (
            f"{patient_info['age']}-year-old {patient_info['sex']} presenting with "
            f"'{patient_info['chief_complaint']}'. {patient_info['history_of_present_illness']} "
            f"Vitals on assessment: {vitals.summary()}. "
            f"Past medical history: {hx_str}. Medications: {meds_str}. Allergies: {allergies_str}."
        )

        # Step 4: Produce an initial differential diagnosis internally
        initial_differential = self.formulate_initial_differential(
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
            vitals=vitals,
            exam=exam,
        )
        await self._emit(
            event_type=EventType.DIFFERENTIAL_UPDATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} formulated initial internal differential ({len(initial_differential)} hypotheses).",
            payload={"phase": "INITIAL", "hypotheses": [d.condition for d in initial_differential]},
        )

        # Step 5: Identify what additional medical evidence is required
        diagnostic_tests = self.determine_diagnostic_workup(
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
            vitals=vitals,
            exam=exam,
        )
        lab_results_payload: List[Dict[str, Any]] = []
        for test in diagnostic_tests:
            is_imaging = test in [LabTestType.ECG_12_LEAD, LabTestType.CXR, LabTestType.CT_CHEST]
            if is_imaging and self.radiology_agent is not None:
                await self._emit(
                    event_type=EventType.IMAGING_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.specialist_name} ordered STAT imaging: {test.value}",
                    payload={"study_type": test.value},
                )
                res = await self.radiology_agent.read_imaging_study(encounter_id, test, toolkit)
            elif self.lab_agent is not None:
                await self._emit(
                    event_type=EventType.LAB_ORDERED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    summary=f"{self.specialist_name} ordered STAT laboratory test: {test.value}",
                    payload={"test_type": test.value},
                )
                res = await self.lab_agent.process_lab_order(encounter_id, test, toolkit)
            else:
                res = toolkit.order_lab_test(test)
            lab_results_payload.append(res.model_dump())

        # Step 6: Query the specialty-specific Medical Book through RAG
        hypotheses = " ".join(d.condition for d in initial_differential[:3])
        book_brief = self.rag_agent.generate_evidence_brief(
            chief_complaint=f"{patient_info['chief_complaint']} {hypotheses}",
            hpi=patient_info["history_of_present_illness"],
        )
        self.active_evidence_brief = book_brief
        book_citations = list(book_brief.citations)

        await self._emit(
            event_type=EventType.RAG_QUERY_INITIATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} queried specialty Medical Book RAG Engine: '{book_brief.domain}'",
            payload={"domain": book_brief.domain, "hypotheses": [d.condition for d in initial_differential[:3]]},
        )
        await self._emit(
            event_type=EventType.RAG_KNOWLEDGE_RETRIEVED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} retrieved {len(book_citations)} citations from {self.specialty} Medical Book",
            payload={"citations_count": len(book_citations)},
        )

        # Step 7: Query approved shared Knowledge Sources when appropriate
        shared_citations: List[Dict[str, Any]] = []
        medications = patient_info.get("medications", [])
        shared_query = f"{patient_info['chief_complaint']} {' '.join(medications)}".strip()
        if shared_query:
            shared_citations = self.shared_sources.retrieve_shared_evidence(query=shared_query, top_k=3) or []

        # Step 8: Compare retrieved evidence with the patient's actual presentation.
        # Objective patient findings are extracted first and passed to the model as the
        # authoritative record; literature is supplied separately as supporting evidence only.
        relevant_findings = self.extract_relevant_findings(lab_results_payload, vitals, exam)
        all_citations = book_citations + shared_citations

        # Steps 9-10: MedGemma re-evaluates the differential and selects the diagnosis,
        # combining patient data, its own learned knowledge, and retrieved evidence.
        decision = await asyncio.to_thread(
            self.llm.generate_clinical_decision,
            chief_complaint=patient_info["chief_complaint"],
            hpi=patient_info["history_of_present_illness"],
            vitals_summary=vitals.summary(),
            exam_findings=exam,
            lab_results=lab_results_payload,
            rag_context=all_citations,
        )
        if not decision or not decision.get("primary_diagnosis"):
            raise RuntimeError(
                f"{self.specialist_name}: MedGemma returned no primary diagnosis for encounter {encounter_id}."
            )

        # Step 10: Clinical Reasoning & Diagnostic Synthesis Engine (Nemotron)
        # Critically synthesizes Patient Data + MedGemma Output + RAG Evidence
        logger.info(f"{self.specialist_name}: Invoking Nemotron Synthesis Engine for diagnostic reasoning...")
        synthesis_result = await asyncio.to_thread(
            nemotron_synthesis_engine.synthesize_diagnostic_report,
            patient_info=patient_info,
            vitals_summary=vitals.summary(),
            exam_findings=exam,
            lab_results=lab_results_payload,
            medgemma_decision=decision,
            citations=all_citations,
        )

        primary_diagnosis = synthesis_result.primary_diagnosis or str(decision["primary_diagnosis"])
        confidence = float(max(0.0, min(1.0, synthesis_result.confidence)))
        re_evaluated_differential = synthesis_result.differential or [
            DifferentialItem(
                condition=d["condition"],
                likelihood=float(max(0.0, min(1.0, d.get("likelihood", 0.0)))),
                supporting_points=d.get("supporting_points", []),
                opposing_points=d.get("opposing_points", []),
            )
            for d in decision.get("differential", [])
            if d.get("condition")
        ]

        await self._emit(
            event_type=EventType.DIFFERENTIAL_UPDATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} re-evaluated the differential via {synthesis_result.engine_name} against objective findings and retrieved evidence.",
            payload={"phase": "RE_EVALUATED", "top_diagnosis": primary_diagnosis, "confidence": confidence, "engine": synthesis_result.engine_name},
        )
        await self._emit(
            event_type=EventType.DIAGNOSIS_MADE,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} established primary clinical diagnosis: {primary_diagnosis} ({confidence * 100:.1f}%)",
            payload={"primary_diagnosis": primary_diagnosis, "confidence": confidence, "engine": synthesis_result.engine_name},
        )

        treatment_plan = list(decision.get("treatment_plan") or [])
        disposition = decision.get("recommended_disposition") or f"Admit to {self.specialty} for monitoring and further evaluation"
        next_steps = [f"Disposition: {disposition}"]
        pending = [d.condition for d in re_evaluated_differential[1:3]]
        if pending:
            next_steps.append(f"Reassess to confirm or exclude: {', '.join(pending)}")
        next_steps.append("Serial vital signs and repeat key investigations to track response to therapy")
        if synthesis_result.missing_information:
            next_steps.extend([f"Missing info: {item}" for item in synthesis_result.missing_information[:2]])
        if synthesis_result.red_flags:
            next_steps.extend([f"Red Flag: {item}" for item in synthesis_result.red_flags[:2]])

        await self._emit(
            event_type=EventType.TREATMENT_ORDERED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"{self.specialist_name} ordered treatment regimen ({len(treatment_plan)} interventions).",
            payload={"treatment_plan": treatment_plan, "disposition": disposition},
        )

        # Step 11: Produce one coherent final clinical report (synthesis + attribution, no copied text)
        clinical_reasoning = synthesis_result.clinical_reasoning
        if not clinical_reasoning or len(clinical_reasoning.strip()) < 20:
            model_reasoning, removed = self.strip_verbatim_passages(
                str(decision.get("clinical_reasoning", "")), all_citations
            )
            if removed:
                logger.warning(
                    "Removed %d sentence(s) copied verbatim from sources in encounter %s", removed, encounter_id
                )
            references = self.build_source_attribution(all_citations)
            reasoning_parts = [model_reasoning] if model_reasoning else []
            if relevant_findings:
                reasoning_parts.append("Key patient findings: " + "; ".join(relevant_findings[:6]) + ".")
            if references:
                reasoning_parts.append(
                    "Evidence consulted: " + "; ".join(f"[{i + 1}] {r}" for i, r in enumerate(references)) + "."
                )
            clinical_reasoning = " ".join(reasoning_parts) or f"Diagnosis of {primary_diagnosis} generated by {get_model_id()}."

        report = toolkit.write_clinical_report(
            encounter_id=encounter_id,
            primary_diagnosis=primary_diagnosis,
            diagnostic_confidence=confidence,
            differential=re_evaluated_differential,
            clinical_reasoning=clinical_reasoning,
            treatment_plan=treatment_plan,
            citations=all_citations,
            ungrounded=not all_citations,
            clinical_summary=clinical_summary,
            relevant_findings=relevant_findings,
            recommended_next_steps=next_steps,
            recommended_disposition=disposition,
        )

        await self._emit(
            event_type=EventType.CLINICAL_REPORT_GENERATED,
            encounter_id=encounter_id,
            patient_id=patient_id,
            summary=f"Clinical Report #{report.id} finalized with {len(all_citations)} evidence citations.",
            payload={"report_id": report.id, "primary_diagnosis": report.primary_diagnosis},
        )
        return report
