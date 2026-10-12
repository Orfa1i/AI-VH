"""
Base Dimension Evaluator Interface for AI Virtual Hospital (AI-VH).
Enforces fail-closed evaluation semantics across all clinical dimensions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from ..models import DimensionEvaluationResult, EvaluationSeverity

logger = logging.getLogger("DimensionEvaluator")


class BaseDimensionEvaluator(ABC):
    """
    Abstract base evaluator for a single clinical quality dimension.
    Subclasses must implement `_evaluate_internal`.
    The public `evaluate()` method guarantees fail-closed exception handling.
    """

    dimension_id: str = "base"
    display_name: str = "Base Dimension"
    weight: float = 1.0

    @abstractmethod
    def _evaluate_internal(
        self,
        report: Dict[str, Any],
        patient_presentation: Dict[str, Any],
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> DimensionEvaluationResult:
        """Subclass implementation of the dimension-specific clinical checks."""
        pass

    def evaluate(
        self,
        report: Optional[Dict[str, Any]],
        patient_presentation: Optional[Dict[str, Any]],
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> DimensionEvaluationResult:
        """
        Public execution wrapper with strict fail-closed behavior.
        If required report or patient presentation is missing, or an unexpected
        exception occurs during evaluation, this method FAILS CLOSED.
        """
        if not report:
            return DimensionEvaluationResult(
                dimension=self.dimension_id,
                display_name=self.display_name,
                passed=False,
                score=0.0,
                explanation=f"Fail-closed: Missing clinical report input for {self.display_name} evaluation.",
                detected_issues=["MISSING_REPORT_PAYLOAD"],
                severity=EvaluationSeverity.CRITICAL,
                evidence=[{"error": "report payload was None or empty"}],
            )

        if not patient_presentation:
            return DimensionEvaluationResult(
                dimension=self.dimension_id,
                display_name=self.display_name,
                passed=False,
                score=0.0,
                explanation=f"Fail-closed: Missing patient clinical presentation data for {self.display_name} evaluation.",
                detected_issues=["MISSING_PATIENT_PRESENTATION"],
                severity=EvaluationSeverity.CRITICAL,
                evidence=[{"error": "patient presentation payload was None or empty"}],
            )

        try:
            return self._evaluate_internal(
                report=report,
                patient_presentation=patient_presentation,
                retrieved_evidence=retrieved_evidence or {},
                ground_truth=ground_truth,
            )
        except Exception as e:
            logger.error(
                f"Unhandled exception during {self.display_name} evaluation: {e}",
                exc_info=True,
            )
            return DimensionEvaluationResult(
                dimension=self.dimension_id,
                display_name=self.display_name,
                passed=False,
                score=0.0,
                explanation=f"Fail-closed: Evaluation crashed with unhandled exception: {str(e)}",
                detected_issues=["EVALUATOR_EXECUTION_ERROR"],
                severity=EvaluationSeverity.CRITICAL,
                evidence=[{"exception": str(e), "evaluator": self.dimension_id}],
            )
