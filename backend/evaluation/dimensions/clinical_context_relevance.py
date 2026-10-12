"""
Dimension 1: Clinical Context Relevance Evaluator
Verifies whether the diagnosis and report actually correspond to the patient's
presented clinical information (demographics, chief complaint, HPI, and acute syndrome).
"""

from typing import Dict, Any, Optional, List
import re
from .base import BaseDimensionEvaluator
from ..models import DimensionEvaluationResult, EvaluationSeverity


class ClinicalContextRelevanceEvaluator(BaseDimensionEvaluator):
    dimension_id = "clinical_context_relevance"
    display_name = "Clinical Context Relevance"
    weight = 1.0

    def _evaluate_internal(
        self,
        report: Dict[str, Any],
        patient_presentation: Dict[str, Any],
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> DimensionEvaluationResult:
        detected_issues: List[str] = []
        evidence_records: List[Dict[str, Any]] = []
        deductions = 0.0

        # 1. Demographic consistency check
        expected_age = patient_presentation.get("age")
        report_age = report.get("patient_age")
        if expected_age is not None and report_age is not None:
            if expected_age != report_age:
                detected_issues.append(f"Demographic mismatch: Report age ({report_age}) does not match patient age ({expected_age}).")
                deductions += 0.2
                evidence_records.append({"type": "age_mismatch", "expected": expected_age, "found": report_age})

        expected_sex = str(patient_presentation.get("sex", "")).lower()
        report_sex = str(report.get("patient_sex", "")).lower()
        if expected_sex and report_sex and expected_sex != report_sex:
            detected_issues.append(f"Demographic mismatch: Report sex ({report_sex}) does not match patient record ({expected_sex}).")
            deductions += 0.2
            evidence_records.append({"type": "sex_mismatch", "expected": expected_sex, "found": report_sex})

        # 2. Chief complaint correspondence
        chief_complaint = str(patient_presentation.get("chief_complaint", "")).strip().lower()
        hpi = str(patient_presentation.get("history_of_present_illness", "")).strip().lower()
        presentation_corpus = f"{chief_complaint} {hpi}"

        primary_dx = str(report.get("primary_diagnosis", "")).strip().lower()
        clinical_summary = str(report.get("clinical_summary", "")).strip().lower()
        clinical_reasoning = str(report.get("clinical_reasoning", "")).strip().lower()
        report_corpus = f"{primary_dx} {clinical_summary} {clinical_reasoning}"

        if not primary_dx or primary_dx == "undifferentiated acute medical illness":
            detected_issues.append("Primary diagnosis is absent or an uncommitted generic placeholder.")
            deductions += 0.5
            evidence_records.append({"type": "uncommitted_diagnosis", "found": report.get("primary_diagnosis")})

        # Check keyword semantic overlap between presentation and report
        presentation_tokens = set(re.findall(r"\b[a-z]{4,}\b", presentation_corpus))
        # Remove common non-specific filler words
        stop_words = {"with", "that", "this", "from", "have", "been", "year", "male", "female", "presenting", "presents", "history", "acute"}
        key_tokens = presentation_tokens - stop_words

        if key_tokens:
            matched_tokens = {tok for tok in key_tokens if tok in report_corpus}
            overlap_ratio = len(matched_tokens) / len(key_tokens)
            evidence_records.append({
                "type": "presentation_overlap",
                "key_tokens_count": len(key_tokens),
                "matched_count": len(matched_tokens),
                "overlap_ratio": round(overlap_ratio, 2),
            })
            if overlap_ratio < 0.20:
                detected_issues.append(
                    f"Low semantic correspondence between patient presentation and report (overlap ratio: {overlap_ratio:.2f})."
                )
                deductions += 0.35

        # 3. Clinical syndrome alignment check
        # Verify cardinal presentation keywords have corresponding diagnosis domain
        syndrome_checks = [
            ("cardiac", ["chest", "angina", "substernal", "troponin", "mi", "coronary"], ["coronary", "infarction", "angina", "myocard", "pericard", "aortic", "cardiac", "nstemi", "stemi", "heart"]),
            ("metabolic", ["dka", "ketoacidosis", "glucose", "insulin", "hyperglyc"], ["diabetic", "ketoacidosis", "dka", "hyperglyc", "hyperosmolar", "diabetes"]),
            ("respiratory", ["dyspnea", "shortness of breath", "rales", "orthopnea", "cough"], ["heart failure", "pneumonia", "embolism", "copd", "asthma", "respiratory", "pulmonary", "chf", "bronch", "infarction", "angina", "coronary", "nstemi", "stemi", "cardiac"]),
            ("renal", ["creatinine", "oliguria", "anuria", "bun", "dialysis"], ["kidney", "renal", "aki", "nephropathy", "uremia"]),
        ]

        for syn_name, presentation_keywords, valid_dx_keywords in syndrome_checks:
            if any(k in presentation_corpus for k in presentation_keywords):
                if not any(k in primary_dx or k in report_corpus for k in valid_dx_keywords):
                    detected_issues.append(
                        f"Syndrome misalignment: Patient presented with {syn_name} symptoms, but report lacks corresponding diagnostic consideration."
                    )
                    deductions += 0.3
                    evidence_records.append({"type": "syndrome_misalignment", "syndrome": syn_name})

        # Calculate final dimension score and severity
        final_score = max(0.0, min(1.0, 1.0 - deductions))
        passed = final_score >= 0.70 and len(detected_issues) == 0

        if final_score < 0.40:
            severity = EvaluationSeverity.HIGH
        elif final_score < 0.70:
            severity = EvaluationSeverity.MEDIUM
        elif detected_issues:
            severity = EvaluationSeverity.LOW
        else:
            severity = EvaluationSeverity.INFO

        explanation = (
            "Clinical context relevance fully verified: report precisely aligns with patient presentation and demographics."
            if passed
            else f"Clinical context relevance concerns: {'; '.join(detected_issues)}"
        )

        return DimensionEvaluationResult(
            dimension=self.dimension_id,
            display_name=self.display_name,
            passed=passed,
            score=round(final_score, 2),
            explanation=explanation,
            detected_issues=detected_issues,
            severity=severity,
            evidence=evidence_records,
        )
