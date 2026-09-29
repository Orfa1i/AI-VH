"""
Cases and clinical cohort management module for AI-VH.
Provides patient records, synthetic benchmarks, and repository mappings.
"""

from .schema import GoldenCase, GroundTruth, SupportingReference, CaseView
from .patient_repo import PatientRepository
from .fhir_loader import FHIRBundleLoader, LoadSummary
from .spec import (
    CaseSpec,
    AgentView,
    VisiblePresentation,
    HiddenResult,
    ReleasedResult,
    DataIsolationError,
)
from .builder import (
    CaseBuilder,
    CaseBuilderConfig,
    LeakageGuard,
    NumberConsistencyChecker,
    SpecialtyCohortSpec,
    ACS_COHORT,
    CAP_COHORT,
    DKA_COHORT,
    ALL_COHORTS,
)
from .validation import (
    CaseValidator,
    BatchCaseValidator,
    VitalsRangeRule,
    UCUMUnitsRule,
    DiagnosticLabConsistencyRule,
    MedicationConditionConsistencyRule,
    TemporalOrderingRule,
    LeakageValidationRule,
    generate_spotcheck_packet,
)

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
    "CaseSpec",
    "AgentView",
    "VisiblePresentation",
    "HiddenResult",
    "ReleasedResult",
    "DataIsolationError",
    "CaseBuilder",
    "CaseBuilderConfig",
    "LeakageGuard",
    "NumberConsistencyChecker",
    "SpecialtyCohortSpec",
    "ACS_COHORT",
    "CAP_COHORT",
    "DKA_COHORT",
    "ALL_COHORTS",
    "CaseValidator",
    "BatchCaseValidator",
    "VitalsRangeRule",
    "UCUMUnitsRule",
    "DiagnosticLabConsistencyRule",
    "MedicationConditionConsistencyRule",
    "TemporalOrderingRule",
    "LeakageValidationRule",
    "generate_spotcheck_packet",
    "BENCHMARK_CASES",
    "hospital_repo",
]
