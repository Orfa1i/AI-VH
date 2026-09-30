"""
Independent automated reviewer/evaluator for AI-VH (approved automated-track design).

INDEPENDENCE MANDATE: the evaluator derives decisions ONLY from independently
computed signals -- schema validation, deterministic safety rules, grounding
verification, Ground-Truth comparison, and metric math. It receives DATA
(EncounterState, CaseSpec, evidence chunks), never generators, adapters, or
models. Generator self-assessment fields (confidence, self-evaluation,
reasoning traces, justifications) are stripped by `sanitize_for_evaluation`
before any signal is computed, so they can neither pass nor fail a report.
"""

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from vh.agents.orchestrator import EncounterState
from vh.agents.scoring import EncounterScorer
from vh.cases.spec import CaseSpec
from vh.generation.report import ClinicalReport, validate_clinical_report
from vh.verification.grounding import ClaimGroundingChecker
from vh.verification.router import ClinicalVerificationRouter, VerificationStatus
from vh.verification.rules.engine import DeterministicSafetyEngine

SELF_ASSESSMENT_FIELDS = frozenset(
    {
        "confidence",
        "self_evaluation",
        "self_assessment",
        "self_critique",
        "self_score",
        "reasoning_trace",
        "reasoning",
        "chain_of_thought",
        "justification",
        "certainty",
        "model_confidence",
    }
)

VALIDATOR_VERSIONS = {
    "router": "verification-router/1.0.0",
    "safety_tables": "configs/safety v1.0.0",
    "grounding": "deterministic-heuristic/v1",
    "scorer": "encounter-scorer/v1",
}

FATAL_REASONS = {"schema_invalid", "critical_safety", "dx_miss", "red_flag_miss"}


class AutomatedReview(BaseModel):
    """Result of one independent automated evaluation."""

    decision: str = Field(description="approve | correct | reject")
    reasons: List[str] = Field(default_factory=list)
    target: Optional[Dict[str, Any]] = Field(
        default=None, description="SFT target (automated-target, never doctor-final)"
    )
    repair_ops: List[Dict[str, Any]] = Field(default_factory=list)
    revalidation_pass: bool = False
    sanitized_removed: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: str = ""


