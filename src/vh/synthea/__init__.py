"""
AI-VH Synthea Package: Reproducible FHIR generation, bundle validation,
isolated demo data service, and multi-resource FHIR R4 adaptation.
"""

from .config import SyntheaGenerationConfig
from .runner import SyntheaRunResult, SyntheaRunner
from .validator import BundleValidationReport, validate_bundle_directory, validate_fhir_bundle
from .fhir_adapter import (
    FHIRR4Adapter,
    TimelineEvent,
    DemoPatientProfile,
    DemoPatientSummary,
    TimelineResponse,
)
from .service import DemoDataService, demo_data_service

__all__ = [
    "SyntheaGenerationConfig",
    "SyntheaRunner",
    "SyntheaRunResult",
    "BundleValidationReport",
    "validate_bundle_directory",
    "validate_fhir_bundle",
    "FHIRR4Adapter",
    "TimelineEvent",
    "DemoPatientProfile",
    "DemoPatientSummary",
    "TimelineResponse",
    "DemoDataService",
    "demo_data_service",
]
