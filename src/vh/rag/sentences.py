"""
Versioned sentence splitter shared by retrieval and verification (V6/V7 redesign).

Both the evidence resolver (generation side, which extracts supporting_quote
verbatim from cited sentence ranges) and the per-report constrained-decoding
schema (retrieval side, which bounds sentence indices per chunk) MUST use
this splitter so indices always agree. Bumping the version requires a
prompt-version bump alongside it.

Owner: AI Engineer.
"""

import re
from typing import List

SENTENCE_SPLITTER_VERSION = "v1"


def split_sentences_v1(text: str) -> List[str]:
    """Split chunk text into sentences, preserving original wording and order.

    v1: boundary after `.`/`!`/`?` followed by whitespace. Empty fragments
    are dropped; indices are positions in the returned list (0-based).
    """
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [part for part in (p.strip() for p in parts) if part]
