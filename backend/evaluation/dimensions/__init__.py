"""
Dimensions package for diagnosis report evaluation.
"""

from .base import BaseDimensionEvaluator
from .clinical_context_relevance import ClinicalContextRelevanceEvaluator
from .hallucination_detection import HallucinationDetectionEvaluator
from .structural_compliance import StructuralComplianceEvaluator
from .clinical_reasoning_consistency import ClinicalReasoningConsistencyEvaluator
from .recommendation_validity import RecommendationValidityEvaluator
from .evidence_grounding import EvidenceGroundingEvaluator

__all__ = [
    "BaseDimensionEvaluator",
    "ClinicalContextRelevanceEvaluator",
    "HallucinationDetectionEvaluator",
    "StructuralComplianceEvaluator",
    "ClinicalReasoningConsistencyEvaluator",
    "RecommendationValidityEvaluator",
    "EvidenceGroundingEvaluator",
]
