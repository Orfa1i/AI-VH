"""
Runtime verification router for AI Virtual Hospital (AI-VH).
Coordinates input rails, deterministic safety rules, and claim grounding checks.
Routes clinical reports to 'verified' or 'flagged' status with fail-closed security.
Stores verification results immutably with the report.
"""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from vh.common.logging import get_logger
from vh.generation.report import ClinicalReport
from .rules.engine import DeterministicSafetyEngine, SafetyEvaluationResult
from .grounding import ClaimGroundingChecker, GroundingVerdict, ReportGroundingResult
from .guardrails.runtime import ClinicalGuardrailsRuntime

logger = get_logger("vh.verification.router")
REPO_ROOT = Path(__file__).resolve().parents[2]


class VerificationStatus(str, Enum):
    """Routing verdict for a generated clinical report."""
    VERIFIED = "verified"
    FLAGGED = "flagged"


class VerificationEnvelope(BaseModel):
    """
    Immutable envelope encapsulating verified clinical report and verification telemetry.
    Strictly frozen to prevent post-verification tampering.
    """
    model_config = ConfigDict(frozen=True)

    report: ClinicalReport
    status: VerificationStatus
    reasons: Tuple[str, ...] = Field(default_factory=tuple, description="Immutable tuple of flagging reasons")
    safety_result: Optional[SafetyEvaluationResult] = None
    grounding_result: Optional[ReportGroundingResult] = None
    latency_ms: float = Field(description="Total verification latency in milliseconds")
    verified_at: str = Field(description="ISO 8601 UTC timestamp of verification")


class ClinicalVerificationRouter:
    """
    Enforces runtime guardrails and routes clinical reports.
    Policy:
      - 'verified' ONLY IF:
          1. Input scope rail is satisfied
          2. Zero critical safety rule findings
          3. Zero major safety rule findings
          4. All claims are supported (zero unsupported and zero partial claims)
          5. All citations are valid
      - Otherwise 'flagged' with explicit structured reasons attached.
      - Fail-Closed: Any checker exception or timeout immediately defaults to 'flagged'
        with reason 'verification_error'.
    """

    def __init__(
        self,
        safety_engine: Optional[Any] = None,
        grounding_checker: Optional[Any] = None,
        guardrails_runtime: Optional[Any] = None,
        timeout_s: float = 10.0,
    ):
        self.safety_engine = safety_engine or DeterministicSafetyEngine(mode="dev")
        self.grounding_checker = grounding_checker or ClaimGroundingChecker()
        self.guardrails_runtime = guardrails_runtime or ClinicalGuardrailsRuntime()
        self.timeout_s = timeout_s

    def verify(
        self,
        report: ClinicalReport,
        patient_record: Optional[Dict[str, Any]] = None,
        retrieved_chunks: Optional[Dict[str, str]] = None,
    ) -> VerificationEnvelope:
        """
        Executes full verification pipeline against the clinical report.
        Returns an immutable VerificationEnvelope.
        """
        t0 = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()
        patient_record = patient_record or {}
        retrieved_chunks = retrieved_chunks or {}
        reasons: List[str] = []

        try:
            # 1. Input Rails Check (Scope and Injection Prevention)
            text_to_check = f"{report.patient_summary} {' '.join(report.findings)}"
            is_valid_scope, scope_err = self.guardrails_runtime.validate_input_scope(text_to_check)
            if not is_valid_scope:
                reasons.append(f"out_of_scope_input: {scope_err}")

            # 2. Output Rail A: Deterministic Safety Rules Engine
            safety_res: Optional[SafetyEvaluationResult] = self.safety_engine.evaluate(
                report=report,
                patient_record=patient_record,
            )

            if safety_res:
                for finding in safety_res.findings:
                    if finding.severity == "critical":
                        reasons.append(f"safety_rule_critical: [{finding.rule_id}] {finding.message}")
                    elif finding.severity == "major":
                        reasons.append(f"safety_rule_major: [{finding.rule_id}] {finding.message}")

            # 3. Output Rail B: Claim Grounding & Citation Checker
            grounding_res: Optional[ReportGroundingResult] = self.grounding_checker.evaluate_report(
                report=report,
                retrieved_chunks=retrieved_chunks,
            )

            if grounding_res:
                for judgment in grounding_res.judgments:
                    if not judgment.citation_valid:
                        reasons.append(f"invalid_citation: [{judgment.claim_id}] {judgment.rationale}")
                    elif judgment.verdict == GroundingVerdict.UNSUPPORTED:
                        reasons.append(f"claim_grounding_unsupported: [{judgment.claim_id}] {judgment.rationale}")
                    elif judgment.verdict == GroundingVerdict.PARTIAL:
                        reasons.append(f"claim_grounding_partial: [{judgment.claim_id}] {judgment.rationale}")

            # 4. Check timeout
            elapsed_s = time.perf_counter() - t0
            if elapsed_s > self.timeout_s:
                reasons.append(f"verification_error: evaluation_timed_out ({elapsed_s:.2f}s > {self.timeout_s:.2f}s)")

            # Routing decision: VERIFIED only if zero flagging reasons
            status = VerificationStatus.VERIFIED if len(reasons) == 0 else VerificationStatus.FLAGGED
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            return VerificationEnvelope(
                report=report,
                status=status,
                reasons=tuple(reasons),
                safety_result=safety_res,
                grounding_result=grounding_res,
                latency_ms=latency_ms,
                verified_at=now_iso,
            )

        except Exception as exc:
            # FAIL-CLOSED GUARD: Any internal exception routes report to 'flagged' with verification_error
            logger.error(f"Fail-closed verification guard triggered on exception: {exc}")
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            fail_reasons = (f"verification_error: {type(exc).__name__}: {str(exc)}",)

            return VerificationEnvelope(
                report=report,
                status=VerificationStatus.FLAGGED,
                reasons=fail_reasons,
                safety_result=None,
                grounding_result=None,
                latency_ms=latency_ms,
                verified_at=now_iso,
            )
