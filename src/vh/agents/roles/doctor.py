"""
Doctor (Attending Physician) agent implementation for AI-VH.
Coordinates diagnostic reasoning, test ordering, specialist consultations, and report submission.
"""

from typing import Any, Dict, List, Optional

from vh.cases.spec import AgentView
from vh.agents.environment import ActionResponse, HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter
from .base import BaseAgent


class DoctorAgent(BaseAgent):
    """
    Attending Physician Agent.
    Authorized to order tests, consult other roles, prescribe, and submit clinical reports.
    Uses MedGemmaAdapter for evidence-grounded generation.
    """

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: str = "doctor@1.0.0",
    ) -> None:
        super().__init__(
            role="doctor",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )

    def request_vitals(self) -> Dict[str, Any]:
        """Request triage and current patient vital signs."""
        if self.environment:
            return self.environment.request_vitals(actor=self.role)
        vitals = dict(self.agent_view.initial_vitals)
        self.record_event(action="request_vitals", payload={"vitals": vitals})
        return vitals

    def order_lab(self, code: str) -> ActionResponse:
        """Place a clinical laboratory test order."""
        if self.environment:
            return self.environment.order_lab(code=code, actor=self.role)
        raise RuntimeError("Environment required to execute order_lab.")

    def order_imaging(self, code: str) -> ActionResponse:
        """Place a diagnostic imaging study order."""
        if self.environment:
            return self.environment.order_imaging(code=code, actor=self.role)
        raise RuntimeError("Environment required to execute order_imaging.")

    def order_medication(self, medication: str, dose: Optional[str] = None) -> Dict[str, Any]:
        """Prescribe a medication."""
        res = {
            "status": "ordered",
            "medication": medication,
            "dose": dose,
        }
        self.record_event(action="order_medication", payload=res)
        return res

    def diagnose(self, diagnosis: str, certainty: str = "suspected") -> Dict[str, Any]:
        """Formulate or document a diagnosis."""
        res = {
            "status": "diagnosed",
            "diagnosis": diagnosis,
            "certainty": certainty,
        }
        self.record_event(action="diagnose", payload=res)
        return res

    def consult(self, role: str, query: str) -> Dict[str, Any]:
        """Request a specialist consultation."""
        if self.environment:
            return self.environment.consult(role=role, query=query, actor=self.role)
        res = {"status": "acknowledged", "role": role, "query": query}
        self.record_event(action="consult", payload=res)
        return res

    def submit_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Submit final clinical report."""
        if self.environment:
            return self.environment.submit_report(report=report, actor=self.role)
        res = {"status": "submitted", "report": report}
        self.record_event(action="submit_report", payload=res)
        return res

    def check_medication_info(self, drug_name: str) -> Dict[str, Any]:
        """Inspect medication information against patient record."""
        if self.environment:
            return self.environment.request_medication_info(drug_name=drug_name, actor=self.role)
        clean = drug_name.strip().lower()
        on_drug = any(clean in m.lower() for m in self.agent_view.current_medications)
        return {
            "query": drug_name,
            "patient_on_drug": on_drug,
            "current_medications": list(self.agent_view.current_medications),
        }

    def check_allergies(self, regimen: str) -> Dict[str, Any]:
        """Check proposed regimen against documented patient allergies."""
        clean = regimen.strip().lower()
        conflicts = [a for a in self.agent_view.allergies if a.lower() in clean]
        return {
            "has_allergy_conflict": len(conflicts) > 0,
            "conflicting_allergies": conflicts,
        }

    def generate_clinical_assessment(self) -> Dict[str, Any]:
        """
        Generate structured clinical assessment using MedGemmaAdapter.
        All LLM generation is routed strictly through the adapter.
        """
        if self.adapter is None:
            self.adapter = MedGemmaAdapter()

        inputs = {
            "case_id": self.agent_view.case_id,
            "presentation": self.agent_view.presentation,
            "vitals": self.agent_view.initial_vitals,
            "history": self.agent_view.history,
            "released_results": [r.model_dump() for r in self.agent_view.released_results],
        }

        result = self.adapter.generate(
            prompt_name_version=self.prompt_template_spec,
            inputs=inputs,
        )

        self.record_event(
            action="generate_clinical_assessment",
            payload={"prompt_spec": self.prompt_template_spec, "inputs_keys": list(inputs.keys())},
        )
        return result if isinstance(result, dict) else result.model_dump()
