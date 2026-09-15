"""
Deterministic Clinical Text Scoring
Computes evaluation metrics by comparing real model-generated text (from
MedGemmaService, live GPU or heuristic engine) against case ground truth,
instead of using invented literals.
"""

import re
from typing import Any, Dict, List

_STOPWORDS = {
    "with", "the", "a", "an", "of", "and", "or", "to", "in", "on", "for",
    "is", "at", "by", "from", "secondary", "due",
}


def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOPWORDS]


def diagnosis_accuracy_percent(predicted_diagnosis: str, true_diagnosis: str) -> float:
    """Recall of true-diagnosis tokens found in the predicted diagnosis text, bucketed."""
    true_tokens = set(_tokenize(true_diagnosis))
    if not true_tokens:
        return 0.0
    pred_tokens = set(_tokenize(predicted_diagnosis))
    recall = len(true_tokens & pred_tokens) / len(true_tokens)

    if recall >= 0.50:
        return 100.0
    if recall >= 0.25:
        return 60.0
    if recall >= 0.10:
        return 35.0
    return round(recall * 100, 1)


def differential_completeness_percent(context_text: str, differentials: List[str]) -> float:
    """Percent of differential candidates whose distinguishing terms/acronym appear in the text."""
    if not differentials:
        return 0.0
    text = (context_text or "").lower()
    matches = 0
    for d in differentials:
        acronyms = re.findall(r"\(([A-Z/]{2,10})\)", d)
        acronym_hit = any(a.lower() in text for group in acronyms for a in group.split("/"))
        key_tokens = [t for t in _tokenize(d) if len(t) >= 6]
        token_hit = any(t in text for t in key_tokens)
        if acronym_hit or token_hit:
            matches += 1
    return round(matches / len(differentials) * 100, 1)


def treatment_overlap_percent(treatment_plan: List[str], reference_items: List[str]) -> float:
    """Percent of reference treatment items reflected (token overlap >= 25%) in the actual plan."""
    if not reference_items:
        return 0.0
    plan_text = " ".join(treatment_plan or []).lower()
    matches = 0
    for item in reference_items:
        tokens = [t for t in _tokenize(item) if len(t) > 4]
        if not tokens:
            continue
        hit_ratio = sum(1 for t in tokens if t in plan_text) / len(tokens)
        if hit_ratio >= 0.25:
            matches += 1
    return round(matches / len(reference_items) * 100, 1)


def treatment_safety_percent(contraindications_missed: int, adverse_violations: int) -> float:
    score = 100.0 - (contraindications_missed * 30.0) - (adverse_violations * 10.0)
    return max(0.0, min(100.0, score))


def evidence_grounding_percent(citations: List[str], reasoning: str) -> float:
    score = len(citations or []) * 45.0
    if "harrison" in (reasoning or "").lower():
        score += 15.0
    return max(0.0, min(100.0, score))


def overall_clinical_score(
    diagnostic_accuracy: float,
    treatment_safety: float,
    evidence_grounding: float,
    differential_completeness: float,
    workup_efficiency: float,
    has_contraindication: bool,
) -> float:
    """Weighted composite mapped onto a 1.0-5.0 clinical quality scale.

    Safety and diagnostic correctness dominate the weighting because a
    clinically unsafe or wrong-diagnosis plan cannot be rated "good"
    regardless of secondary polish (differential breadth, workup coverage).
    Any missed contraindication additionally halves the composite score,
    reflecting that a single contraindicated order is a patient-safety
    failure, not a partial-credit deduction.
    """
    weighted = (
        diagnostic_accuracy * 0.25
        + treatment_safety * 0.40
        + evidence_grounding * 0.25
        + differential_completeness * 0.05
        + workup_efficiency * 0.05
    )
    if has_contraindication:
        weighted *= 0.5
    return round(1.0 + (weighted / 100.0) * 4.0, 2)
