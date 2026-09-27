"""
Clinical text and report generation module for AI-VH.
Provides local MedGemma 4-bit serving and comparative inference pipelines.
"""

try:
    from backend.llm.medgemma_service import medgemma_service, MedGemmaService
except ImportError:
    medgemma_service = None
    MedGemmaService = None

__all__ = ["medgemma_service", "MedGemmaService"]
