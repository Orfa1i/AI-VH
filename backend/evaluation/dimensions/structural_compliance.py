"""
Dimension 3: Structural & Format Compliance Evaluator
Audits whether the diagnosis report satisfies the formal ClinicalReport schema,
mandatory sections, bounded confidence metrics, and required differential structure.
"""

from typing import Dict, Any, Optional, List
from .base import BaseDimensionEvaluator
from ..models import DimensionEvaluationResult, EvaluationSeverity


class StructuralComplianceEvaluator(BaseDimensionEvaluator):
    dimension_id = "structural_compliance"
    display_name = "Structural / Format Compliance"
    weight = 1.0

    MANDATORY_STRING_FIELDS = [
        ("primary_diagnosis", "Primary Diagnosis", 3),
        ("clinical_summary", "Clinical Summary", 15),
        ("clinical_reasoning", "Clinical Reasoning", 20),
        ("recommended_disposition", "Recommended Disposition", 5),
    ]

    MANDATORY_LIST_FIELDS = [
        ("differential_diagnosis", "Differential Diagnosis", 1),
        ("treatment_plan", "Treatment Plan", 1),
        ("relevant_findings", "Relevant Findings", 1),
        ("recommended_next_steps", "Recommended Next Steps", 1),
    ]

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

        # 1. Mandatory string sections check
        for field_name, label, min_len in self.MANDATORY_STRING_FIELDS:
            val = report.get(field_name)
            if not val or not isinstance(val, str) or len(val.strip()) < min_len:
                detected_issues.append(f"Missing or insufficient mandatory section: '{label}' (min {min_len} chars).")
                deductions += 0.20
                evidence_records.append({"field": field_name, "error": "missing_or_too_short", "found": val})

        # 2. Mandatory list sections check
        for field_name, label, min_items in self.MANDATORY_LIST_FIELDS:
            val = report.get(field_name)
            if not val or not isinstance(val, list) or len(val) < min_items:
                detected_issues.append(f"Missing or empty mandatory list section: '{label}' (min {min_items} items).")
                deductions += 0.15
                evidence_records.append({"field": field_name, "error": "missing_or_empty_list"})

        # 3. Differential diagnosis schema compliance
        diff_items = report.get("differential_diagnosis") or []
        if isinstance(diff_items, list) and diff_items:
            for idx, item in enumerate(diff_items):
                if hasattr(item, "model_dump"):
                    item = item.model_dump()
                elif hasattr(item, "__dict__"):
                    item = item.__dict__

                cond = item.get("condition") if isinstance(item, dict) else getattr(item, "condition", None)
                likelihood = item.get("likelihood") if isinstance(item, dict) else getattr(item, "likelihood", None)

                if not cond or not str(cond).strip():
                    detected_issues.append(f"Differential item #{idx + 1} is missing condition name.")
                    deductions += 0.10

                if likelihood is None or not isinstance(likelihood, (int, float)) or not (0.0 <= likelihood <= 1.0):
                    detected_issues.append(f"Differential item #{idx + 1} has invalid likelihood score: {likelihood} (must be 0.0-1.0).")
                    deductions += 0.10

        # 4. Diagnostic confidence bounds check
        confidence = report.get("diagnostic_confidence")
        if confidence is None or not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            detected_issues.append(f"Invalid diagnostic confidence: {confidence} (must be float between 0.0 and 1.0).")
            deductions += 0.15
            evidence_records.append({"field": "diagnostic_confidence", "found": confidence})

        # 5. Encounter and Patient ID integrity
        for id_field in ["encounter_id", "patient_id"]:
            if not report.get(id_field):
                detected_issues.append(f"Report is missing required identifier: '{id_field}'.")
                deductions += 0.10

        final_score = max(0.0, min(1.0, 1.0 - deductions))
        passed = len(detected_issues) == 0 and final_score >= 0.85

        if final_score < 0.50:
            severity = EvaluationSeverity.HIGH
        elif detected_issues:
            severity = EvaluationSeverity.MEDIUM
        else:
            severity = EvaluationSeverity.INFO

        explanation = (
            "Structural compliance verified: all required report schema sections, differential items, and bounds are valid."
            if passed
            else f"Schema compliance defects: {'; '.join(detected_issues)}"
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
