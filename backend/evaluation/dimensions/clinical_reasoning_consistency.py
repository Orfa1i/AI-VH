"""
Dimension 4: Clinical Reasoning Consistency Evaluator
Verifies whether the diagnostic conclusions are logically and coherently supported
by the case presentation, investigations, differential re-ranking, and clinical evidence.
"""

from typing import Dict, Any, Optional, List
import re
from .base import BaseDimensionEvaluator
from ..models import DimensionEvaluationResult, EvaluationSeverity


class ClinicalReasoningConsistencyEvaluator(BaseDimensionEvaluator):
    dimension_id = "clinical_reasoning_consistency"
    display_name = "Clinical Reasoning Consistency"
    weight = 1.1

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

        primary_dx = str(report.get("primary_diagnosis", "")).strip()
        clinical_reasoning = str(report.get("clinical_reasoning", "")).strip()
        diff_items = report.get("differential_diagnosis") or report.get("differential_diagnoses") or []

        # 1. Primary diagnosis vs Top Differential alignment
        if diff_items:
            first_item = diff_items[0]
            if hasattr(first_item, "model_dump"):
                first_item = first_item.model_dump()
            elif hasattr(first_item, "__dict__"):
                first_item = first_item.__dict__

            top_cond = str(first_item.get("condition", "")).strip().lower()
            norm_primary = primary_dx.lower()

            # Filter generic clinical qualifiers to prevent false matches on words like 'acute'
            dx_stopwords = {"acute", "chronic", "primary", "secondary", "severe", "mild", "moderate", "stage", "suspected", "probable", "possible", "recurrent", "unspecified"}
            top_words = {w for w in re.findall(r"\b[a-z]{3,}\b", top_cond) if w not in dx_stopwords}
            primary_words = {w for w in re.findall(r"\b[a-z]{3,}\b", norm_primary) if w not in dx_stopwords}

            # Allow semantic match (e.g. "Acute Non-ST-Elevation Myocardial Infarction" vs "NSTEMI")
            acronym_equivalences = [
                ({"nstemi", "myocardial", "infarction"}, {"nstemi", "myocardial", "infarction"}),
                ({"dka", "ketoacidosis"}, {"dka", "diabetic", "ketoacidosis"}),
                ({"aki", "kidney", "renal"}, {"aki", "kidney", "renal"}),
            ]
            has_acronym_match = any(
                bool(top_words & eq1) and bool(primary_words & eq2)
                for eq1, eq2 in acronym_equivalences
            )

            if not (top_words & primary_words) and not has_acronym_match:
                detected_issues.append(
                    f"Differential inconsistency: Primary diagnosis ('{primary_dx}') does not match top differential condition ('{first_item.get('condition')}')."
                )
                deductions += 0.35
                evidence_records.append({
                    "type": "primary_differential_mismatch",
                    "primary_diagnosis": primary_dx,
                    "top_differential": first_item.get("condition"),
                })

        # 2. Supporting points check for primary diagnosis
        if diff_items:
            first_item = diff_items[0]
            if hasattr(first_item, "model_dump"):
                first_item = first_item.model_dump()
            elif hasattr(first_item, "__dict__"):
                first_item = first_item.__dict__

            supporting = first_item.get("supporting_points") or []
            if not supporting:
                detected_issues.append("Primary diagnosis differential item lacks supporting clinical points.")
                deductions += 0.20

            # Alternative candidates should have opposing points or lower likelihood
            for idx, alt_item in enumerate(diff_items[1:], start=2):
                if hasattr(alt_item, "model_dump"):
                    alt_item = alt_item.model_dump()
                elif hasattr(alt_item, "__dict__"):
                    alt_item = alt_item.__dict__

                alt_likelihood = alt_item.get("likelihood", 0.0)
                primary_likelihood = first_item.get("likelihood", 1.0)
                if alt_likelihood >= primary_likelihood:
                    detected_issues.append(
                        f"Likelihood ranking error: Alternative candidate #{idx} ('{alt_item.get('condition')}') has likelihood ({alt_likelihood}) >= primary candidate ({primary_likelihood})."
                    )
                    deductions += 0.25

        # 3. Internal logical contradiction check in reasoning text
        reasoning_lower = clinical_reasoning.lower()
        contradiction_pairs = [
            (
                r"\bnormal\s+sinus\s+rhythm\b|\bno\s+st[- ](?:elevation|depression)\b",
                r"\bstemi\b|\bst-elevation\s+myocardial\s+infarction\b",
                "Reasoning describes normal ECG without ST elevation but asserts STEMI diagnosis.",
            ),
            (
                r"\bnormal\s+blood\s+glucose\b|\beuglycem",
                r"\bdiabetic\s+ketoacidosis\b|\bdka\b",
                "Reasoning asserts normal glucose / euglycemia while diagnosing severe DKA.",
            ),
            (
                r"\bnormal\s+troponin\b|\bnegative\s+biomarkers\b",
                r"\bmyocardial\s+infarction\b|\bnstemi\b",
                "Reasoning asserts negative/normal troponin while diagnosing acute myocardial infarction.",
            ),
        ]

        for absent_finding_pat, positive_dx_pat, desc in contradiction_pairs:
            if re.search(absent_finding_pat, reasoning_lower) and re.search(positive_dx_pat, primary_dx.lower()):
                detected_issues.append(f"Logical contradiction: {desc}")
                deductions += 0.40
                evidence_records.append({"type": "internal_contradiction", "detail": desc})

        final_score = max(0.0, min(1.0, 1.0 - deductions))
        passed = len(detected_issues) == 0 and final_score >= 0.75

        if final_score < 0.40:
            severity = EvaluationSeverity.HIGH
        elif detected_issues:
            severity = EvaluationSeverity.MEDIUM
        else:
            severity = EvaluationSeverity.INFO

        explanation = (
            "Clinical reasoning consistency verified: conclusions are logically derived from findings without contradiction."
            if passed
            else f"Reasoning consistency defects: {'; '.join(detected_issues)}"
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
