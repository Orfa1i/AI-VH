"""
Diagnosis Report Evaluation Pipeline for AI Virtual Hospital (AI-VH).
Orchestrates independent multi-stage evaluation across 6 focused clinical dimensions
with strict fail-closed behavior before reports enter the human review queue.
"""

from typing import Dict, Any, Optional, List
import uuid
import logging
from datetime import datetime, timezone

from .models import (
    AggregateEvaluationResult,
    DimensionEvaluationResult,
    EvaluationSeverity,
    EvaluationStatus,
)
from .dimensions import (
    BaseDimensionEvaluator,
    ClinicalContextRelevanceEvaluator,
    HallucinationDetectionEvaluator,
    StructuralComplianceEvaluator,
    ClinicalReasoningConsistencyEvaluator,
    RecommendationValidityEvaluator,
    EvidenceGroundingEvaluator,
)
from ..simulation.events import HospitalEvent, EventType
from ..simulation.event_bus import event_bus

logger = logging.getLogger("EvaluationPipeline")


class DiagnosisReportEvaluationPipeline:
    """
    Independent clinical report evaluation pipeline.
    Executes all 6 clinical quality dimensions independently of the generating model,
    enforcing fail-closed safety and comprehensive audit logging.
    """

    SEVERITY_ORDER = {
        EvaluationSeverity.INFO: 0,
        EvaluationSeverity.LOW: 1,
        EvaluationSeverity.MEDIUM: 2,
        EvaluationSeverity.HIGH: 3,
        EvaluationSeverity.CRITICAL: 4,
    }

    def __init__(self):
        self.evaluators: List[BaseDimensionEvaluator] = [
            ClinicalContextRelevanceEvaluator(),
            HallucinationDetectionEvaluator(),
            StructuralComplianceEvaluator(),
            ClinicalReasoningConsistencyEvaluator(),
            RecommendationValidityEvaluator(),
            EvidenceGroundingEvaluator(),
        ]

    async def evaluate_report(
        self,
        report: Any,
        patient_presentation: Optional[Dict[str, Any]] = None,
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
        emit_events: bool = True,
    ) -> AggregateEvaluationResult:
        """
        Runs the full 6-dimension evaluation pipeline against a clinical report.
        Strictly fail-closed: if report is missing or errors arise, report fails evaluation.
        """
        # Convert report to dict if Pydantic model
        report_dict: Optional[Dict[str, Any]] = None
        if report is not None:
            if hasattr(report, "model_dump"):
                report_dict = report.model_dump()
            elif hasattr(report, "__dict__"):
                report_dict = report.__dict__
            elif isinstance(report, dict):
                report_dict = dict(report)

        report_id = report_dict.get("id", f"RPT-UNKNOWN-{uuid.uuid4().hex[:6]}") if report_dict else "RPT-MISSING"
        encounter_id = report_dict.get("encounter_id", "ENC-UNKNOWN") if report_dict else "ENC-MISSING"
        patient_id = report_dict.get("patient_id", "PAT-UNKNOWN") if report_dict else "PAT-MISSING"
        eval_id = f"EVAL-{uuid.uuid4().hex[:8].upper()}"

        if emit_events:
            await event_bus.publish(
                HospitalEvent(
                    id=f"EVT-{uuid.uuid4().hex[:8]}",
                    event_type=EventType.REPORT_EVALUATION_STARTED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    sender_agent_id="evaluation_pipeline",
                    department="AUDIT_AND_SAFETY",
                    payload={"report_id": report_id, "evaluation_id": eval_id},
                    summary=f"Automated 6-Dimension Evaluation started for Clinical Report #{report_id}.",
                )
            )

        # Fail-closed check: verify report exists
        if not report_dict:
            res = AggregateEvaluationResult(
                evaluation_id=eval_id,
                report_id=report_id,
                encounter_id=encounter_id,
                patient_id=patient_id,
                overall_score=0.0,
                dimension_scores={},
                dimensions={},
                failed_checks=["MISSING_REPORT"],
                severity=EvaluationSeverity.CRITICAL,
                final_status=EvaluationStatus.REJECTED,
                passed=False,
                fail_reasons=["Report payload is missing or empty."],
                evaluated_at=datetime.now(timezone.utc),
            )
            return res

        # Fallback patient presentation extraction from report itself if not explicitly supplied
        if not patient_presentation:
            patient_presentation = {
                "age": report_dict.get("patient_age"),
                "sex": report_dict.get("patient_sex"),
                "chief_complaint": report_dict.get("chief_complaint", ""),
                "history_of_present_illness": report_dict.get("history_of_present_illness", ""),
                "past_medical_history": report_dict.get("past_medical_history", []),
                "medications": report_dict.get("medications", []),
                "allergies": report_dict.get("allergies", []),
                "vital_signs": report_dict.get("vital_signs", {}),
            }

        dimensions_results: Dict[str, DimensionEvaluationResult] = {}
        dimension_scores: Dict[str, float] = {}
        failed_checks: List[str] = []
        fail_reasons: List[str] = []
        highest_severity = EvaluationSeverity.INFO
        weighted_score_sum = 0.0
        total_weights = 0.0

        for evaluator in self.evaluators:
            dim_res = evaluator.evaluate(
                report=report_dict,
                patient_presentation=patient_presentation,
                retrieved_evidence=retrieved_evidence,
                ground_truth=ground_truth,
            )
            dimensions_results[evaluator.dimension_id] = dim_res
            dimension_scores[evaluator.dimension_id] = dim_res.score

            weighted_score_sum += dim_res.score * evaluator.weight
            total_weights += evaluator.weight

            if not dim_res.passed:
                failed_checks.append(evaluator.dimension_id)
                fail_reasons.append(f"{evaluator.display_name}: {dim_res.explanation}")

            # Update highest severity
            if self.SEVERITY_ORDER[dim_res.severity] > self.SEVERITY_ORDER[highest_severity]:
                highest_severity = dim_res.severity

        overall_score = round(weighted_score_sum / total_weights, 3) if total_weights > 0 else 0.0

        # Determine Final Status
        if highest_severity in [EvaluationSeverity.CRITICAL, EvaluationSeverity.HIGH] or overall_score < 0.60:
            final_status = EvaluationStatus.REJECTED
            passed = False
        elif highest_severity == EvaluationSeverity.MEDIUM or overall_score < 0.80 or len(failed_checks) > 0:
            final_status = EvaluationStatus.FLAGGED
            passed = False
        else:
            final_status = EvaluationStatus.PASSED
            passed = True

        aggregate_result = AggregateEvaluationResult(
            evaluation_id=eval_id,
            report_id=report_id,
            encounter_id=encounter_id,
            patient_id=patient_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            dimensions=dimensions_results,
            failed_checks=failed_checks,
            severity=highest_severity,
            final_status=final_status,
            passed=passed,
            fail_reasons=fail_reasons,
            evaluated_at=datetime.now(timezone.utc),
        )

        if emit_events:
            await event_bus.publish(
                HospitalEvent(
                    id=f"EVT-{uuid.uuid4().hex[:8]}",
                    event_type=EventType.REPORT_EVALUATION_COMPLETED,
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    sender_agent_id="evaluation_pipeline",
                    department="AUDIT_AND_SAFETY",
                    payload={
                        "report_id": report_id,
                        "evaluation_id": eval_id,
                        "overall_score": overall_score,
                        "final_status": final_status.value,
                        "passed": passed,
                        "failed_checks": failed_checks,
                    },
                    summary=f"Automated Evaluation completed: Status {final_status.value} (Score: {overall_score:.2f}, Failed Checks: {len(failed_checks)}).",
                )
            )

        return aggregate_result


# Singleton instance for platform-wide usage
evaluation_pipeline = DiagnosisReportEvaluationPipeline()
