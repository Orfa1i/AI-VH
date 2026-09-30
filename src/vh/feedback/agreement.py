"""
Reviewer agreement metrics for AI-VH (STEP 39 / P6.4).

Cohen's kappa over overlap pairs (two independent decided sessions on one
original): per-claim ratings and report-level decisions. Plus per-taxonomy
error rates and reviewer throughput. Only decided sessions count: an
undecided session is not a measurement.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Tuple

from vh.feedback.models import FeedbackStore

Label = Any
Pair = Tuple[Label, Label]


def cohens_kappa(pairs: List[Pair]) -> float:
    """Cohen's kappa for paired categorical labels in [-1, 1].

    Degenerate cases: empty input scores 0.0; unanimous marginals score 1.0
    when raters agree and 0.0 otherwise (chance agreement is undefined there).
    """
    if not pairs:
        return 0.0
    n = len(pairs)
    observed = sum(1 for left, right in pairs if left == right) / n
    left_counts: Counter = Counter(left for left, _ in pairs)
    right_counts: Counter = Counter(right for _, right in pairs)
    expected = sum(
        (left_counts[label] / n) * (right_counts.get(label, 0) / n)
        for label in set(left_counts) | set(right_counts)
    )
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def _overlap_session_pairs(store: FeedbackStore) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """First two decided sessions per overlap original, oldest first."""
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for original in store.list_originals():
        sessions = store.decided_sessions_for_original(original["id"])
        if len(sessions) >= 2:
            pairs.append((sessions[0], sessions[1]))
    return pairs


def claim_kappa(store: FeedbackStore) -> float:
    """Kappa over paired per-claim ratings on claims both reviewers rated."""
    pairs: List[Pair] = []
    for left_session, right_session in _overlap_session_pairs(store):
        left = {r["claim_id"]: r["rating"] for r in store.claim_ratings_for(left_session["id"])}
        right = {r["claim_id"]: r["rating"] for r in store.claim_ratings_for(right_session["id"])}
        for claim_id in left.keys() & right.keys():
            pairs.append((left[claim_id], right[claim_id]))
    return cohens_kappa(pairs)


def decision_kappa(store: FeedbackStore) -> float:
    """Kappa over paired report-level decisions (approve/correct/reject)."""
    pairs: List[Pair] = [
        (left["decision"], right["decision"]) for left, right in _overlap_session_pairs(store)
    ]
    return cohens_kappa(pairs)


def per_taxonomy_error_rates(store: FeedbackStore) -> Dict[str, Dict[str, float]]:
    """Error fraction (rating != correct) per taxonomy code across all ratings."""
    totals: Counter = Counter()
    errors: Counter = Counter()
    for row in store.all_claim_ratings():
        code = str(row["taxonomy_code"])
        totals[code] += 1
        if row["rating"] != "correct":
            errors[code] += 1
    return {
        code: {
            "n": float(totals[code]),
            "errors": float(errors[code]),
            "error_rate": (errors[code] / totals[code]) if totals[code] else 0.0,
        }
        for code in sorted(totals)
    }


def _seconds_between(started: str, ended: str) -> float:
    try:
        return max(0.0, (datetime.fromisoformat(ended) - datetime.fromisoformat(started)).total_seconds())
    except (ValueError, TypeError):
        return 0.0


def reviewer_throughput(store: FeedbackStore) -> List[Dict[str, Any]]:
    """Decided-session counts and mean decision latency per reviewer."""
    rows = store.decision_latencies()
    by_reviewer: Dict[str, List[float]] = {}
    names: Dict[str, str] = {}
    for row in rows:
        by_reviewer.setdefault(row["reviewer_id"], []).append(
            _seconds_between(row["started_at"], row["ended_at"])
        )
        names[row["reviewer_id"]] = row["name"]
    return [
        {
            "reviewer_id": reviewer_id,
            "name": names[reviewer_id],
            "decisions": len(latencies),
            "mean_seconds_per_decision": sum(latencies) / len(latencies) if latencies else 0.0,
        }
        for reviewer_id, latencies in sorted(by_reviewer.items())
    ]


def agreement_report(store: FeedbackStore) -> Dict[str, Any]:
    """Full agreement summary used by snapshots and the Phase 6 gate."""
    pairs = _overlap_session_pairs(store)
    return {
        "n_overlap_originals": len(pairs),
        "claim_kappa": claim_kappa(store),
        "decision_kappa": decision_kappa(store),
    }
