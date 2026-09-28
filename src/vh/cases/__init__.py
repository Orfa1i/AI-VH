"""
Cases and clinical cohort management module for AI-VH.
Provides patient records, synthetic benchmarks, and repository mappings.
"""

from .schema import GoldenCase, GroundTruth, SupportingReference, CaseView
from .patient_repo import PatientRepository
from .fhir_loader import FHIRBundleLoader, LoadSummary

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
    "PatientRepository",
    "FHIRBundleLoader",
    "LoadSummary",
    "BENCHMARK_CASES",
    "hospital_repo",
]
