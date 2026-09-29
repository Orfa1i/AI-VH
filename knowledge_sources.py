"""
Knowledge sources root compatibility alias for AI-VH.
Refactored to route to vh.rag.sources and maintain NABD feature support.
"""

from backend.clinical.knowledge_sources import (
    SourceDocument,
    SourceAdapter,
    LicenceEnforcementError,
    PubMedAdapter,
    PMCAdapter,
    DailyMedAdapter,
    OpenFDAAdapter,
    LocalGuidelinesAdapter,
    RxNormService,
    NABDService,
    DrugProfile,
    nabd_drug_search,
    rxnorm_service,
    nabd_service,
)

__all__ = [
    "SourceDocument",
    "SourceAdapter",
    "LicenceEnforcementError",
    "PubMedAdapter",
    "PMCAdapter",
    "DailyMedAdapter",
    "OpenFDAAdapter",
    "LocalGuidelinesAdapter",
    "RxNormService",
    "NABDService",
    "DrugProfile",
    "nabd_drug_search",
    "rxnorm_service",
    "nabd_service",
]
