"""
Diagnostic Radiology specialist agent implementation for AI-VH.
Returns study interpretations and diagnostic impressions from released case findings.
Image pixel inspection tools are explicitly stubbed with NotImplementedError until Phase 9.
"""

from typing import Any, Dict, Optional

from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter
from .base import BaseAgent


class RadiologyAgent(BaseAgent):
    """
    Diagnostic Radiologist Agent.
    Interprets released imaging and electrocardiogram studies.
    Image pixel processing tools are explicitly stubbed until Phase 9.
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

    def inspect_image_pixels(self, study_code: str) -> Any:
        """
        Pixel-level computer vision inspection tool.
        Explicitly stubbed with NotImplementedError until Phase 9 multi-modal expansion.
        """
        raise NotImplementedError(
            f"Image processing tool 'inspect_image_pixels' for '{study_code}' is stubbed until Phase 9 multi-modal integration."
        )
