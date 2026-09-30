"""
Base schemas and abstract rule definition for deterministic clinical safety rules engine.
Defines Finding data model, rule evaluation context, and base SafetyRule protocol.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from vh.generation.report import ClinicalReport


class Finding(BaseModel):
    """Structured clinical safety finding emitted by a deterministic rule."""
    rule_id: str = Field(description="Unique identifier of the rule that generated the finding")
    severity: Literal["critical", "major", "minor"] = Field(
        description="Clinical severity grade: critical (immediate harm), major (adverse event risk), minor (suboptimal)"
    )
    claim_ids: List[str] = Field(
        default_factory=list,
        description="IDs of clinical claims or recommendations in the report linked to this violation"
    )
    message: str = Field(description="Concise, actionable clinical explanation of the safety violation")
    evidence: str = Field(
        default="",
        description="Authoritative source reference or physiological threshold justifying the finding"
    )


class SafetyRule(ABC):
    """Abstract base class for all deterministic clinical safety rules."""
    rule_id: str = "RULE-BASE"
    description: str = "Base clinical safety rule"

    @abstractmethod
    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        """
        Pure function evaluating the report against patient record and safety knowledge.
        Returns a list of structured Finding instances. Must never call an LLM or mutate inputs.
        """
        pass
