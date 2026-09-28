"""
Cases and clinical cohort management module for AI-VH.
Provides patient records, synthetic benchmarks, and repository mappings.
"""

from .schema import GoldenCase, GroundTruth, SupportingReference, CaseView

try:
    from backend.clinical.cases import BENCHMARK_CASES
    from backend.database.repository import hospital_repo
except ImportError:
    BENCHMARK_CASES = {}
    hospital_repo = None

__all__ = [
    "GoldenCase",
    "GroundTruth",
    "SupportingReference",
    "CaseView",
    "BENCHMARK_CASES",
    "hospital_repo"
]
