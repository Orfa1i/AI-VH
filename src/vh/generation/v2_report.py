"""
Phase 2 assessment schema for AI-VH (prompt FOR UPDATE/02_Phase2).

Single JSON object produced by MedGemma from the structured case + Harrison
chunks. Grounding counts and fractions are computed by code (Phase 3), never
trusted from the model.

Owner: AI Engineer. Legacy v1 ClinicalReport (report.py) is untouched.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

EvidenceSource = Literal[
    "harrison",
    "braunwald",
    "nabd_rxnorm",
    "dailymed",
    "openfda",
    "pubmed",
    "model_knowledge",
]
Certainty = Literal["confirmed", "probable", "provisional"]
DispositionSetting = Literal["outpatient", "ward", "HDU", "ICU"]
WorkupPriority = Literal["stat", "urgent", "routine"]

CONFIDENCE_BANDS = {
    "provisional": (0.0, 0.5),
    "probable": (0.5, 0.85),
    "confirmed": (0.85, 1.0),
}


class EvidenceItem(BaseModel):
    """One cited evidence unit: Harrison chunk or labelled model knowledge."""

    source: EvidenceSource = Field(description="harrison | model_knowledge (extensible enum)")
    chunk_id: Optional[str] = Field(default=None, description="H- chunk id, or null for model_knowledge")
    supporting_quote: Optional[str] = Field(
        default=None, description="Verbatim quote from the chunk (max 40 words), or null"
    )
    note: Optional[str] = Field(default=None, description="Optional annotator note")


class DifferentialDx(BaseModel):
    """One differential diagnosis with for/against findings and evidence."""

    diagnosis: str
    icd10: str = Field(description="ICD-10 code for the diagnosis")
    probability: float = Field(ge=0.0, le=1.0)
    supporting_findings: List[str] = Field(default_factory=list)
    against_findings: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)


class FinalDiagnosis(BaseModel):
    """Single final diagnosis with certainty band and confidence."""

    diagnosis: str = Field(description="Specific named condition")
    icd10: str = Field(description="ICD-10 code for the diagnosis")
    certainty: Certainty
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[EvidenceItem] = Field(default_factory=list)


class SeverityScore(BaseModel):
    """Validated severity score with components, value and interpretation."""

    score_name: str = Field(description="e.g. CURB-65")
    components: Dict[str, Any] = Field(default_factory=dict)
    value: str = Field(description="Computed score value")
    interpretation: str = Field(description="What the score implies for this patient")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class WorkupItem(BaseModel):
    """One prioritised diagnostic workup item."""

    test: str
    priority: WorkupPriority
    rationale: str = Field(description="Short patient-specific rationale")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class TreatmentItem(BaseModel):
    """One treatment item with full dosing and patient-specific rationale."""

    item: str
    dose_route_frequency_duration: str = Field(description="Specific dose, route, frequency and duration")
    rationale: str = Field(description="Short patient-specific rationale")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class Disposition(BaseModel):
    """Disposition setting with rationale and evidence."""

    setting: DispositionSetting
    rationale: str = Field(description="Short patient-specific rationale")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class AssessmentReport(BaseModel):
    """Phase 2 single-JSON clinical assessment (MedGemma output)."""

    report_id: str
    case_summary: str = Field(description="2-4 sentences")
    chief_complaint: str = Field(description="Symptoms + duration, never a diagnosis")
    differential_diagnosis: List[DifferentialDx] = Field(min_length=1)
    final_diagnosis: FinalDiagnosis
    severity_assessment: List[SeverityScore] = Field(default_factory=list)
    clinical_reasoning: str = Field(description="Plain prose 150-400 words, claims tagged [H:chunk_id] or [MG]")
    workup: List[WorkupItem] = Field(default_factory=list)
    treatment: List[TreatmentItem] = Field(default_factory=list)
    disposition: Disposition
    red_flags: List[str] = Field(default_factory=list)
    follow_up: str = ""
    missing_data: List[str] = Field(default_factory=list)
    conflicts_noted: List[str] = Field(
        default_factory=list, description="Where Harrison and model knowledge disagree"
    )
    prompt_version: str = Field(description="Prompt name@version that produced this report")

    @field_validator("differential_diagnosis")
    @classmethod
    def _differential_bounded(cls, items: List[DifferentialDx]) -> List[DifferentialDx]:
        if len(items) > 5:
            raise ValueError(f"differential_diagnosis must hold 3-5 entries, got {len(items)}")
        return items

    @model_validator(mode="after")
    def _probabilities_consistent(self) -> "AssessmentReport":
        total = sum(d.probability for d in self.differential_diagnosis)
        if total > 1.0 + 1e-6:
            raise ValueError(f"differential probabilities must sum to <= 1, got {total}")
        return self

    @model_validator(mode="after")
    def _confidence_matches_certainty(self) -> "AssessmentReport":
        low, high = CONFIDENCE_BANDS[self.final_diagnosis.certainty]
        conf = self.final_diagnosis.confidence
        if self.final_diagnosis.certainty == "provisional" and conf > high + 1e-6:
            raise ValueError(f"provisional certainty requires confidence <= {high}, got {conf}")
        if self.final_diagnosis.certainty == "confirmed" and conf < low - 1e-6:
            raise ValueError(f"confirmed certainty requires confidence >= {low}, got {conf}")
        if self.final_diagnosis.certainty == "probable" and not (low - 1e-6 <= conf <= high + 1e-6):
            raise ValueError(f"probable certainty requires confidence in [{low}, {high}], got {conf}")
        return self


def validate_assessment(report: AssessmentReport) -> bool:
    """Schema-level integrity check (grounding V-checks belong to Phase 3)."""
    if not isinstance(report, AssessmentReport):
        raise TypeError("validate_assessment expects an AssessmentReport")
    total = sum(d.probability for d in report.differential_diagnosis)
    if total > 1.0 + 1e-6:
        raise ValueError(f"differential probabilities sum to {total} (> 1)")
    return True


def export_assessment_json_schema() -> Dict[str, Any]:
    """JSON Schema for the Phase 2 assessment (constrained-decoding capable stacks)."""
    return AssessmentReport.model_json_schema()
