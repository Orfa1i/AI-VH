"""
Clinical knowledge source adapters and terminology services for AI-VH RAG.
"""

from vh.rag.sources.base import (
    SourceDocument,
    SourceAdapter,
    LicenceEnforcementError,
    is_licence_permitted,
    assert_licence_permitted,
    PERMITTED_LICENCES,
    RateLimiter,
    RetryHandler,
)
from vh.rag.sources.pubmed import PubMedAdapter
from vh.rag.sources.pmc import PMCAdapter
from vh.rag.sources.dailymed import DailyMedAdapter
from vh.rag.sources.openfda import OpenFDAAdapter
from vh.rag.sources.guidelines import LocalGuidelinesAdapter
from vh.rag.sources.rxnorm import RxNormService
from vh.rag.sources.nabd import NABDService, DrugProfile, nabd_drug_search
from vh.rag.sources.client import SourceClient, get_ncbi_client

__all__ = [
    "SourceDocument",
    "SourceAdapter",
    "LicenceEnforcementError",
    "is_licence_permitted",
    "assert_licence_permitted",
    "PERMITTED_LICENCES",
    "RateLimiter",
    "RetryHandler",
    "PubMedAdapter",
    "PMCAdapter",
    "DailyMedAdapter",
    "OpenFDAAdapter",
    "LocalGuidelinesAdapter",
    "RxNormService",
    "NABDService",
    "DrugProfile",
    "nabd_drug_search",
    "SourceClient",
    "get_ncbi_client",
]
