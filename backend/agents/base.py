"""
Base Agent Definition
Provides the core structure, memory segregation, and event dispatching for all hospital agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import uuid
import logging
from ..simulation.event_bus import event_bus
from ..simulation.events import HospitalEvent, EventType

logger = logging.getLogger("BaseAgent")


class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, role: str, department: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.department = department
        # Segregated agent episodic memory (actions taken, decisions made)
        self.episodic_memory: List[Dict[str, Any]] = []

    async def emit_event(
        self,
        event_type: EventType,
        encounter_id: str,
        patient_id: str,
        summary: str,
        payload: Optional[Dict[str, Any]] = None,
        receiver_id: Optional[str] = None,
    ) -> HospitalEvent:
        event = HospitalEvent(
            id=f"EVT-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            encounter_id=encounter_id,
            patient_id=patient_id,
            sender_agent_id=self.agent_id,
            receiver_agent_id=receiver_id,
            department=self.department,
            payload=payload or {},
            summary=summary,
        )
        self.episodic_memory.append({
            "event_id": event.id,
            "type": event_type.value,
            "summary": summary,
            "timestamp": event.timestamp.isoformat(),
        })
        await event_bus.publish(event)
        return event

    @abstractmethod
    async def process_event(self, event: HospitalEvent):
        """Handle incoming hospital events."""
        pass
