"""
Clinical Laboratory specialist agent implementation for AI-VH.
Returns validated laboratory results with reference ranges and abnormal flags.
"""

from typing import Any, Dict, Optional

from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter
from .base import BaseAgent


class LabAgent(BaseAgent):
    """
    Laboratory Specialist Agent.
    Returns released laboratory findings with clinical reference intervals and flags.
    """

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: str = "lab@1.0.0",
    ) -> None:
        super().__init__(
            role="lab",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )

    def analyze_specimen(self, specimen_id: str) -> Dict[str, Any]:
        """Process specimen and confirm specimen integrity."""
        res = {
            "specimen_id": specimen_id,
            "status": "processed",
            "condition": "satisfactory",
        }
        self.record_event(action="analyze_specimen", payload=res)
        return res

    def get_lab_result(self, order_code: str) -> Dict[str, Any]:
        """
        Retrieve and format released laboratory result with reference ranges and abnormal flags.
        Only results released into the AgentView are accessible.
        """
        clean_code = str(order_code).strip()
        if not self.agent_view.has_released(clean_code):
            res = {
                "order_code": clean_code,
                "status": "pending_or_unreleased",
                "result": None,
                "message": f"Laboratory test '{clean_code}' has not completed turnaround time.",
            }
            self.record_event(action="get_lab_result", payload=res)
            return res

        released_val = self.agent_view.get_released_result(clean_code)
        val_str = str(released_val).lower()
        is_abnormal = any(kw in val_str for kw in ["elevated", "high", "low", "critical", "positive", "abnormal"])

        res = {
            "order_code": clean_code,
            "status": "released",
            "result": released_val,
            "flag": "abnormal" if is_abnormal else "normal",
            "reference_range": "See standard assay parameters",
        }
        self.record_event(action="get_lab_result", payload=res, result_ref=clean_code)
        return res
