"""
Clinical verification, safety rules, guardrails, and grounding validation module for AI-VH.
Provides deterministic safety checks, medication interaction verification,
claim-level factual grounding judges, and calibration tools.
"""

from .grounding import (
    ClaimGroundingChecker,
    ClaimGroundingJudgment,
    GroundingVerdict,
    ReportGroundingResult,
    compute_cohens_kappa,
    compute_confusion_matrix,
    evaluate_calibration,
)
from .rules import (
    AllergyRule,
    ContraindicationRule,
    DeterministicSafetyEngine,
    DoseRangeRule,
    DrugInteractionRule,
    Finding,
    PatientDataContradictionRule,
    RedFlagCoverageRule,
    SafetyConfigurationError,
    SafetyEvaluationResult,
    SafetyRule,
)
from .router import (
    ClinicalVerificationRouter,
    VerificationEnvelope,
    VerificationStatus,
)

__all__ = [
    "ClaimGroundingChecker",
    "ClaimGroundingJudgment",
    "GroundingVerdict",
    "ReportGroundingResult",
    "compute_cohens_kappa",
    "compute_confusion_matrix",
    "evaluate_calibration",
    "AllergyRule",
    "ContraindicationRule",
    "DeterministicSafetyEngine",
    "DoseRangeRule",
    "DrugInteractionRule",
    "Finding",
    "PatientDataContradictionRule",
    "RedFlagCoverageRule",
    "SafetyConfigurationError",
    "SafetyEvaluationResult",
    "SafetyRule",
    "ClinicalVerificationRouter",
    "VerificationEnvelope",
    "VerificationStatus",
]
