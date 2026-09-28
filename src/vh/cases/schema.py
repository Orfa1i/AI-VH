"""
Golden case and clinical presentation schemas for AI Virtual Hospital (AI-VH).
Defines Pydantic models for validated benchmark cases, isolated agent views, and ground truth.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class GroundTruth(BaseModel):
    primary_dx: str = Field(description="Primary clinical diagnosis confirmed by attending physician")
    acceptable_differential: List[str] = Field(
        default_factory=list,
        description="List of acceptable alternative diagnoses or differentials"
    )
    expected_workup: List[str] = Field(
        default_factory=list,
        description="Standard-of-care laboratory, imaging, and diagnostic orders required"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Critical symptoms, contraindications, or emergency warning signs"
    )


class SupportingReference(BaseModel):
    source: str = Field(description="Medical textbook, clinical guideline, or PubMed citation")
    locator: str = Field(description="Chapter, section, page, or table identifier")
    note: str = Field(description="Clinical rationale or evidence snippet")


class GoldenCase(BaseModel):
    """Complete golden case specification containing patient presentation and hidden ground truth."""
    case_id: str
    specialty: str
    patient_ref: str
    visible_presentation: Dict[str, Any]
    hidden_results: List[Dict[str, Any]] = Field(default_factory=list)
    ground_truth: GroundTruth
    supporting_references: List[SupportingReference] = Field(default_factory=list)
    status: Literal["draft", "verified"] = "draft"
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None
    version: str = "1.0.0"

    def to_case_view(self) -> "CaseView":
        """Export sanitized agent presentation view, strictly omitting ground truth and hidden results."""
        return CaseView(
            case_id=self.case_id,
            specialty=self.specialty,
            patient_ref=self.patient_ref,
            visible_presentation=self.visible_presentation
        )


class CaseView(BaseModel):
    """Sanitized patient presentation accessible to clinical pipelines and agents."""
    case_id: str
    specialty: str
    patient_ref: str
    visible_presentation: Dict[str, Any]

    model_config = {
        "extra": "forbid"
    }
