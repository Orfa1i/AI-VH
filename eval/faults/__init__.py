"""
Verification fault-injection suite for AI Virtual Hospital (AI-VH).
Provides models, configuration, synthetic generation, and evaluation scoring
for auditing runtime guardrails and verification layers.
"""

from .config import load_fault_classification
from .generator import FaultGenerator
from .models import (
    CleanCase,
    CorruptedCase,
    FaultClassificationConfig,
    FaultClassificationInfo,
    FaultEvaluationReport,
    FaultSet,
    FaultSeverity,
    FaultType,
)
from .scorer import FaultInjectionScorer

__all__ = [
    "CleanCase",
    "CorruptedCase",
    "FaultClassificationConfig",
    "FaultClassificationInfo",
    "FaultEvaluationReport",
    "FaultGenerator",
    "FaultInjectionScorer",
    "FaultSet",
    "FaultSeverity",
    "FaultType",
    "load_fault_classification",
]
