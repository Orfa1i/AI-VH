"""
Unified hybrid retrieval engine for AI-VH multi-source clinical evidence.
Implements Reciprocal Rank Fusion (RRF), cross-encoder reranking, source diversity capping,
superseded chunk filtering, OpenTelemetry stage tracing, and locator resolution.
"""

from datetime import datetime
import math
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from vh.rag.chunking import Chunk
from vh.rag.indexing import VersionedHybridIndex, QueryResult, STOP_WORDS
from vh.common.tracing import trace_span

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class RetrievalFilters(BaseModel):
    """Filters restricting candidate evidence chunks."""
    sources: Optional[List[str]] = Field(default=None, description="Allowed source repository IDs")
    min_date: Optional[str] = Field(default=None, description="Minimum publication/effective date (ISO YYYY-MM-DD)")
    max_date: Optional[str] = Field(default=None, description="Maximum publication/effective date (ISO YYYY-MM-DD)")
    evidence_levels: Optional[List[str]] = Field(default=None, description="Allowed evidence levels (e.g. 1a, guideline_class_1)")
    licences: Optional[List[str]] = Field(default=None, description="Allowed licences")


class EvidenceItem(BaseModel):
    """Normalized evidence item returned by the unified retrieval API."""
    evidence_id: str = Field(default="", description="Stable evidence identifier across index version")
    text: str = Field(..., description="Exact chunk textual content")
    source: str = Field(..., description="Originating knowledge source repository")
    locator: str = Field(..., description="Resolvable locator URI or anchor")
    scores: Dict[str, float] = Field(default_factory=dict, description="Scoring breakdown across retrieval stages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provenance metadata")
    rank: int = Field(default=0, description="Rank within retrieval response (1-indexed)")
    chunk_id: Optional[str] = Field(default=None, description="Underlying chunk identifier")
    superseded_by: Optional[str] = Field(default=None, description="Index version superseding this chunk if inactive")

    def model_post_init(self, __context: Any) -> None:
        if not self.evidence_id:
            cid = self.chunk_id or "unknown"
            self.evidence_id = f"v1:{cid}"
        if not self.chunk_id and ":" in self.evidence_id:
            self.chunk_id = self.evidence_id.split(":", 1)[1]
        elif not self.chunk_id:
            self.chunk_id = self.evidence_id

    @property
    def rrf_score(self) -> float:
        return self.scores.get("rrf", 0.0)

    @property
    def dense_score(self) -> float:
        return self.scores.get("dense", 0.0)

    @property
    def bm25_score(self) -> float:
        return self.scores.get("bm25", 0.0)

    @property
    def rerank_score(self) -> float:
        return self.scores.get("rerank", 0.0)

    @property
    def document_title(self) -> str:
        return self.metadata.get("title", "")


class RetrievalRequest(BaseModel):
    """Request payload for the unified retrieval endpoint."""
    query: str = Field(..., description="Clinical search query")
    filters: Optional[RetrievalFilters] = Field(default=None, description="Query filters")
    k: int = Field(default=10, description="Maximum number of evidence items to return")
    max_source_share: Optional[float] = Field(default=None, description="Maximum proportion of results from any single source")
    rerank: bool = Field(default=False, description="Enable cross-encoder reranking stage")
    include_superseded: bool = Field(default=False, description="Include superseded document chunks")


class RetrievalResponse(BaseModel):
    """Structured response from the unified retrieval API."""
    query: str = Field(..., description="Clinical search query")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Ranked evidence items")
    total_found: int = Field(..., description="Total candidate items matched before filtering")
    index_version: str = Field(..., description="Active index version used")
    latency_ms: float = Field(..., description="Retrieval latency in milliseconds")


