"""
Diagnostic accuracy and bootstrap confidence interval scorers for AI-VH evaluation harness.
Evaluates top-1 and top-3 diagnostic concordance against physician-verified golden ground truth,
computes paired bootstrap differences, and measures run-to-run stability.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

from vh.cases.schema import CaseView, GoldenCase
from eval.harness.interfaces import PipelineResult


# Clinical abbreviations and expansions for robust diagnostic matching
CLINICAL_ALIASES: Dict[str, List[str]] = {
    "stemi": ["st elevation myocardial infarction", "anterior stemi", "inferior stemi", "lateral stemi", "posterior stemi", "myocardial infarction"],
    "nstemi": ["non st elevation myocardial infarction", "nonstemi", "acute coronary syndrome"],
    "dka": ["diabetic ketoacidosis", "ketoacidosis"],
    "cap": ["community acquired pneumonia", "pneumonia", "bacterial pneumonia", "lobar pneumonia"],
    "copd": ["chronic obstructive pulmonary disease", "copd exacerbation"],
    "pe": ["pulmonary embolism"],
    "acs": ["acute coronary syndrome", "myocardial infarction"],
}

CORE_DISEASE_ENTITIES: List[str] = [
    "pneumonia",
    "pneumonitis",
    "ketoacidosis",
    "stemi",
    "nstemi",
    "angina",
    "pericarditis",
    "cardiomyopathy",
]


def normalize_medical_term(term: str) -> str:
    """Normalizes medical diagnosis string by lowercasing and stripping punctuation."""
    if not term:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", term.lower())
    return " ".join(cleaned.split())


def is_diagnostic_match(
    candidate: str,
    primary_dx: str,
    acceptable_differential: Optional[List[str]] = None,
) -> bool:
    """
    Evaluates whether a candidate diagnosis matches the primary diagnosis
    or any acceptable differential from golden ground truth.
    """
    cand_norm = normalize_medical_term(candidate)
    target_norm = normalize_medical_term(primary_dx)

    if not cand_norm or not target_norm:
        return False

    # Exact or substring containment
    if cand_norm == target_norm or cand_norm in target_norm or target_norm in cand_norm:
        return True

    # Check clinical alias mappings against primary
    for alias, expansions in CLINICAL_ALIASES.items():
        if alias in cand_norm and any(exp in target_norm for exp in expansions):
            return True
        if alias in target_norm and any(exp in cand_norm for exp in expansions):
            return True

    # Check shared core clinical entity
    for entity in CORE_DISEASE_ENTITIES:
        if entity in cand_norm and entity in target_norm:
            return True

    # Token overlap check (e.g. "Acute Anterior STEMI" and "STEMI")
    cand_tokens = set(cand_norm.split())
    target_tokens = set(target_norm.split())
    informative_tokens = {t for t in target_tokens if len(t) > 2 and t not in ("the", "and", "with", "acute")}
    if informative_tokens and len(cand_tokens.intersection(informative_tokens)) >= min(2, len(informative_tokens)):
        return True

    # Check against acceptable differentials
    if acceptable_differential:
        for diff in acceptable_differential:
            diff_norm = normalize_medical_term(diff)
            if not diff_norm:
                continue
            if cand_norm == diff_norm or cand_norm in diff_norm or diff_norm in cand_norm:
                return True
            for alias, expansions in CLINICAL_ALIASES.items():
                if alias in cand_norm and any(exp in diff_norm for exp in expansions):
                    return True
                if alias in diff_norm and any(exp in cand_norm for exp in expansions):
                    return True
            for entity in CORE_DISEASE_ENTITIES:
                if entity in cand_norm and entity in diff_norm:
                    return True
            diff_tokens = set(diff_norm.split())
            diff_info = {t for t in diff_tokens if len(t) > 2 and t not in ("the", "and", "with", "acute")}
            if diff_info and len(cand_tokens.intersection(diff_info)) >= min(2, len(diff_info)):
                return True

    return False


def compute_per_case_accuracy(
    results: List[Tuple[CaseView, PipelineResult]],
    golden_cases: List[GoldenCase],
    metric: str = "dx_top3",
) -> List[float]:
    """
    Computes binary accuracy (1.0 or 0.0) for each evaluated case.
    metric: 'dx_top1' or 'dx_top3'.
    """
    golden_map = {g.case_id: g for g in golden_cases}
    accuracies: List[float] = []

    for cv, res in results:
        gc = golden_map.get(cv.case_id)
        if not gc:
            accuracies.append(0.0)
            continue

        primary_dx = gc.ground_truth.primary_dx
        acceptable_diff = gc.ground_truth.acceptable_differential

        if metric == "dx_top1":
            match = is_diagnostic_match(res.diagnosis, primary_dx, acceptable_diff)
            accuracies.append(1.0 if match else 0.0)
        elif metric == "dx_top3":
            # Check primary diagnosis plus top-3 differentials
            candidates = [res.diagnosis]
            if res.differential:
                candidates.extend(res.differential[:3])
            match = any(is_diagnostic_match(c, primary_dx, acceptable_diff) for c in candidates)
            accuracies.append(1.0 if match else 0.0)
        else:
            raise ValueError(f"Unknown diagnostic metric '{metric}'. Expected 'dx_top1' or 'dx_top3'.")

    return accuracies


def evaluate_diagnostic_accuracy(
    results: List[Tuple[CaseView, PipelineResult]],
    golden_cases: List[GoldenCase],
) -> Dict[str, float]:
    """Computes aggregate top-1 and top-3 diagnostic accuracy."""
    if not results:
        return {"dx_top1": 0.0, "dx_top3": 0.0}

    top1_scores = compute_per_case_accuracy(results, golden_cases, metric="dx_top1")
    top3_scores = compute_per_case_accuracy(results, golden_cases, metric="dx_top3")

    return {
        "dx_top1": round(float(np.mean(top1_scores)), 4),
        "dx_top3": round(float(np.mean(top3_scores)), 4),
    }


def compute_bootstrap_ci_difference(
    rag_results: List[Tuple[CaseView, PipelineResult]],
    norag_results: List[Tuple[CaseView, PipelineResult]],
    golden_cases: List[GoldenCase],
    metric: str = "dx_top3",
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Tuple[float, float]:
    """
    Computes a non-parametric paired bootstrap confidence interval for accuracy difference:
      Delta = Accuracy(RAG) - Accuracy(No-RAG)
    Returns (ci_lower, ci_upper) at (1 - alpha) confidence (default 95%).
    """
    rag_acc = compute_per_case_accuracy(rag_results, golden_cases, metric=metric)
    norag_acc = compute_per_case_accuracy(norag_results, golden_cases, metric=metric)

    n = len(rag_acc)
    if n == 0 or n != len(norag_acc):
        return (0.0, 0.0)

    diffs = np.array(rag_acc) - np.array(norag_acc)

    rng = np.random.default_rng(seed)
    bootstrap_means: List[float] = []

    for _ in range(n_bootstrap):
        sample_indices = rng.choice(n, size=n, replace=True)
        resampled_mean = float(np.mean(diffs[sample_indices]))
        bootstrap_means.append(resampled_mean)

    lower_pct = (alpha / 2.0) * 100.0
    upper_pct = (1.0 - alpha / 2.0) * 100.0

    ci_lower = round(float(np.percentile(bootstrap_means, lower_pct)), 4)
    ci_upper = round(float(np.percentile(bootstrap_means, upper_pct)), 4)

    return ci_lower, ci_upper


def compute_differential_agreement(
    run_a: List[PipelineResult],
    run_b: List[PipelineResult],
) -> float:
    """Computes mean top-3 differential overlap (Jaccard agreement) between two runs."""
    if not run_a or len(run_a) != len(run_b):
        return 0.0

    agreements: List[float] = []
    for r_a, r_b in zip(run_a, run_b):
        set_a = set(normalize_medical_term(d) for d in r_a.differential[:3])
        set_b = set(normalize_medical_term(d) for d in r_b.differential[:3])
        if not set_a and not set_b:
            agreements.append(1.0)
            continue
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        jaccard = intersection / union if union > 0 else 0.0
        agreements.append(jaccard)

    return round(float(np.mean(agreements)), 4)
