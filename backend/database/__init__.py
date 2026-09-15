"""
AI Virtual Hospital Database Package
Exposes database repository, connection manager, and models.
"""

from .connection import db_manager, DatabaseConnectionManager
from .repository import db_repo, DatabaseRepository
from .models import (
    ClinicalReportRecord,
    PhysicianReviewRecord,
    DPOFeedbackRecord,
    KnowledgeChunkRecord,
    EncounterRecord,
)

__all__ = [
    "db_manager",
    "DatabaseConnectionManager",
    "db_repo",
    "DatabaseRepository",
    "ClinicalReportRecord",
    "PhysicianReviewRecord",
    "DPOFeedbackRecord",
    "KnowledgeChunkRecord",
    "EncounterRecord",
]
