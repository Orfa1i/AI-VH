"""
Diagnosis Report Evaluation Models for AI Virtual Hospital (AI-VH).
Defines schemas for independent multi-stage evaluation dimensions,
severities, statuses, and aggregate results.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EvaluationSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvaluationStatus(str, Enum):
    PASSED = "PASSED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class DimensionEvaluationResult(BaseModel):
    """Result of an individual evaluation dimension check."""
    dimension: str = Field(description="Unique identifier of the evaluation dimension")
    display_name: str = Field(description="Human-readable title of the dimension")
    passed: bool = Field(description="True if dimension check passed, False otherwise")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score 0.0 to 1.0")
    explanation: str = Field(description="Concise clinical rationale for the evaluation verdict")
    detected_issues: List[str] = Field(default_factory=list, description="Specific identified defects or anomalies")
    severity: EvaluationSeverity = Field(default=EvaluationSeverity.INFO, description="Highest severity level found in this check")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting telemetry, patient values, or citation records")


class AggregateEvaluationResult(BaseModel):
    """Comprehensive multi-dimensional evaluation report for a clinical diagnosis report."""
    evaluation_id: str = Field(description="Unique evaluation execution ID")
    report_id: str = Field(description="Target clinical report ID")
    encounter_id: str = Field(description="Associated clinical encounter ID")
    patient_id: str = Field(description="Patient identifier")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite clinical evaluation score (0.0 - 1.0)")
    dimension_scores: Dict[str, float] = Field(default_factory=dict, description="Score mapped per dimension name")
    dimensions: Dict[str, DimensionEvaluationResult] = Field(default_factory=dict, description="Detailed per-dimension results")
    failed_checks: List[str] = Field(default_factory=list, description="List of dimensions that did not pass")
    severity: EvaluationSeverity = Field(description="Highest severity observed across all failed checks")
    final_status: EvaluationStatus = Field(description="PASSED | FLAGGED | REJECTED")
    passed: bool = Field(description="True only if final_status is PASSED")
    fail_reasons: List[str] = Field(default_factory=list, description="List of primary reasons causing failure or flagging")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Evaluation timestamp")
    evaluator_version: str = Field(default="evaluation-pipeline/1.0.0", description="Evaluation engine release version")
