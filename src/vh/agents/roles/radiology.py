"""
Diagnostic Radiology specialist agent implementation for AI-VH.
Returns study interpretations and diagnostic impressions from released case findings.
Pixel-level inspection dispatches to the STEP-51 reference imaging tools
(deterministic, synthetic-phantom validated, labeled model output).
"""

from typing import Any, Dict, Optional

import numpy as np

from vh.agents.tools.imaging import FractureLocalizationTool, KneeOAGradingTool
from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter
from .base import BaseAgent


class RadiologyAgent(BaseAgent):
    """
    Diagnostic Radiologist Agent. Interprets released imaging studies and
    executes STEP-51 reference imaging tools (labeled model output).
    """

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: str = "radiology@1.0.0",
    ) -> None:
        super().__init__(
            role="radiology",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )

    def interpret_imaging(self, study_code: str) -> Dict[str, Any]:
        """
        Return clinical interpretation and narrative report text for released imaging study.
        """
        clean_code = str(study_code).strip()
        if not self.agent_view.has_released(clean_code):
            res = {
                "study_code": clean_code,
                "status": "unreleased",
                "report_text": "Study has not completed turnaround time or was not ordered.",
            }
            self.record_event(action="interpret_imaging", payload=res)
            return res

        finding = self.agent_view.get_released_result(clean_code)
        res = {
            "study_code": clean_code,
            "status": "interpreted",
            "report_text": str(finding),
            "modality": "diagnostic_imaging",
        }
        self.record_event(action="interpret_imaging", payload=res, result_ref=clean_code)
        return res

    def inspect_image_pixels(
        self, study_code: str, image: Optional[Any] = None, tool: str = "auto"
    ) -> Dict[str, Any]:
        """
        Pixel-level computer vision inspection via STEP-51 reference tools.

        Routes by explicit tool name ("fracture", "knee-oa"/"koa") or, with
        tool="auto", by study-code prefix (KOA*/KNEE* -> knee tool, else
        fracture tool). Outputs are labeled model output, never ground truth.
        """
        clean_code = str(study_code).strip()
        if image is None:
            raise ValueError(
                f"inspect_image_pixels requires an image array for '{clean_code}' "
                f"(no pixels supplied)."
            )
        code_upper = clean_code.upper()
        chosen = tool.strip().lower()
        if chosen == "auto":
            chosen = "knee-oa" if code_upper.startswith("KOA") or "KNEE" in code_upper else "fracture"
        pixels = np.asarray(image)
        if chosen == "fracture":
            output = FractureLocalizationTool().analyze(pixels)
        elif chosen in ("knee-oa", "koa"):
            output = KneeOAGradingTool().analyze(pixels)
        else:
            raise ValueError(
                f"Unknown imaging tool {tool!r} for '{clean_code}'. "
                f"Expected 'fracture', 'knee-oa', or 'auto'."
            )
        res = output.model_dump()
        self.record_event(action="inspect_image_pixels", payload=res, result_ref=clean_code)
        return res
