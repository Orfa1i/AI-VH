"""
Clinical Tools Implementation
Implements tools callable by Doctor and Nurse agents to interact with patient data,
order laboratory investigations, query medical textbooks, and generate clinical reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .models import VitalSigns, LabTestType, LabResult, ClinicalReport, DifferentialItem
from .cases import PatientGroundTruth, get_benchmark_case
from ..rag.vector_index import MedicalKnowledgeIndex
from ..rag.book_parser import HarrisonParser

logger = logging.getLogger("ClinicalTools")


class ClinicalToolkit:
    def __init__(self, ground_truth: PatientGroundTruth, rag_index: Optional[MedicalKnowledgeIndex] = None):
        self.ground_truth = ground_truth
        if rag_index is None:
            parser = HarrisonParser()
            chunks = parser.load_or_extract_chunks(max_pages_per_chapter=2)
            self.rag_index = MedicalKnowledgeIndex(chunks)
        else:
            self.rag_index = rag_index

        self.ordered_labs: List[LabTestType] = []
        self.lab_results: List[LabResult] = []
        self.interview_transcript: List[Dict[str, str]] = []

    def get_vital_signs(self) -> VitalSigns:
        """Nurse or Doctor checks patient's current vital signs."""
        logger.info(f"Tool called: get_vital_signs for {self.ground_truth.name}")
        return self.ground_truth.baseline_vitals

    def get_patient_history(self) -> Dict[str, Any]:
        """Doctor or Nurse reads the intake medical history."""
        logger.info(f"Tool called: get_patient_history for {self.ground_truth.name}")
        return {
            "name": self.ground_truth.name,
            "age": self.ground_truth.age,
            "sex": self.ground_truth.sex,
            "chief_complaint": self.ground_truth.chief_complaint,
            "history_of_present_illness": self.ground_truth.history_of_present_illness,
            "past_medical_history": self.ground_truth.past_medical_history,
            "medications": self.ground_truth.medications,
            "allergies": self.ground_truth.allergies,
        }

    def perform_physical_exam(self, system: Optional[str] = None) -> Dict[str, str]:
        """Doctor examines organ systems (e.g. Cardiovascular, Pulmonary, Abdomen)."""
        logger.info(f"Tool called: perform_physical_exam ({system or 'Comprehensive'})")
        if system and system in self.ground_truth.physical_exam:
            return {system: self.ground_truth.physical_exam[system]}
        return self.ground_truth.physical_exam

    def order_lab_test(self, test_type: LabTestType) -> LabResult:
        """Doctor orders a clinical laboratory test or diagnostic study."""
        logger.info(f"Tool called: order_lab_test ({test_type.value})")
        self.ordered_labs.append(test_type)

        test_key = test_type.value
        values = self.ground_truth.simulated_labs.get(test_key, {
            "result": "Normal / Non-diagnostic",
            "interpretation": "Within standard clinical parameters"
        })

        # Calculate abnormal flags
        flags = {}
        if "flag" in values:
            flags["primary"] = True
        elif any("elevation" in str(v).lower() or "critical" in str(v).lower() or "depression" in str(v).lower() for v in values.values()):
            flags["primary"] = True

        result = LabResult(
            test_type=test_type,
            values=values,
            abnormal_flags=flags,
            interpretation=values.get("interpretation", "Results processed by clinical laboratory.")
        )
        self.lab_results.append(result)
        return result

    def search_medical_knowledge(self, clinical_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Doctor queries Harrison's Principles of Internal Medicine for evidence-based clinical guidance."""
        logger.info(f"Tool called: search_medical_knowledge ('{clinical_query}')")
        return self.rag_index.search(clinical_query, top_k=top_k)

    def write_clinical_report(
        self,
        encounter_id: str,
        primary_diagnosis: str,
        diagnostic_confidence: float,
        differential: List[DifferentialItem],
        clinical_reasoning: str,
        treatment_plan: List[str],
        citations: List[Dict[str, Any]],
        ungrounded: bool = False,
    ) -> ClinicalReport:
        """Doctor generates the structured clinical report for human physician review."""
        logger.info(f"Tool called: write_clinical_report for encounter {encounter_id}")
        report = ClinicalReport(
            id=f"REP-{encounter_id[-6:]}",
            encounter_id=encounter_id,
            patient_id=self.ground_truth.id,
            patient_name=self.ground_truth.name,
            patient_age=self.ground_truth.age,
            patient_sex=self.ground_truth.sex,
            chief_complaint=self.ground_truth.chief_complaint,
            history_of_present_illness=self.ground_truth.history_of_present_illness,
            past_medical_history=self.ground_truth.past_medical_history,
            medications=self.ground_truth.medications,
            allergies=self.ground_truth.allergies,
            vital_signs=self.ground_truth.baseline_vitals,
            physical_exam_findings=self.ground_truth.physical_exam,
            investigations_ordered=self.ordered_labs,
            investigation_results=self.lab_results,
            differential_diagnosis=differential,
            primary_diagnosis=primary_diagnosis,
            diagnostic_confidence=diagnostic_confidence,
            clinical_reasoning=clinical_reasoning,
            treatment_plan=treatment_plan,
            medical_knowledge_citations=citations,
            ungrounded=ungrounded,
        )
        return report
