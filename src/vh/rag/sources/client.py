"""
HTTP client helper with rate limiting, retries, and disk caching for knowledge sources.
"""

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional
import httpx
import yaml

from vh.common.config import get_settings
from vh.rag.sources.base import RateLimiter, RetryHandler, logger


class SourceClient:
    """
    HTTP client configured with rate limiting, retries, and optional response caching.
    """
    def __init__(
        self,
        source_name: str,
        base_url: str = "",
        requests_per_second: float = 3.0,
        max_retries: int = 3,
        timeout: float = 10.0,
        cache_dir: Optional[Path] = None,
    ):
        self.source_name = source_name
        self.base_url = base_url
        self.timeout = timeout
        self.limiter = RateLimiter(requests_per_second=requests_per_second)
        self.retry = RetryHandler(max_retries=max_retries)

        settings = get_settings()
        self.cache_dir = Path(cache_dir or settings.RAG_CACHE_DIR) / source_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, url: str, params: Optional[Dict[str, Any]]) -> str:
        key_raw = f"{url}?{sorted((params or {}).items())}"
        return hashlib.sha256(key_raw.encode("utf-8")).hexdigest()

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> str:
        """
        Execute rate-limited GET request with exponential retry and disk caching.
        """
        cache_key = self._cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.cache"

        if use_cache and cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        # Acquire token from rate limiter
        if not self.limiter.acquire(timeout=10.0):
            raise TimeoutError(f"Rate limit exceeded for {self.source_name}")

        def _do_get() -> str:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                return resp.text

        content = self.retry.execute(_do_get)

        if use_cache:
            try:
                cache_file.write_text(content, encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to write cache for {self.source_name}: {e}")

        return content


def get_ncbi_client() -> SourceClient:
    """Factory creating configured NCBI client with API key and rate limits from config."""
    settings = get_settings()
    api_key = settings.NCBI_API_KEY or os.environ.get("NCBI_API_KEY")
    rate = 10.0 if api_key else 3.0
    return SourceClient(
        source_name="ncbi",
        base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        requests_per_second=rate,
        max_retries=3,
        timeout=15.0,
    )
