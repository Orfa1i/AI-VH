"""
Encounter scoring for AI-VH multi-agent clinical encounters (STEP 34 / P5.4).

Scores a completed (or terminated) orchestrated encounter against the
case's gold-standard ground truth. Only evaluation scorers may read
``CaseSpec.ground_truth`` -- agents and generation pipelines must never
receive it directly.

Composite weights (documented in ADR-0006):
  dx_top1 0.35, dx_top3 0.20, workup_recall 0.12, workup_precision 0.08,
  red_flags 0.08, verification 0.07, time_efficiency 0.05, budget_efficiency 0.05.
"""

import re
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from vh.agents.orchestrator import EncounterBudget, EncounterState, EncounterStatus
from vh.cases.spec import CaseSpec

# Composite weights. H5 set agents.encounter_score_min = 0.30
# (see docs/steps/STEP-34.md). The project owner owns the threshold value.
WEIGHT_DX_TOP1 = 0.35
WEIGHT_DX_TOP3 = 0.20
WEIGHT_WORKUP_RECALL = 0.12
WEIGHT_WORKUP_PRECISION = 0.08
WEIGHT_RED_FLAGS = 0.08
WEIGHT_VERIFICATION = 0.07
WEIGHT_TIME = 0.05
WEIGHT_BUDGET = 0.05

TIME_EFFICIENT_MINUTES = 60
TIME_MAX_MINUTES = 360

_STOPWORDS = {"the", "and", "with", "acute", "of", "a", "an", "to", "in", "for"}


