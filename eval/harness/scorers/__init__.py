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

from .generation import (
    compute_schema_valid_rate,
    compute_fabricated_citation_rate,
    compute_abstention_correct_rate,
    GenerationScorer,
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
    "compute_schema_valid_rate",
    "compute_fabricated_citation_rate",
    "compute_abstention_correct_rate",
    "GenerationScorer",
]
