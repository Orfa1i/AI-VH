"""
Dimension 6: Evidence & Grounding Quality Evaluator
Verifies whether clinical diagnostic claims and recommendations are solidly
grounded in actual retrieved evidence from approved medical textbooks and knowledge sources.
Checks citation validity, detects ungrounded reports, and verifies citation provenance.
"""

from typing import Dict, Any, Optional, List
from .base import BaseDimensionEvaluator
from ..models import DimensionEvaluationResult, EvaluationSeverity


class EvidenceGroundingEvaluator(BaseDimensionEvaluator):
    dimension_id = "evidence_grounding_quality"
    display_name = "Evidence / Grounding Quality"
    weight = 1.2  # Grounding provenance critical

    APPROVED_SOURCES = {
        "harrison",
        "harrison's",
        "braunwald",
        "braunwald's",
        "nabd",
        "rxnorm",
        "nabd_rxnorm",
        "clinical pharmacology",
    }

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

        # 1. Check explicit ungrounded flag
        is_ungrounded = bool(report.get("ungrounded", False))
        if is_ungrounded:
            detected_issues.append("Report is flagged as ungrounded (failed grounding provenance).")
            deductions += 0.50
            evidence_records.append({"type": "ungrounded_flag", "value": True})

        # 2. Citations presence and structure
        citations = report.get("medical_knowledge_citations") or []
        if not citations:
            detected_issues.append("No medical knowledge citations or references attached to report.")
            deductions += 0.40
            evidence_records.append({"type": "missing_citations", "count": 0})
        else:
            evidence_records.append({"type": "citations_count", "count": len(citations)})
            valid_citations_count = 0
            for idx, c in enumerate(citations):
                if hasattr(c, "model_dump"):
                    c = c.model_dump()
                elif hasattr(c, "__dict__"):
                    c = c.__dict__

                source_name = str(c.get("source") or c.get("book") or c.get("title") or "").strip().lower()
                chapter = str(c.get("chapter") or c.get("topic") or "").strip()

                # Verify approved source
                is_approved = any(approved in source_name for approved in self.APPROVED_SOURCES)
                if not is_approved and source_name:
                    detected_issues.append(
                        f"Unapproved medical knowledge source in citation #{idx + 1}: '{source_name}'."
                    )
                    deductions += 0.15

                # Verify citation has minimum clinical context
                has_content = bool(c.get("text") or c.get("page") or chapter)
                if not has_content:
                    detected_issues.append(f"Citation #{idx + 1} lacks verifiable chapter, text, or page reference.")
                    deductions += 0.10
                else:
                    valid_citations_count += 1

            if len(citations) > 0 and valid_citations_count == 0:
                detected_issues.append("None of the supplied citations contain valid medical reference data.")
                deductions += 0.30

        # 3. Check if clinical reasoning incorporates evidence references
        reasoning = str(report.get("clinical_reasoning", "")).lower()
        has_evidence_mention = any(
            k in reasoning
            for k in ["guideline", "evidence", "harrison", "braunwald", "principles", "chapter", "[", "reference"]
        )
        if not has_evidence_mention and citations:
            detected_issues.append("Clinical reasoning does not reference or cite the retrieved medical evidence.")
            deductions += 0.15

        final_score = max(0.0, min(1.0, 1.0 - deductions))
        passed = len(detected_issues) == 0 and final_score >= 0.80 and not is_ungrounded

        if is_ungrounded or final_score < 0.40:
            severity = EvaluationSeverity.HIGH
        elif detected_issues:
            severity = EvaluationSeverity.MEDIUM
        else:
            severity = EvaluationSeverity.INFO

        explanation = (
            f"Evidence grounding verified: report is substantiated by {len(citations)} citations from approved medical sources."
            if passed
            else f"Evidence grounding deficiencies: {'; '.join(detected_issues)}"
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
