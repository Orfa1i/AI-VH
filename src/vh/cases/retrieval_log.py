"""
Phase 1 retrieval log: stored proof that retrieval ran before generation.

Every report carries the queries issued, returned chunk_ids, scores and the
full chunk text. Generation must never run without a retrieval_log; the guard
in vh.generation.pipeline refuses the call otherwise.

Owner: Software Engineer. Storage uses vh.common.artifacts registry without
modifying artifacts.py (FROZEN in Phase 1).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalQueryRecord(BaseModel):
    """One retrieval query within a two-pass run."""

    query: str = Field(description="Query text sent to the source adapter")
    top_k: int = Field(description="Requested top_k for this query")
    returned_chunk_ids: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)


class RetrievalLogChunk(BaseModel):
    """Stored chunk snapshot: metadata + full text + score."""

    chunk_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    text: str = ""
    score: float = 0.0


class RetrievalLog(BaseModel):
    """Stored retrieval proof attached to every Phase 1 report."""

    case_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    queries: List[RetrievalQueryRecord] = Field(default_factory=list)
    chunks: Dict[str, RetrievalLogChunk] = Field(default_factory=dict)
    status: str = Field(default="SUFFICIENT", description="SUFFICIENT or INSUFFICIENT_GROUNDING")


class MissingRetrievalLogError(RuntimeError):
    """Raised when generation is attempted without a retrieval_log."""


def new_retrieval_log(case_id: str) -> RetrievalLog:
    """Create an empty retrieval log for a case."""
    return RetrievalLog(case_id=case_id)


def record_query(
    log: RetrievalLog,
    query: str,
    top_k: int,
    hits: List[Any],
    chunk_text_fn: Optional[Any] = None,
) -> RetrievalLog:
    """
    Append one query record plus chunk snapshots to the log.

    hits: list of SourceSearchHit (or anything with chunk_id/metadata/text/score).
    Never raises on odd hit shapes; stores what is present.
    """
    returned: List[str] = []
    scores: Dict[str, float] = {}
    for hit in hits:
        cid = str(getattr(hit, "chunk_id", "") or "")
        if not cid:
            continue
        score = float(getattr(hit, "score", 0.0) or 0.0)
        returned.append(cid)
        scores[cid] = score
        metadata = getattr(hit, "metadata", {}) or {}
        text = getattr(hit, "text", "") or ""
        if chunk_text_fn is not None:
            try:
                text = chunk_text_fn(hit) or text
            except Exception:
                pass
        if cid not in log.chunks:
            log.chunks[cid] = RetrievalLogChunk(
                chunk_id=cid,
                metadata=dict(metadata) if isinstance(metadata, dict) else {"raw": metadata},
                text=str(text),
                score=score,
            )
    log.queries.append(RetrievalQueryRecord(query=query, top_k=top_k, returned_chunk_ids=returned, scores=scores))
    return log


def assert_retrieval_log_present(log: Optional[RetrievalLog]) -> RetrievalLog:
    """
    Hard guard: no retrieval_log means generation is refused.

    Retrieval must have RUN (at least one query recorded). Zero passing
    chunks is allowed: the pipeline then returns INSUFFICIENT_GROUNDING
    instead of generating.
    """
    if log is None or not isinstance(log, RetrievalLog):
        raise MissingRetrievalLogError("Generation refused: no retrieval_log provided.")
    if not log.queries:
        raise MissingRetrievalLogError("Generation refused: retrieval_log has no recorded queries.")
    return log