def sanitize_for_evaluation(report: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Deep-copy the report with generator self-assessment fields removed.

    Returns (sanitized, removed_paths). The input is never mutated.
    """
    cleaned = copy.deepcopy(report)
    removed: List[str] = []

    def _walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key in [k for k in node.keys() if k in SELF_ASSESSMENT_FIELDS]:
                del node[key]
                removed.append(f"{path}.{key}" if path else str(key))
            for key, value in node.items():
                _walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                _walk(value, f"{path}[{index}]")

    _walk(cleaned, "")
    return cleaned, removed


def decide_from_metrics(metrics: Dict[str, Any], t_approve: float) -> Tuple[str, List[str]]:
    """Pure decision function over independently computed metric signals."""
    reasons: List[str] = []
    if not metrics.get("schema_ok", False):
        return "reject", ["schema_invalid"]
    if int(metrics.get("critical_count", 0)) > 0:
        reasons.append("critical_safety")
    if float(metrics.get("dx_top1", 0.0)) != 1.0:
        reasons.append("dx_miss")
    if float(metrics.get("red_flags", 0.0)) != 1.0:
        reasons.append("red_flag_miss")
    if not metrics.get("verification_passed", False):
        reasons.append("verification_failed")
    grounding_bad = int(metrics.get("grounding_unsupported", 0)) > 0
    fatal = any(reason in FATAL_REASONS for reason in reasons)
    if grounding_bad and not fatal and metrics.get("verification_passed", False):
        return "correct", []
    if grounding_bad:
        reasons.append("grounding_unsupported")
    if not metrics.get("router_verified", False):
        reasons.append("router_not_verified")
    if not reasons and float(metrics.get("composite", 0.0)) < t_approve:
        reasons.append("ambiguous_composite")
    if reasons:
        return "reject", reasons
    return "approve", []


class _Unfixable(Exception):
    """Repair cannot proceed; the report must be rejected."""


class AutomatedEvaluator:
    """Independent evaluator: deterministic validators + Ground-Truth scorer.

    Dependencies are validator objects (or test doubles with the same method
    shapes). No generator, adapter, model, or LLM handle is accepted.
    """

    def __init__(
        self,
        t_approve: float = 0.50,
        safety_engine: Optional[DeterministicSafetyEngine] = None,
        grounding_checker: Optional[ClaimGroundingChecker] = None,
        router: Optional[ClinicalVerificationRouter] = None,
        scorer: Optional[EncounterScorer] = None,
    ) -> None:
        self.t_approve = t_approve
        self.safety_engine = safety_engine or DeterministicSafetyEngine(mode="dev")
        # adapter=None forces the deterministic heuristic judge: zero LLM
        # dependency, so generation-time models cannot influence the verdict.
        self.grounding_checker = grounding_checker or ClaimGroundingChecker(adapter=None)
        self.router = (
            router
            or ClinicalVerificationRouter(
                safety_engine=self.safety_engine,
                grounding_checker=self.grounding_checker,
            )
        )
        self.scorer = scorer or EncounterScorer()

    def _patient_record(self, case_spec: CaseSpec) -> Dict[str, Any]:
        visible = case_spec.visible
        return {
            "allergies": list(visible.allergies),
            "current_medications": list(visible.current_medications),
            "initial_vitals": dict(visible.initial_vitals),
            "demographics": dict(visible.demographics),
        }

    def evaluate(
        self,
        state: EncounterState,
        case_spec: CaseSpec,
        evidence: Dict[str, str],
        ground_truth_source: str = "physician-verified-golden-v1",
        ground_truth_version: str = "v1",
        reviewer_id: str = "auto-validator/v1",
    ) -> AutomatedReview:
        """Evaluate one completed encounter. Fails closed on any validator error."""
        evaluated_at = datetime.now(timezone.utc).isoformat()
        raw_report = state.report or {}
        sanitized, removed = sanitize_for_evaluation(raw_report)

        def _provenance(
            decision: str,
            reasons: List[str],
            metrics: Dict[str, Any],
            target: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            report_provenance = sanitized.get("provenance", {})
            if not isinstance(report_provenance, dict):
                report_provenance = {}
            return {
                "reviewer_type": "automated",
                "reviewer_id": reviewer_id,
                "case_id": state.case_id,
                "patient_ref": case_spec.patient_ref,
                "ground_truth_source": ground_truth_source,
                "ground_truth_version": ground_truth_version,
                "validator_versions": dict(VALIDATOR_VERSIONS),
                "metrics": metrics,
                "decision": decision,
                "reasons": list(reasons),
                "model_versions": {
                    "model_id": report_provenance.get("model_id", "unknown"),
                    "prompt_version": report_provenance.get("prompt_name_version", "unknown"),
                    "index_version": report_provenance.get("index_version", "unknown"),
                },
            }

        def _reject(reasons: List[str], metrics: Dict[str, Any]) -> AutomatedReview:
            return AutomatedReview(
                decision="reject",
                reasons=reasons,
                target=None,
                repair_ops=[],
                revalidation_pass=False,
                sanitized_removed=removed,
                provenance=_provenance("reject", reasons, metrics),
                evaluated_at=evaluated_at,
            )

        try:
            clinical = ClinicalReport.model_validate(sanitized)
            validate_clinical_report(clinical, valid_evidence_ids=set(evidence.keys()))
        except Exception:
            return _reject(["schema_invalid"], {"schema_ok": False})

        try:
            envelope = self.router.verify(clinical, self._patient_record(case_spec), evidence)
            safety_result = envelope.safety_result
            grounding_result = envelope.grounding_result
            critical_count = int(getattr(safety_result, "critical_count", 0) or 0)
            unsupported = int(getattr(grounding_result, "unsupported_count", 0) or 0)
            invalid_citations = int(getattr(grounding_result, "invalid_citation_count", 0) or 0)
            router_verified = envelope.status == VerificationStatus.VERIFIED
            bad_claim_ids = {
                judgment.claim_id
                for judgment in (getattr(grounding_result, "judgments", []) or [])
                if getattr(getattr(judgment, "verdict", ""), "value", judgment.verdict)
                != "supported"
            }
            scored_state = state.model_copy(update={"report": sanitized})
            score = self.scorer.score(scored_state, case_spec)
            verification = state.verification or {}
            metrics = {
                "schema_ok": True,
                "critical_count": critical_count,
                "grounding_unsupported": unsupported + invalid_citations,
                "dx_top1": score.dx_top1,
                "dx_top3": score.dx_top3,
                "red_flags": score.red_flags_addressed,
                "composite": score.encounter_score,
                "verification_passed": bool(
                    verification.get("passed") is True and verification.get("status") == "verified"
                ),
                "router_verified": bool(router_verified),
            }
        except Exception:
            return _reject(["eval_error"], {"schema_ok": True})

        decision, reasons = decide_from_metrics(metrics, self.t_approve)
        if decision == "approve":
            return AutomatedReview(
                decision="approve",
                reasons=[],
                target=sanitized,
                repair_ops=[],
                revalidation_pass=True,
                sanitized_removed=removed,
                provenance=_provenance("approve", [], metrics, sanitized),
                evaluated_at=evaluated_at,
            )
        if decision == "reject":
            return _reject(reasons, metrics)

        # Correct track: deletion-only repair of unsupported claims, then full
        # revalidation. Any failure or residual defect rejects.
        try:
            repaired, repair_ops = self._repair_unsupported(sanitized, bad_claim_ids)
            revalidated = self._revalidate(repaired, case_spec, evidence, state)
        except _Unfixable as exc:
            return _reject(["unfixable_repair", str(exc)], metrics)
        except Exception:
            return _reject(["eval_error"], metrics)
        if not revalidated:
            return _reject(["revalidation_failed"] + reasons, metrics)
        return AutomatedReview(
            decision="correct",
            reasons=[],
            target=repaired,
            repair_ops=repair_ops,
            revalidation_pass=True,
            sanitized_removed=removed,
            provenance=_provenance("correct", [], metrics, repaired),
            evaluated_at=evaluated_at,
        )

    def _repair_unsupported(
        self, sanitized: Dict[str, Any], bad_claim_ids: set
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Drop unsupported claims (+ abstentions); prune dangling references.

        Raises _Unfixable when a differential or recommendation would be left
        with no supporting claims: repair must never weaken schema integrity.
        """
        if not bad_claim_ids:
            raise _Unfixable("no unsupported claims to repair")
        repaired = copy.deepcopy(sanitized)
        claims = repaired.get("claims", [])
        if not isinstance(claims, list):
            raise _Unfixable("claims block is not a list")
        repair_ops: List[Dict[str, Any]] = []
        kept: List[Dict[str, Any]] = []
        for index, claim in enumerate(claims):
            claim_id = claim.get("claim_id") if isinstance(claim, dict) else None
            if claim_id in bad_claim_ids:
                repair_ops.append({"op": "remove", "path": ["claims", index]})
            else:
                kept.append(claim)
        # Rebuild without index-shift hazards; record canonical index-free ops.
        repaired["claims"] = kept
        repair_ops = [
            {"op": "remove", "path": ["claims"], "value": sorted(bad_claim_ids)},
        ]
        for entry_key in ("differential", "recommendations"):
            for entry in repaired.get(entry_key, []) or []:
                if not isinstance(entry, dict):
                    continue
                linked = [cid for cid in entry.get("claim_ids", []) if cid not in bad_claim_ids]
                entry["claim_ids"] = linked
                if not linked:
                    raise _Unfixable(f"{entry_key} entry left without supporting claims")
        abstentions = repaired.get("abstentions")
        if not isinstance(abstentions, list):
            abstentions = []
            repaired["abstentions"] = abstentions
            repair_ops.append({"op": "add", "path": ["abstentions"], "value": []})
        for claim_id in sorted(bad_claim_ids):
            abstentions.append(
                {
                    "question": f"Insufficient evidence for {claim_id}",
                    "reason": "Claim removed during automated review: no supporting evidence chunk found.",
                }
            )
            repair_ops.append(
                {
                    "op": "add",
                    "path": ["abstentions", len(abstentions) - 1],
                    "value": f"Insufficient evidence for {claim_id}",
                }
            )
        return repaired, repair_ops

    def _revalidate(
        self,
        repaired: Dict[str, Any],
        case_spec: CaseSpec,
        evidence: Dict[str, str],
        state: EncounterState,
    ) -> bool:
        """Full revalidation of a repaired report: schema, router, scorer bars."""
        try:
            clinical = ClinicalReport.model_validate(repaired)
            validate_clinical_report(clinical, valid_evidence_ids=set(evidence.keys()))
            envelope = self.router.verify(clinical, self._patient_record(case_spec), evidence)
            if envelope.status != VerificationStatus.VERIFIED:
                return False
            if int(getattr(envelope.safety_result, "critical_count", 0) or 0) > 0:
                return False
            grounding_result = envelope.grounding_result
            if int(getattr(grounding_result, "unsupported_count", 0) or 0) > 0:
                return False
            if int(getattr(grounding_result, "invalid_citation_count", 0) or 0) > 0:
                return False
            rescored = self.scorer.score(state.model_copy(update={"report": repaired}), case_spec)
            return bool(
                rescored.dx_top1 == 1.0
                and rescored.red_flags_addressed == 1.0
                and rescored.encounter_score >= self.t_approve
            )
        except Exception:
            return False
