from .report import (
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ClaimItem,
    AbstentionItem,
    ReportProvenance,
    validate_clinical_report,
    IntegrityValidationError,
    MissingClaimError,
    UnresolvedEvidenceError,
    EmptyClaimsError,
    export_clinical_report_json_schema,
)

try:
    from backend.llm.medgemma_service import medgemma_service, MedGemmaService
except ImportError:
    medgemma_service = None
    MedGemmaService = None

__all__ = [
    "ClinicalReport",
    "DifferentialItem",
    "RecommendationItem",
    "ClaimItem",
    "AbstentionItem",
    "ReportProvenance",
    "validate_clinical_report",
    "IntegrityValidationError",
    "MissingClaimError",
    "UnresolvedEvidenceError",
    "EmptyClaimsError",
    "export_clinical_report_json_schema",
    "medgemma_service",
    "MedGemmaService",
]