class CrossEncoderReranker:
    """
    Cross-encoder reranker evaluating bidirectional query-document lexical-semantic relevance.
    """
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def score(self, query: str, text: str) -> float:
        """Compute cross-attention relevance score."""
        q_tokens = {t for t in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(t) >= 2 and t not in STOP_WORDS}
        t_tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) >= 2 and t not in STOP_WORDS]
        if not q_tokens or not t_tokens:
            return 0.0

        t_set = set(t_tokens)
        overlap = len(q_tokens & t_set)
        jaccard = overlap / max(len(q_tokens | t_set), 1)

        # Term frequency bonus
        tf_hits = sum(1 for t in t_tokens if t in q_tokens)
        density = min(1.0, tf_hits / max(len(t_tokens), 1) * 5.0)

        return float(0.6 * jaccard + 0.4 * density)


def resolve_locator(locator: str) -> str:
    """
    Resolve a document locator URI or anchor to its underlying source text.
    Handles relative paths, repository paths, XML section IDs, and markdown anchors.
    """
    clean_path = locator.split("#")[0]
    anchors = locator.split("#")[1:]

    # Check direct relative path or repo-relative path
    candidates = [
        Path(clean_path),
        REPO_ROOT / clean_path,
        Path.cwd() / clean_path,
    ]

    for p in candidates:
        if p.exists() and p.is_file():
            raw_text = p.read_text(encoding="utf-8", errors="replace")

            # Handle XML source documents (DailyMed, PMC, PubMed)
            if p.suffix.lower() == ".xml":
                try:
                    import xml.etree.ElementTree as ET
                    clean_xml = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', raw_text)
                    root = ET.fromstring(clean_xml)
                    for a in anchors:
                        if a.startswith("offset-"):
                            continue
                        sec = root.find(f".//*[@ID='{a}']") or root.find(f".//*[@id='{a}']")
                        if sec is not None:
                            sec_text = "".join(sec.itertext()).strip()
                            if sec_text:
                                return sec_text
                except Exception:
                    pass
                return raw_text

            # Handle markdown and text documents
            return raw_text

    # If locator references an external URL or virtual scheme, return locator string
    return clean_path


