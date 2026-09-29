"""
Scorers package for AI-VH evaluation harness.
"""

from .retrieval import (
    RetrievalMetrics,
    compute_recall_at_k,
    compute_reciprocal_rank,
    compute_per_source_recall,
    compute_traceability_rate,
    compute_duplicate_rate,
    compute_stale_count,
    compute_p95_latency,
    build_retrieval_query_from_case_view,
    RetrievalEvaluationHarness,
)

__all__ = [
    "RetrievalMetrics",
    "compute_recall_at_k",
    "compute_reciprocal_rank",
    "compute_per_source_recall",
    "compute_traceability_rate",
    "compute_duplicate_rate",
    "compute_stale_count",
    "compute_p95_latency",
    "build_retrieval_query_from_case_view",
    "RetrievalEvaluationHarness",
]
