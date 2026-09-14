"""
Nurse Agent Definition
Handles patient triage, vital signs measurement, and clinical handoff to the attending doctor.
"""

from typing import Dict, Any, Optional
import logging
from .base import BaseAgent
from ..simulation.events import HospitalEvent, EventType
from ..clinical.tools import ClinicalToolkit

logger = logging.getLogger("NurseAgent")


class NurseAgent(BaseAgent):
    def __init__(self, agent_id: str = "nurse_sarah", name: str = "Sarah Jenkins, RN"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role="TRIAGE_NURSE",
            department="NURSE_STATION"
        )

    async def triage_patient(self, encounter_id: str, toolkit: ClinicalToolkit):
        logger.info(f"Nurse {self.name} starting triage for patient {toolkit.ground_truth.name}")
        
        # 1. Start Triage
        await self.emit_event(
            event_type=EventType.NURSE_TRIAGE_STARTED,
            encounter_id=encounter_id,
            patient_id=toolkit.ground_truth.id,
            summary=f"Nurse {self.name} brought patient {toolkit.ground_truth.name} into Triage Bay 1",
            payload={"nurse": self.name}
        )

        # 2. Acquire and log vital signs
        vitals = toolkit.get_vital_signs()
        await self.emit_event(
            event_type=EventType.VITALS_RECORDED,
            encounter_id=encounter_id,
            patient_id=toolkit.ground_truth.id,
            summary=f"Nurse {self.name} recorded vitals: {vitals.summary()}",
            payload=vitals.model_dump()
        )

        # 3. Complete Triage & Escalate to Internal Medicine Doctor
        acuity = toolkit.ground_truth.triage_acuity.value
        await self.emit_event(
            event_type=EventType.TRIAGE_COMPLETED,
            encounter_id=encounter_id,
            patient_id=toolkit.ground_truth.id,
            summary=f"Nurse {self.name} assigned acuity {acuity} and paged Internal Medicine Attending",
            payload={
                "acuity": acuity,
                "assigned_doctor": "Dr. Marcus Vance, MD (Internal Medicine)"
            }
        )

    async def process_event(self, event: HospitalEvent):
        pass