def _normalize_term(term: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", term.lower())
    return " ".join(cleaned.split())


def _significant_tokens(normalized: str) -> Set[str]:
    return {t for t in normalized.split() if len(t) > 2 and t not in _STOPWORDS}


def _tokens_match(cand_tokens: Set[str], target_tokens: Set[str]) -> bool:
    """Token overlap with substring tolerance (e.g. 'trop' matches 'troponin')."""
    if not cand_tokens or not target_tokens:
        return False
    for ct in cand_tokens:
        for tt in target_tokens:
            if ct == tt:
                return True
            if len(ct) >= 4 and len(tt) >= 4 and (ct in tt or tt in ct):
                return True
    overlap = len(cand_tokens.intersection(target_tokens))
    return overlap >= min(2, len(target_tokens))


def _diagnosis_matches(
    candidate: str,
    primary_dx: str,
    acceptable_differential: Optional[List[str]] = None,
) -> bool:
    cand_norm = _normalize_term(candidate)
    target_norm = _normalize_term(primary_dx)
    if not cand_norm or not target_norm:
        return False
    if cand_norm == target_norm or cand_norm in target_norm or target_norm in cand_norm:
        return True
    if _tokens_match(_significant_tokens(cand_norm), _significant_tokens(target_norm)):
        return True
    for diff in acceptable_differential or []:
        diff_norm = _normalize_term(diff)
        if not diff_norm:
            continue
        if cand_norm == diff_norm or cand_norm in diff_norm or diff_norm in cand_norm:
            return True
        if _tokens_match(_significant_tokens(cand_norm), _significant_tokens(diff_norm)):
            return True
    return False


# Common workup synonyms bridging panel/order names to component tests.
# Documented precedent: eval/harness/scorers/diagnostic.py CLINICAL_ALIASES.
# These match ORDERING strings only; they never generate clinical content.
WORKUP_ALIASES: Dict[str, List[str]] = {
    "cardiac enzymes": ["troponin", "ck-mb", "creatine kinase", "ck "],
    "troponin": ["cardiac enzymes", "trop "],
    "ecg": ["electrocardiogram", "ekg", "12-lead"],
    "cbc": ["complete blood count", "hemoglobin", "hematocrit", "wbc", "platelet"],
    "bmp": ["basic metabolic", "electrolytes", "creatinine", "bun"],
    "cmp": ["comprehensive metabolic", "liver function", "ast", "alt"],
    "blood gas": ["abg", "vbg", "arterial blood", "venous blood", "lactate"],
    "cxr": ["chest x-ray", "chest radiograph", "chest xray"],
    "chest radiograph": ["cxr", "chest x-ray", "xray chest"],
    "d-dimer": ["ddimer", "d dimer", "fibrin"],
    "ctpa": ["ct pulmonary", "ct angiography chest", "pulmonary embolism study"],
    "bnp": ["brain natriuretic", "nt-probnp", "nt probnp"],
    "a1c": ["hba1c", "hemoglobin a1c", "glycated hemoglobin"],
    "urinalysis": ["urine", "ua ", "microalbumin"],
    "lipase": ["amylase", "pancreatic"],
}


def _workup_alias_match(ordered_norm: str, expected_norm: str) -> bool:
    for alias, expansions in WORKUP_ALIASES.items():
        if alias in ordered_norm and any(exp.strip() in expected_norm for exp in expansions):
            return True
        if alias in expected_norm and any(exp.strip() in ordered_norm for exp in expansions):
            return True
    return False


def _workup_matches(ordered: str, expected: str) -> bool:
    ordered_norm = _normalize_term(ordered)
    expected_norm = _normalize_term(expected)
    if not ordered_norm or not expected_norm:
        return False
    if ordered_norm == expected_norm:
        return True
    if ordered_norm in expected_norm or expected_norm in ordered_norm:
        return True
    if _workup_alias_match(ordered_norm, expected_norm):
        return True
    return _tokens_match(_significant_tokens(ordered_norm), _significant_tokens(expected_norm))


def _mentions(blob: str, phrase: str) -> bool:
    blob_norm = _normalize_term(blob)
    phrase_norm = _normalize_term(phrase)
    if not phrase_norm:
        return False
    if phrase_norm in blob_norm:
        return True
    phrase_tokens = _significant_tokens(phrase_norm)
    if not phrase_tokens:
        return False
    if _tokens_match(phrase_tokens, _significant_tokens(blob_norm)):
        return True
    return all(tok in blob_norm for tok in phrase_tokens)


def _extract_differential(report: Optional[Dict[str, Any]]) -> List[str]:
    if not report:
        return []
    diffs: List[str] = []
    raw = report.get("differential") or []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("dx"):
                diffs.append(str(item["dx"]))
            elif isinstance(item, str):
                diffs.append(item)
    return diffs


def _extract_report_blob(state: EncounterState) -> str:
    parts: List[str] = []
    report = state.report or {}
    for dx in _extract_differential(report):
        parts.append(dx)
    for key in ("recommendations", "claims", "findings"):
        raw = report.get(key) or []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
    for step in state.history:
        if step.result_summary:
            parts.append(step.result_summary)
    return "\n".join(parts)


def _extract_ordered_tests(state: EncounterState) -> List[str]:
    ordered: List[str] = []
    for step in state.history:
        payload = step.payload or {}
        tests = payload.get("ordered_tests")
        if isinstance(tests, list):
            ordered.extend(str(t) for t in tests)
        findings = payload.get("findings")
        if isinstance(findings, dict):
            ordered.extend(str(k) for k in findings.keys())
        code = payload.get("order_code")
        if isinstance(code, str) and code:
            ordered.append(code)
    # Deduplicate preserving order.
    seen: Set[str] = set()
    unique: List[str] = []
    for item in ordered:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


class EncounterScore(BaseModel):
    """Per-encounter scored metrics with a 0-1 composite encounter_score."""

    case_id: str
    run_id: str = ""
    encounter_status: str = ""
    dx_top1: float = 0.0
    dx_top3: float = 0.0
    workup_recall: float = 0.0
    workup_precision: float = 0.0
    workup_ordered: List[str] = Field(default_factory=list)
    workup_expected: List[str] = Field(default_factory=list)
    red_flags_addressed: float = 0.0
    red_flags_total: int = 0
    red_flags_covered: int = 0
    time_to_diagnosis_minutes: int = 0
    time_efficiency: float = 0.0
    verification_passed: bool = False
    verification_score: float = 0.0
    budget_steps_used: int = 0
    budget_tokens_used: int = 0
    budget_cost_used: float = 0.0
    budget_sim_time_used: int = 0
    budget_efficiency: float = 0.0
    encounter_score: float = 0.0


class EncounterScorer:
    """Scores orchestrated encounters against CaseSpec ground truth."""

    def __init__(self, budget: Optional[EncounterBudget] = None) -> None:
        self.budget: EncounterBudget = budget or EncounterBudget()

    def score(self, state: EncounterState, case_spec: CaseSpec) -> EncounterScore:
        ground_truth = case_spec.ground_truth
        differential = _extract_differential(state.report)

        top1_hit = (
            _diagnosis_matches(
                differential[0],
                ground_truth.primary_dx,
                list(ground_truth.acceptable_differential),
            )
            if differential
            else False
        )
        dx_top1 = 1.0 if top1_hit else 0.0
        dx_top3 = (
            1.0
            if any(
                _diagnosis_matches(
                    cand,
                    ground_truth.primary_dx,
                    list(ground_truth.acceptable_differential),
                )
                for cand in differential[:3]
            )
            else 0.0
        )

        ordered = _extract_ordered_tests(state)
        expected = list(ground_truth.expected_workup or [])
        matched = sum(
            1 for exp in expected if any(_workup_matches(o, exp) for o in ordered)
        )
        workup_recall = (matched / len(expected)) if expected else 1.0
        if ordered:
            appropriate = sum(
                1 for o in ordered if any(_workup_matches(o, exp) for exp in expected)
            )
            workup_precision = appropriate / len(ordered)
        else:
            workup_precision = 1.0 if not expected else 0.0

        blob = _extract_report_blob(state)
        red_flags = list(ground_truth.red_flags or [])
        covered = sum(1 for flag in red_flags if _mentions(blob, flag))
        red_flags_addressed = (covered / len(red_flags)) if red_flags else 1.0

        verification = state.verification or {}
        verification_passed = (
            verification.get("passed") is True and verification.get("status") == "verified"
        )
        verification_score = 1.0 if verification_passed else 0.0

        sim_time = state.sim_time_minutes
        if sim_time <= TIME_EFFICIENT_MINUTES:
            time_efficiency = 1.0
        elif sim_time >= TIME_MAX_MINUTES:
            time_efficiency = 0.0
        else:
            time_efficiency = 1.0 - (sim_time - TIME_EFFICIENT_MINUTES) / (
                TIME_MAX_MINUTES - TIME_EFFICIENT_MINUTES
            )

        step_frac = min(1.0, state.step_count / max(1, self.budget.max_steps))
        token_frac = min(1.0, state.token_count / max(1, self.budget.max_tokens))
        cost_frac = min(1.0, state.cost / max(1e-9, self.budget.max_cost))
        time_frac = min(1.0, sim_time / max(1, self.budget.max_sim_time_minutes))
        budget_efficiency = max(
            0.0, 1.0 - 0.4 * step_frac - 0.2 * token_frac - 0.2 * cost_frac - 0.2 * time_frac
        )

        composite = (
            WEIGHT_DX_TOP1 * dx_top1
            + WEIGHT_DX_TOP3 * dx_top3
            + WEIGHT_WORKUP_RECALL * workup_recall
            + WEIGHT_WORKUP_PRECISION * workup_precision
            + WEIGHT_RED_FLAGS * red_flags_addressed
            + WEIGHT_VERIFICATION * verification_score
            + WEIGHT_TIME * time_efficiency
            + WEIGHT_BUDGET * budget_efficiency
        )

        return EncounterScore(
            case_id=state.case_id,
            run_id=getattr(state, "encounter_id", ""),
            encounter_status=(
                state.status.value
                if isinstance(state.status, EncounterStatus)
                else str(state.status)
            ),
            dx_top1=dx_top1,
            dx_top3=dx_top3,
            workup_recall=workup_recall,
            workup_precision=workup_precision,
            workup_ordered=ordered,
            workup_expected=expected,
            red_flags_addressed=red_flags_addressed,
            red_flags_total=len(red_flags),
            red_flags_covered=covered,
            time_to_diagnosis_minutes=sim_time,
            time_efficiency=round(time_efficiency, 4),
            verification_passed=verification_passed,
            verification_score=verification_score,
            budget_steps_used=state.step_count,
            budget_tokens_used=state.token_count,
            budget_cost_used=state.cost,
            budget_sim_time_used=sim_time,
            budget_efficiency=round(budget_efficiency, 4),
            encounter_score=round(composite, 4),
        )


def aggregate_encounter_scores(scores: List[EncounterScore]) -> Dict[str, float]:
    """Aggregate per-encounter scores into a 0-1 distribution summary."""
    if not scores:
        return {"n_cases": 0.0}
    n = len(scores)

    def _mean(values: List[float]) -> float:
        return round(sum(values) / n, 4) if n else 0.0

    encounter_values = [s.encounter_score for s in scores]
    return {
        "n_cases": float(n),
        "encounter_score_mean": _mean(encounter_values),
        "encounter_score_min": round(min(encounter_values), 4),
        "encounter_score_max": round(max(encounter_values), 4),
        "dx_top1_rate": _mean([s.dx_top1 for s in scores]),
        "dx_top3_rate": _mean([s.dx_top3 for s in scores]),
        "workup_recall_mean": _mean([s.workup_recall for s in scores]),
        "workup_precision_mean": _mean([s.workup_precision for s in scores]),
        "red_flags_addressed_mean": _mean([s.red_flags_addressed for s in scores]),
        "verification_pass_rate": _mean([s.verification_score for s in scores]),
        "time_efficiency_mean": _mean([s.time_efficiency for s in scores]),
        "budget_efficiency_mean": _mean([s.budget_efficiency for s in scores]),
    }
