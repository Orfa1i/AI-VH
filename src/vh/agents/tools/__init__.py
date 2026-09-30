"""Typed imaging-tool contracts for the Radiology agent (STEP 51 / P9.1)."""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

ToolName = Literal["fracture-localization", "knee-oa-grading"]


class ImagingToolOutput(BaseModel):
    """Typed model output. Explicitly labeled, never ground truth."""

    output_id: str = Field(description="Stable id, IMG-<tool>-<hash8>")
    tool: ToolName
    model_version: str = Field(description="Reference implementation version")
    finding: str = Field(description="e.g. fracture_detected, no_fracture, oa_graded")
    location: Optional[Dict[str, int]] = Field(
        default=None, description="Bounding box {xmin, ymin, xmax, ymax} in pixels"
    )
    grade: Optional[int] = Field(default=None, description="Severity grade when applicable")
    confidence: float = Field(ge=0.0, le=1.0)
    interpretation: Literal["model-output"] = "model-output"

    model_config = {"frozen": True}
