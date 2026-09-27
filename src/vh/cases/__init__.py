"""
Cases and clinical cohort management module for AI-VH.
Provides patient records, synthetic benchmarks, and repository mappings.
"""

try:
    from backend.clinical.cases import BENCHMARK_CASES
    from backend.database.repository import hospital_repo
except ImportError:
    BENCHMARK_CASES = {}
    hospital_repo = None

__all__ = ["BENCHMARK_CASES", "hospital_repo"]
