"""
FastAPI REST router for unified hybrid clinical retrieval API.
"""

import time
from fastapi import APIRouter, HTTPException, Request

from vh.rag.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    UnifiedRetrievalService,
)

router = APIRouter(prefix="/api/rag", tags=["Retrieval"])


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_evidence(req: RetrievalRequest, request: Request):
    """
    Unified clinical evidence retrieval endpoint.
    Fuses dense semantic similarity and BM25 keywords via Reciprocal Rank Fusion,
    applies source diversity caps, filters out superseded documents, and tracks OpenTelemetry spans.
    """
    start = time.perf_counter()

    # Locate retrieval service from app state or singleton
    service: UnifiedRetrievalService = getattr(request.app.state, "retrieval_service", None)
    if not service:
        # Fallback or initialization
        from vh.rag.indexing import VersionedHybridIndex, get_embedding_model
        from vh.rag.chunking import StructureAwareChunker, ChunkerConfig
        from vh.rag.sources.guidelines import LocalGuidelinesAdapter
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        guidelines_dir = repo_root / "data" / "sources" / "guidelines"

        adapter = LocalGuidelinesAdapter(guidelines_dir=guidelines_dir)
        docs = adapter.load_all()

        chunker = StructureAwareChunker(config=ChunkerConfig())
        chunks = chunker.chunk_documents(docs)

        embedder = get_embedding_model("general")
        idx = VersionedHybridIndex(index_id="default_clinical_idx")
        idx.build(chunks=chunks, embedding_model=embedder, index_version="v1.0")

        service = UnifiedRetrievalService(index=idx)
        request.app.state.retrieval_service = service

    try:
        evidence = service.retrieve(
            query=req.query,
            filters=req.filters,
            k=req.k,
            max_source_share=req.max_source_share,
            rerank=req.rerank,
            include_superseded=req.include_superseded,
        )
        latency = (time.perf_counter() - start) * 1000.0

        return RetrievalResponse(
            query=req.query,
            evidence=evidence,
            total_found=len(evidence),
            index_version=service.index.manifest.index_version if service.index.manifest else "v1.0",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failure: {str(e)}")
