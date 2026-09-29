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

from .medgemma import (
    MedGemmaAdapter,
    MedGemmaConfig,
    GenerationFailed,
    GenerationTimeoutError,
    GenerationConcurrencyError,
    MissingPromptVersionError,
    extract_json_from_text,
    format_generation_prompt,
)

from .pipeline import (
    GroundedGenerationPipeline,
    QueryPlanner,
    get_default_retrieval_service,
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
    "MedGemmaAdapter",
    "MedGemmaConfig",
    "GenerationFailed",
    "GenerationTimeoutError",
    "GenerationConcurrencyError",
    "MissingPromptVersionError",
    "extract_json_from_text",
    "format_generation_prompt",
    "GroundedGenerationPipeline",
    "QueryPlanner",
    "get_default_retrieval_service",
    "medgemma_service",
    "MedGemmaService",
]
