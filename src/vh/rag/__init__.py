"""
Retrieval-Augmented Generation (RAG) module for AI-VH.
Provides vector search, semantic embeddings, and Harrison's medical literature integration.
"""

try:
    from backend.rag.rag_service import rag_service
except ImportError:
    rag_service = None

from vh.rag.chunking import Chunk, ChunkerConfig, StructureAwareChunker
from vh.rag.indexing import (
    IndexManifest,
    EmbeddingModel,
    GeneralEmbeddingModel,
    BiomedicalEmbeddingModel,
    get_embedding_model,
    DenseVectorIndex,
    BM25Index,
    VersionedHybridIndex,
    RetrievedItem,
    QueryResult,
)

__all__ = [
    "rag_service",
    "Chunk",
    "ChunkerConfig",
    "StructureAwareChunker",
    "IndexManifest",
    "EmbeddingModel",
    "GeneralEmbeddingModel",
    "BiomedicalEmbeddingModel",
    "get_embedding_model",
    "DenseVectorIndex",
    "BM25Index",
    "VersionedHybridIndex",
    "RetrievedItem",
    "QueryResult",
]
