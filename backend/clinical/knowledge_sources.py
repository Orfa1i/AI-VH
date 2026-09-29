"""
Refactored clinical knowledge sources and NABD search provider for AI-VH backend.
Bridges backend clinical services to vh.rag.sources.
"""

from typing import Any, Dict, List, Optional

from vh.rag.sources import (
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
)

# Singleton service instances for application reuse
rxnorm_service = RxNormService()
nabd_service = NABDService(rxnorm_service=rxnorm_service)

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