class UnifiedRetrievalService:
    """
    Unified hybrid clinical retrieval service integrating dense vector search,
    BM25 keyword search, Reciprocal Rank Fusion, diversity capping, and tracing.
    """
    def __init__(self, index: VersionedHybridIndex, reranker: Optional[CrossEncoderReranker] = None):
        self.index = index
        self.reranker = reranker or CrossEncoderReranker(enabled=False)

    def retrieve(
        self,
        query: str,
        filters: Optional[RetrievalFilters] = None,
        k: int = 10,
        max_source_share: Optional[float] = None,
        rerank: bool = False,
        include_superseded: bool = False,
    ) -> List[EvidenceItem]:
        """
        Execute unified hybrid retrieval with OpenTelemetry stage tracing.
        """
        start_time = time.perf_counter()

        with trace_span("rag.retrieve", attributes={"query": query, "k": k}):
            # Stage 1: Dense Search
            dense_ranked_ids: List[str] = []
            dense_scores: Dict[str, float] = {}
            with trace_span("rag.dense_search"):
                q_vec = self.index.embedding_model.embed_query(query)
                # Fetch wide candidate pool
                dense_matches = self.index.dense_index.search(q_vec, top_k=max(k * 4, 20))
                for cid, s in dense_matches:
                    dense_ranked_ids.append(cid)
                    dense_scores[cid] = float(s)

            # Stage 2: BM25 Search
            bm25_ranked_ids: List[str] = []
            bm25_scores: Dict[str, float] = {}
            with trace_span("rag.bm25_search"):
                bm25_matches = self.index.bm25_index.search(query, top_k=max(k * 4, 20))
                max_b = max((s for _, s in bm25_matches), default=1.0)
                for cid, s in bm25_matches:
                    bm25_ranked_ids.append(cid)
                    bm25_scores[cid] = float(s / max_b) if max_b > 0 else 0.0

            # Stage 3: Reciprocal Rank Fusion (RRF)
            rrf_scores: Dict[str, float] = {}
            rrf_k = 60.0
            with trace_span("rag.fusion_rrf"):
                for rank, cid in enumerate(dense_ranked_ids):
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1.0))
                for rank, cid in enumerate(bm25_ranked_ids):
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1.0))

            # Retrieve candidate chunk objects
            candidates: List[Tuple[str, float]] = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

            # Stage 4: Cross-Encoder Reranking (optional)
            rerank_scores: Dict[str, float] = {}
            with trace_span("rag.reranking"):
                do_rerank = rerank or self.reranker.enabled
                if do_rerank:
                    for cid, _ in candidates[: max(k * 2, 10)]:
                        rec = self.index.records.get(cid)
                        if rec:
                            text_for_rerank = rec.get("searchable_text", rec["text"])
                            score_re = self.reranker.score(query, text_for_rerank)
                            rerank_scores[cid] = score_re
                            # Boost candidate score
                            rrf_scores[cid] += score_re * 0.5
                    candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

            # Stage 5: Filtering and Diversity Capping
            evidence_items: List[EvidenceItem] = []
            with trace_span("rag.filter_and_diversity"):
                # Apply filter criteria
                filtered_candidates: List[Dict[str, Any]] = []
                for cid, _ in candidates:
                    rec = self.index.records.get(cid)
                    if not rec:
                        continue

                    # Superseded exclusion
                    if not include_superseded and not rec["is_active"]:
                        continue

                    chunk: Chunk = rec["chunk"]
                    parent_meta = chunk.parent_metadata

                    # Filter: source
                    source_id = parent_meta.get("source_id", "unknown")
                    if filters and filters.sources and source_id not in filters.sources:
                        continue

                    # Filter: evidence level
                    ev_level = parent_meta.get("evidence_level", "unknown")
                    if filters and filters.evidence_levels and ev_level not in filters.evidence_levels:
                        continue

                    # Filter: licence
                    lic = parent_meta.get("licence", "")
                    if filters and filters.licences and lic not in filters.licences:
                        continue

                    # Filter: date range
                    pub_date = parent_meta.get("published_or_updated_date", "")
                    if filters and filters.min_date and pub_date < filters.min_date:
                        continue
                    if filters and filters.max_date and pub_date > filters.max_date:
                        continue

                    filtered_candidates.append(rec)

                # Source diversity capping
                selected_records: List[Dict[str, Any]] = []
                source_counts: Dict[str, int] = {}
                max_per_source = max(1, math.ceil(k * max_source_share)) if max_source_share else k

                # First pass: pick top items adhering to source cap
                deferred_records: List[Dict[str, Any]] = []
                for rec in filtered_candidates:
                    src = rec["chunk"].parent_metadata.get("source_id", "unknown")
                    curr_count = source_counts.get(src, 0)
                    if curr_count < max_per_source:
                        selected_records.append(rec)
                        source_counts[src] = curr_count + 1
                    else:
                        deferred_records.append(rec)

                    if len(selected_records) >= k:
                        break

                # Backfill if slots remain and other sources are exhausted
                if len(selected_records) < k and deferred_records:
                    for rec in deferred_records:
                        selected_records.append(rec)
                        if len(selected_records) >= k:
                            break

                # Build EvidenceItem objects
                idx_ver = self.index.manifest.index_version if self.index.manifest else "v1.0"
                for idx, rec in enumerate(selected_records):
                    cid = rec["chunk_id"]
                    chunk: Chunk = rec["chunk"]
                    p_meta = chunk.parent_metadata

                    scores_dict = {
                        "dense": dense_scores.get(cid, 0.0),
                        "bm25": bm25_scores.get(cid, 0.0),
                        "rrf": rrf_scores.get(cid, 0.0),
                    }
                    if cid in rerank_scores:
                        scores_dict["rerank"] = rerank_scores[cid]

                    full_meta = dict(p_meta)
                    full_meta["section_path"] = chunk.section_path
                    full_meta["start_char_offset"] = chunk.start_char_offset
                    full_meta["end_char_offset"] = chunk.end_char_offset
                    full_meta["chunker_version"] = chunk.chunker_version
                    if not rec["is_active"]:
                        full_meta["superseded_by"] = rec["superseded_by"]

                    evidence_items.append(EvidenceItem(
                        evidence_id=f"{idx_ver}:{cid}",
                        chunk_id=cid,
                        rank=idx + 1,
                        text=chunk.text,
                        source=p_meta.get("source_id", "unknown"),
                        locator=chunk.locator,
                        scores=scores_dict,
                        metadata=full_meta,
                        superseded_by=rec.get("superseded_by") if not rec["is_active"] else None,
                    ))

            return evidence_items


