"""
Deterministic clinical safety rules package for AI Virtual Hospital (AI-VH).
Provides zero-LLM deterministic rules for clinical verification:
- Base Finding and SafetyRule definitions
- Allergy checking with RxNorm class hierarchy
- Contraindication checking against active conditions
- Drug-drug interaction checking
- Dose range and renal adjustment checking
- Patient data contradiction auditing
- Emergency physiological red-flag coverage
- Deterministic safety engine coordinator
"""

from .base import Finding, SafetyRule
from .allergy import AllergyRule
from .contraindication import ContraindicationRule
from .interaction import DrugInteractionRule
from .dose import DoseRangeRule
from .contradiction import PatientDataContradictionRule
from .red_flags import RedFlagCoverageRule
from .engine import (
    DeterministicSafetyEngine,
    SafetyConfigurationError,
    SafetyEvaluationResult,
)

__all__ = [
    "Finding",
    "SafetyRule",
    "AllergyRule",
    "ContraindicationRule",
    "DrugInteractionRule",
    "DoseRangeRule",
    "PatientDataContradictionRule",
    "RedFlagCoverageRule",
    "DeterministicSafetyEngine",
    "SafetyConfigurationError",
    "SafetyEvaluationResult",
]
