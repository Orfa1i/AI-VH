"""
Base classes, schemas, and licence enforcement policy for RAG source adapters.
"""

from abc import ABC, abstractmethod
import logging
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger("vh.rag.sources")

PERMITTED_LICENCES: Set[str] = {
    "cc0",
    "cc-by",
    "cc-by-4.0",
    "cc-by-3.0",
    "cc-by-2.0",
    "cc-by-sa",
    "cc-by-sa-4.0",
    "cc-by-sa-3.0",
    "open access",
    "open-access",
    "us government work",
    "u.s. government work",
    "public domain",
    "fda public domain",
    "nlm public domain",
    "open data commons",
}


class LicenceEnforcementError(Exception):
    """Raised when a source document has an unknown, restricted, or unpermitted licence."""
    pass


def is_licence_permitted(licence: Optional[str]) -> bool:
    """
    Check if the specified licence string is allowed under the AI-VH ingestion policy.
    Rejects None, empty strings, unknown licenses, and all-rights-reserved works.
    """
    if not licence:
        return False
    cleaned = licence.strip().lower()
    if not cleaned or cleaned in {"unknown", "none", "null"}:
        return False

    # Immediate rejection for restrictive terms
    restrictive_terms = ["all rights reserved", "proprietary", "confidential", "restricted", "unauthorized"]
    if any(term in cleaned for term in restrictive_terms):
        return False

    # Check direct set inclusion
    if cleaned in PERMITTED_LICENCES:
        return True

    # Check Creative Commons URIs and patterns
    if "creativecommons.org/publicdomain/zero" in cleaned or "publicdomain/zero" in cleaned:
        return True
    if "creativecommons.org/licenses/by" in cleaned:
        return True
    if "creativecommons.org/licenses/by-sa" in cleaned:
        return True

    # Check substring matches for permitted standards
    for permitted in PERMITTED_LICENCES:
        if permitted in cleaned:
            if "not open" in cleaned or "no cc" in cleaned:
                return False
            return True

    return False


def assert_licence_permitted(licence: Optional[str], doc_id: str = "") -> None:
    """Validate licence, raising LicenceEnforcementError and logging rejection if unpermitted."""
    if not is_licence_permitted(licence):
        msg = f"Document '{doc_id}' rejected due to unpermitted or unknown licence: '{licence}'"
        logger.warning(msg)
        raise LicenceEnforcementError(msg)


class SourceDocument(BaseModel):
    """
    Standardized normalised schema for all ingested clinical and pharmacological source documents.

    Phase 1 (case extraction + Harrison retrieval) extension: optional Harrison
    textbook metadata. All new fields are nullable and never fabricated: when the
    chapter/page cannot be determined from the source record, they stay None.
    Owner: Software Engineer. FROZEN fields above this note are unchanged.
    """
    source_id: str = Field(..., description="Identifier for the source adapter (e.g. pubmed, dailymed)")
    doc_id: str = Field(..., description="Unique document identifier within the source repository")
    title: str = Field(..., description="Document or section title")
    section_path: List[str] = Field(default_factory=list, description="Hierarchical section path")
    locator: str = Field(..., description="Locator URL, anchor, or page reference")
    version: str = Field(default="1.0", description="Document or dataset version")
    published_or_updated_date: str = Field(..., description="Publication or last update date (ISO formatted)")
    evidence_level: str = Field(..., description="Evidence hierarchy level (e.g. 1a, guideline, fda_label)")
    licence: str = Field(..., description="Document licence identifier")
    text: str = Field(..., description="Normalised plain text content of the document or section")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata payload")
    # --- Phase 1 Harrison textbook metadata (all nullable, never invented) ---
    edition: Optional[str] = Field(default=None, description="Textbook edition, e.g. '21st Edition (2022)'")
    chapter_number: Optional[str] = Field(default=None, description="Chapter number when determinable from source")
    chapter_title: Optional[str] = Field(default=None, description="Chapter number/title as given by the source")
    section_heading: Optional[str] = Field(default=None, description="Section heading within the chapter")
    page: Optional[int] = Field(default=None, description="Page number when given by the source; else None")

    class Config:
        extra = "allow"


class SourceSearchHit(BaseModel):
    """
    Phase 1 common search result shape behind the SourceAdapter interface.

    `search(query)` returns a list of these: source_name, chunk_id, metadata,
    text and score. No logic outside the adapter may be Harrison-specific.
    Owner: Software Engineer.
    """
    source_name: str = Field(..., description="Source repository name, e.g. 'harrison'")
    chunk_id: str = Field(..., description="Stable chunk identifier from the source collection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="chunk_id, edition, chapter, section, page(s)")
    text: str = Field(..., description="Full chunk text")
    score: float = Field(default=0.0, description="Retrieval score for this query")


class SourceAdapter(ABC):
    """Abstract base class defining the contract for knowledge source adapters."""
    source_id: str

    @abstractmethod
    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """Parse raw content from the source into normalised SourceDocument objects."""
        pass

    def fetch(self, query_or_id: str) -> List[SourceDocument]:
        """Fetch documents by ID or query. Base implementation raises NotImplementedError for offline use."""
        raise NotImplementedError("Live fetch disabled in offline mode. Use parse with recorded fixtures.")

    def search(self, query: str, top_k: int = 6) -> List[SourceSearchHit]:
        """
        Phase 1 common interface: search(query) -> chunks.

        Default implementation raises NotImplementedError; adapters override it.
        Non-abstract so existing adapters (pubmed, dailymed, guidelines, ...)
        keep instantiating without changes.
        """
        raise NotImplementedError(f"search() not implemented for source '{self.source_id}'")


class RateLimiter:
    """
    Thread-safe token-bucket rate limiter for external source requests.
    """
    def __init__(self, requests_per_second: float = 3.0, burst: int = 10):
        self.rate = float(requests_per_second)
        self.burst = float(burst)
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1, timeout: float = 5.0) -> bool:
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
            time.sleep(0.01)
        return False


class RetryHandler:
    """
    Exponential backoff retry handler for network requests.
    """
    def __init__(self, max_retries: int = 3, backoff_base: float = 0.1, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    break
                sleep_time = self.backoff_base * (self.backoff_factor ** attempt)
                time.sleep(sleep_time)
        if last_exception:
            raise last_exception
