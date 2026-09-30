"""
NeMo Guardrails actions connecting runtime flows to AI-VH verification engines.
"""

from typing import Any, Dict
from vh.generation.report import ClinicalReport
from vh.verification.rules.engine import DeterministicSafetyEngine, SafetyEvaluationResult
from vh.verification.grounding import ClaimGroundingChecker, ReportGroundingResult


def check_injection_patterns(text: str) -> bool:
    """Detects prompt injection markers and out-of-scope directives."""
    text_lower = text.lower()
    injection_markers = [
        "ignore previous instructions",
        "system prompt override",
        "write a poem",
        "stock market",
        "cryptocurrency",
        "disregard all previous",
        "bypass safety",
        "jailbreak",
    ]
    return any(marker in text_lower for marker in injection_markers)


def run_deterministic_safety_rules(
    report: ClinicalReport,
    patient_record: Dict[str, Any],
) -> SafetyEvaluationResult:
    """Executes deterministic clinical safety rules engine."""
    engine = DeterministicSafetyEngine(mode="dev")
    return engine.evaluate(report=report, patient_record=patient_record)


def run_claim_grounding_checker(
    report: ClinicalReport,
    retrieved_chunks: Dict[str, str],
) -> ReportGroundingResult:
    """Executes claim grounding and citation checker."""
    checker = ClaimGroundingChecker()
    return checker.evaluate_report(report=report, retrieved_chunks=retrieved_chunks)
