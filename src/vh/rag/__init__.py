"""
Retrieval-Augmented Generation (RAG) module for AI-VH.
Provides vector search, semantic embeddings, and Harrison's medical literature integration.
"""

try:
    from backend.rag.rag_service import rag_service
except ImportError:
    rag_service = None

__all__ = ["rag_service"]