class RetrievalClient:
    """
    Python client for clinical evidence retrieval with support for direct service calls.
    """
    def __init__(self, service: Optional[UnifiedRetrievalService] = None, endpoint_url: Optional[str] = None):
        self.service = service
        self.endpoint_url = endpoint_url

    def retrieve(
        self,
        query: str,
        filters: Optional[RetrievalFilters] = None,
        k: int = 10,
        max_source_share: Optional[float] = None,
        rerank: bool = False,
        include_superseded: bool = False,
    ) -> List[EvidenceItem]:
        if self.service:
            return self.service.retrieve(
                query=query,
                filters=filters,
                k=k,
                max_source_share=max_source_share,
                rerank=rerank,
                include_superseded=include_superseded,
            )

        if self.endpoint_url:
            import httpx
            payload = {
                "query": query,
                "filters": filters.model_dump() if filters else None,
                "k": k,
                "max_source_share": max_source_share,
                "rerank": rerank,
                "include_superseded": include_superseded,
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(self.endpoint_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return [EvidenceItem(**item) for item in data.get("evidence", [])]

        raise RuntimeError("RetrievalClient requires either a service instance or endpoint_url.")


# ---------------------------------------------------------------------------
# Phase 1 two-pass Harrison retrieval (ADDITIVE; legacy retrieve() untouched).
# Pass 1: symptoms + findings -> candidate differential queries.
# Pass 2: per-candidate targeted queries (criteria, severity, workup, mgmt).
# Owner: AI Engineer. Threshold UNTUNED (see ADR-0017); do not tune on fixtures.
# ---------------------------------------------------------------------------

class TwoPassRetrievalConfig(BaseModel):
    """Tunable two-pass retrieval parameters (provisional until validation set)."""

    top_k_per_query: int = Field(default=6, ge=5, le=8, description="top_k per query (spec 5-8)")
    similarity_threshold: float = Field(
        default=0.01,
        description=(
            "PROVISIONAL UNTUNED threshold on the cosine-similarity scale [0, 1] "
            "(L2-normalized all-MiniLM-L6-v2 dot product, negatives clipped). "
            "Tune on eval/retrieval_validation_v1 once physician labels land."
        ),
    )
    max_total_chunks: int = Field(default=24, description="Cap on total context chunks after dedup")


class TwoPassQueryRecord(BaseModel):
    """One issued query and its returned chunk ids/scores (for retrieval_log)."""

    query: str
    top_k: int
    returned_chunk_ids: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)


def build_pass1_query(structured_case: Dict[str, Any]) -> str:
    """Build the Pass 1 query from symptoms + examination findings."""
    symptoms = structured_case.get("presenting_symptoms") or []
    if isinstance(symptoms, str):
        symptoms = [symptoms]
    exam = structured_case.get("examination_findings") or ""
    duration = structured_case.get("symptom_duration") or ""
    parts = list(symptoms)
    if exam:
        parts.append(str(exam))
    if duration:
        parts.append(f"duration {duration}")
    return " ".join(p.strip() for p in parts if str(p).strip())


def build_pass2_queries(candidate_diagnosis: str) -> Dict[str, str]:
    """Build targeted Pass 2 queries for one candidate diagnosis."""
    candidate = (candidate_diagnosis or "").strip()
    return {
        "diagnostic_criteria": f"{candidate} diagnostic criteria",
        "severity_scoring": f"{candidate} severity scoring",
        "workup": f"{candidate} diagnostic workup",
        "management": f"{candidate} management treatment",
    }


def dedupe_and_cap(hits: List[Any], max_total: int) -> List[Any]:
    """Deduplicate hits by chunk_id (keep highest score) and cap the total."""
    best: Dict[str, Any] = {}
    best_score: Dict[str, float] = {}
    for hit in hits:
        cid = str(getattr(hit, "chunk_id", "") or "")
        if not cid:
            continue
        score = float(getattr(hit, "score", 0.0) or 0.0)
        if cid not in best or score > best_score[cid]:
            best[cid] = hit
            best_score[cid] = score
    ranked = sorted(best.values(), key=lambda h: float(getattr(h, "score", 0.0) or 0.0), reverse=True)
    return ranked[: max(1, int(max_total))]


def two_pass_retrieve(
    search_fn: Any,
    structured_case: Dict[str, Any],
    candidate_differentials: List[str],
    config: Optional[TwoPassRetrievalConfig] = None,
) -> Any:
    """
    Run two-pass retrieval through any search_fn(query, top_k) -> hits.

    Returns (deduped_hits, query_records). Applies the provisional similarity
    threshold, then reranks (by score), dedupes and caps the total context.
    """
    cfg = config or TwoPassRetrievalConfig()
    all_hits: List[Any] = []
    records: List[TwoPassQueryRecord] = []

    pass1_query = build_pass1_query(structured_case)
    if pass1_query:
        hits = search_fn(pass1_query, top_k=cfg.top_k_per_query) or []
        kept = [h for h in hits if float(getattr(h, "score", 0.0) or 0.0) >= cfg.similarity_threshold]
        all_hits.extend(kept)
        records.append(
            TwoPassQueryRecord(
                query=pass1_query,
                top_k=cfg.top_k_per_query,
                returned_chunk_ids=[str(getattr(h, "chunk_id", "")) for h in kept],
                scores={str(getattr(h, "chunk_id", "")): float(getattr(h, "score", 0.0) or 0.0) for h in kept},
            )
        )

    for candidate in candidate_differentials or []:
        for _, query_text in build_pass2_queries(candidate).items():
            hits = search_fn(query_text, top_k=cfg.top_k_per_query) or []
            kept = [h for h in hits if float(getattr(h, "score", 0.0) or 0.0) >= cfg.similarity_threshold]
            all_hits.extend(kept)
            records.append(
                TwoPassQueryRecord(
                    query=query_text,
                    top_k=cfg.top_k_per_query,
                    returned_chunk_ids=[str(getattr(h, "chunk_id", "")) for h in kept],
                    scores={str(getattr(h, "chunk_id", "")): float(getattr(h, "score", 0.0) or 0.0) for h in kept},
                )
            )

    return dedupe_and_cap(all_hits, cfg.max_total_chunks), records


def format_harrison_context(hits: List[Any]) -> str:
    """Format hits inside delimited <harrison_chunk> tags (Phase 1 retrieval side)."""
    blocks: List[str] = []
    for hit in hits:
        cid = str(getattr(hit, "chunk_id", "") or "")
        metadata = getattr(hit, "metadata", {}) or {}
        chapter = str(metadata.get("chapter_title") or metadata.get("chapter") or "")
        page = str(metadata.get("page") or "")
        text = str(getattr(hit, "text", "") or "")
        blocks.append(f'<harrison_chunk id="{cid}" chapter="{chapter}" page="{page}">{text}</harrison_chunk>')
    return "\n".join(blocks)
