"""
Data models for the verification fault-injection suite in AI-VH.
Defines schemas for fault classifications, corrupted cases, fault sets, and evaluation reports.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from vh.generation.report import ClinicalReport


class FaultType(str, Enum):
    """The 9 canonical verification fault types."""
    WRONG_EVIDENCE_ID = "wrong_evidence_id"
    SWAPPED_EVIDENCE = "swapped_evidence"
    FABRICATED_CLAIM = "fabricated_claim"
    ALLERGY_CONFLICT = "allergy_conflict"
    CONTRAINDICATED_DRUG = "contraindicated_drug"
    OVERDOSE = "overdose"
    RENAL_DOSE_ERROR = "renal_dose_error"
    CONTRADICTION_OF_VITALS_LABS = "contradiction_of_vitals_labs"
    MISSED_RED_FLAG = "missed_red_flag"


class FaultSeverity(str, Enum):
    """Clinical severity classification for injected faults."""
    CRITICAL = "critical"
    NON_CRITICAL = "non_critical"


class FaultClassificationInfo(BaseModel):
    """Metadata describing a single fault type classification."""
    severity: FaultSeverity
    category: str
    description: str
    clinical_risk: str


class FaultClassificationConfig(BaseModel):
    """Configuration mapping all fault types to severity and metadata."""
    config_id: str
    version: str
    description: str
    classifications: Dict[FaultType, FaultClassificationInfo]


class CorruptedCase(BaseModel):
    """A labelled corrupted test case derived from a clean clinical report."""
    case_id: str
    clean_report: ClinicalReport
    corrupted_report: ClinicalReport
    patient_record: Dict[str, Any]
    retrieved_chunks: Dict[str, str]
    fault_type: FaultType
    severity: FaultSeverity
    description: str
    mutation_details: Dict[str, Any] = Field(default_factory=dict)


class CleanCase(BaseModel):
    """An uncorrupted clinical case used to audit false-flag rate."""
    case_id: str
    report: ClinicalReport
    patient_record: Dict[str, Any]
    retrieved_chunks: Dict[str, str]


class FaultSet(BaseModel):
    """A versioned set of clean and corrupted cases."""
    version: str
    created_at: str
    clean_cases: List[CleanCase]
    corrupted_cases: List[CorruptedCase]


class FaultEvaluationReport(BaseModel):
    """Comprehensive evaluation results comparing verification performance against thresholds."""
    run_id: str
    total_cases: int
    total_corrupted: int
    total_clean: int
    detection_by_fault_type: Dict[str, Dict[str, Any]]
    critical_detection_rate: float
    noncritical_detection_rate: float
    false_flag_rate: float
    thresholds: Dict[str, float]
    passed: bool
    evaluated_at: str
