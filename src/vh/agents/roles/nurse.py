"""
Nurse agent implementation for AI-VH.
Handles vitals acquisition, patient monitoring, and bedside observations.
Strictly prohibited from ordering medications or formulating diagnoses.
"""

from typing import Any, Dict, Optional

from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter
from .base import BaseAgent, ToolPermissionError


class NurseAgent(BaseAgent):
    """
    Clinical Nurse Agent.
    Responsible for vitals, observations, and bedside nursing notes.
    Cannot order medications or formulate diagnoses.
    """

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: str = "nurse@1.0.0",
    ) -> None:
        super().__init__(
            role="nurse",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )

    def request_vitals(self) -> Dict[str, Any]:
        """Obtain current patient vital signs."""
        if self.environment:
            return self.environment.request_vitals(actor=self.role)
        vitals = dict(self.agent_view.initial_vitals)
        self.record_event(action="request_vitals", payload={"vitals": vitals})
        return vitals

    def record_vitals(self, vitals: Dict[str, Any]) -> Dict[str, Any]:
        """Record newly observed vital signs."""
        res = {"status": "recorded", "vitals": vitals}
        self.record_event(action="record_vitals", payload=res)
        return res

    def record_observation(self, note: str) -> Dict[str, Any]:
        """Record bedside clinical observation."""
        res = {"status": "recorded", "observation": note}
        self.record_event(action="record_observation", payload=res)
        return res

    def record_nursing_notes(self, notes: str) -> Dict[str, Any]:
        """Record official nursing shift or progress note."""
        res = {"status": "recorded", "notes": notes}
        self.record_event(action="record_nursing_notes", payload=res)
        return res

    def order_medication(self, medication: str, **kwargs: Any) -> Any:
        """Blocked directly at the method level and tool layer."""
        return self.invoke_tool("order_medication", medication=medication, **kwargs)

    def diagnose(self, diagnosis: str, **kwargs: Any) -> Any:
        """Blocked directly at the method level and tool layer."""
        return self.invoke_tool("diagnose", diagnosis=diagnosis, **kwargs)
