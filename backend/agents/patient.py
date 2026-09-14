"""
Patient Agent Definition
Autonomous patient agent with dynamic hidden clinical state, personality, and symptom disclosure.
"""

from typing import Dict, Any, Optional
import logging
from .base import BaseAgent
from ..simulation.events import HospitalEvent, EventType
from ..clinical.cases import PatientGroundTruth

logger = logging.getLogger("PatientAgent")


class PatientAgent(BaseAgent):
    def __init__(self, ground_truth: PatientGroundTruth):
        super().__init__(
            agent_id=f"patient_{ground_truth.id.lower()}",
            name=ground_truth.name,
            role="PATIENT",
            department="EMERGENCY_DEPARTMENT"
        )
        self.ground_truth = ground_truth
        self.revealed_symptoms: Dict[str, str] = {}
        self.is_checked_in = False

    async def arrive(self, encounter_id: str):
        self.is_checked_in = True
        await self.emit_event(
            event_type=EventType.PATIENT_ARRIVED,
            encounter_id=encounter_id,
            patient_id=self.ground_truth.id,
            summary=f"Patient {self.name} ({self.ground_truth.age}yo {self.ground_truth.sex}) entered ER with complaint: '{self.ground_truth.chief_complaint}'",
            payload={
                "name": self.name,
                "age": self.ground_truth.age,
                "sex": self.ground_truth.sex,
                "chief_complaint": self.ground_truth.chief_complaint,
                "acuity": self.ground_truth.triage_acuity.value,
            }
        )

    async def answer_inquiry(self, question: str, encounter_id: str) -> str:
        q_lower = question.lower()
        if "pain" in q_lower or "hurt" in q_lower:
            response = f"The pain started about 2 hours ago. It's a heavy pressure right in my chest and goes into my left arm and jaw. Rated {self.ground_truth.baseline_vitals.pain_score}/10."
        elif "medication" in q_lower or "drug" in q_lower:
            response = f"I take {', '.join(self.ground_truth.medications)}."
        elif "allergy" in q_lower or "allergic" in q_lower:
            response = f"I am allergic to {', '.join(self.ground_truth.allergies)}."
        elif "history" in q_lower or "past" in q_lower or "condition" in q_lower:
            response = f"I have a history of {', '.join(self.ground_truth.past_medical_history)}."
        else:
            response = self.ground_truth.history_of_present_illness

        await self.emit_event(
            event_type=EventType.PATIENT_INTERVIEWED,
            encounter_id=encounter_id,
            patient_id=self.ground_truth.id,
            summary=f"Patient {self.name} answered: '{response[:100]}...'",
            payload={"question": question, "response": response}
        )
        return response

    async def process_event(self, event: HospitalEvent):
        pass
