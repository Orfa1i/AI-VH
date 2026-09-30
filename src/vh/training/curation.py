"""
Automated-track curation for AI-VH (approved design): counting, splitting,
contamination control, and honest labeling.

Counting rule: distinct `patient_ref`s with decision approve/correct, automated
reviewer type, complete provenance, and a passed (re)validation. Rejects,
human rows, duplicates, and incomplete records never count. Splits are by
patient with deterministic stratified allocation; contamination covers golden
id matches and near-duplicate text. Every exported row is labeled
`reviewer_type=automated`; human-labeled language is banned by test.
"""

import random
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CURATION_CONFIG_PATH = REPO_ROOT / "configs" / "training" / "curation.yaml"

COUNTABLE_DECISIONS = {"approve", "correct"}

HONESTY_BANNED_PHRASES = (
    "doctor-final",
    "doctor final",
    "physician-validated",
    "physician validated",
    "physician review",
    "expert clinical judgment",
)


def load_curation_config(path: str = "") -> Dict[str, Any]:
    """Load curation tunables (agent-owned config, never thresholds.yaml)."""
    defaults: Dict[str, Any] = {
        "version": "1.0.0",
        "t_approve": 0.50,
        "gray_zone_policy": "reject",
        "min_per_specialty": 20,
        "similarity_threshold": 0.8,
        "split_ratios": {"train": 0.7, "val": 0.15, "test": 0.15},
        "split_seed": 42,
    }
    config_path = Path(path) if path else CURATION_CONFIG_PATH
    if not config_path.exists():
        return defaults
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return {**defaults, **loaded}


def is_countable(review: Dict[str, Any]) -> bool:
    """One countable automated-reviewed case predicate (all must hold)."""
    if review.get("decision") not in COUNTABLE_DECISIONS:
        return False
    if review.get("reviewer_type", "automated") != "automated":
        return False
    if not review.get("provenance_complete", False):
        return False
    if review.get("revalidation_pass", False) is not True:
        return False
    if not str(review.get("patient_ref", "")).strip():
        return False
    return True


def count_distinct_patients(reviews: Sequence[Dict[str, Any]]) -> int:
    """Distinct countable patient_refs. Duplicates collapse; rejects excluded."""
    seen: Set[str] = set()
    for review in reviews:
        if is_countable(review):
            seen.add(str(review["patient_ref"]))
    return len(seen)


def split_by_patient(
    reviews: Sequence[Dict[str, Any]],
    seed: int = 42,
    ratios: Dict[str, float] = {"train": 0.7, "val": 0.15, "test": 0.15},
) -> Dict[str, List[Dict[str, Any]]]:
    """Deterministic stratified split by patient_ref (never by case).

    Stratified by decision class; duplicate patient_refs collapse to their
    first occurrence (sorted for determinism).
    """
    by_patient: Dict[str, Dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda r: str(r.get("patient_ref", ""))):
        ref = str(review.get("patient_ref", ""))
        if ref and ref not in by_patient:
            by_patient[ref] = review
    groups: Dict[str, List[str]] = {}
    for ref, review in by_patient.items():
        groups.setdefault(str(review.get("decision", "unknown")), []).append(ref)
    rng = random.Random(seed)
    splits: Dict[str, List[Dict[str, Any]]] = {"train": [], "val": [], "test": []}
    for decision in sorted(groups):
        refs = groups[decision][:]
        rng.shuffle(refs)
        total = len(refs)
        n_train = int(total * ratios["train"])
        n_val = int(total * ratios["val"])
        splits["train"].extend(by_patient[r] for r in refs[:n_train])
        splits["val"].extend(by_patient[r] for r in refs[n_train : n_train + n_val])
        splits["test"].extend(by_patient[r] for r in refs[n_train + n_val :])
    # Guarantee full coverage: leftovers from rounding rejoin train deterministically.
    assigned = {str(r.get("patient_ref")) for rows in splits.values() for r in rows}
    for ref in sorted(by_patient):
        if ref not in assigned:
            splits["train"].append(by_patient[ref])
    return splits


def _normalize_tokens(text: str) -> Set[str]:
    import re

    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _review_text(review: Dict[str, Any]) -> str:
    if isinstance(review.get("report_text"), str):
        return str(review["report_text"])
    report = review.get("report")
    if isinstance(report, dict):
        parts = [str(report.get("patient_summary", ""))]
        for item in report.get("differential", []) or []:
            parts.append(str(item.get("dx", "")) if isinstance(item, dict) else str(item))
        return " ".join(parts)
    return ""


def _golden_text(golden: Dict[str, Any]) -> str:
    if isinstance(golden.get("patient_summary"), str):
        return str(golden["patient_summary"])
    visible = golden.get("visible_presentation", {})
    if isinstance(visible, dict):
        return str(visible.get("chief_complaint", "") or visible.get("presentation", ""))
    return ""


def contamination_check(
    reviews: Sequence[Dict[str, Any]],
    golden_cases: Sequence[Dict[str, Any]],
    similarity_threshold: float = 0.8,
) -> List[str]:
    """Patient_refs excluded for golden id match or near-duplicate text."""
    golden_ids = {str(g.get("case_id", "")) for g in golden_cases}
    golden_texts = [_normalize_tokens(_golden_text(g)) for g in golden_cases]
    excluded: List[str] = []
    for review in reviews:
        ref = str(review.get("patient_ref", ""))
        if not ref or ref in excluded:
            continue
        if str(review.get("case_id", "")) in golden_ids:
            excluded.append(ref)
            continue
        review_tokens = _normalize_tokens(_review_text(review))
        for golden_tokens in golden_texts:
            union = review_tokens | golden_tokens
            if not union:
                continue
            if len(review_tokens & golden_tokens) / len(union) >= similarity_threshold:
                excluded.append(ref)
                break
    return excluded


def label_export_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Stamp every exported row automated; refuse human-labeled language."""
    labeled = [{**row, "reviewer_type": "automated"} for row in rows]
    blob = str(labeled).lower()
    for phrase in HONESTY_BANNED_PHRASES:
        if phrase in blob:
            raise ValueError(f"Export contains banned human-review language: {phrase!r}")
    return labeled
