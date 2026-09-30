"""
Multi-agent clinical orchestration module for AI-VH.
Coordinates specialized agents: Triage, Attending, Pharmacist, Lab, and Reviewers.
"""

from .events import EventStore, SimEvent
from .environment import ActionResponse, HospitalEnvironment, OrderStatus

from .roles import (
    BaseAgent,
    DoctorAgent,
    LabAgent,
    NurseAgent,
    PharmacyAgent,
    RadiologyAgent,
    ToolPermissionError,
)

from .orchestrator import (
    EncounterBudget,
    EncounterState,
    EncounterStatus,
    EncounterStep,
    HospitalOrchestrator,
    LoopDetectionConfig,
)

try:
    from backend.simulation.orchestrator import orchestrator
except ImportError:
    orchestrator = None

__all__ = [
    "ActionResponse",
    "BaseAgent",
    "DoctorAgent",
    "EncounterBudget",
    "EncounterState",
    "EncounterStatus",
    "EncounterStep",
    "EventStore",
    "HospitalEnvironment",
    "HospitalOrchestrator",
    "LabAgent",
    "LoopDetectionConfig",
    "NurseAgent",
    "OrderStatus",
    "PharmacyAgent",
    "RadiologyAgent",
    "SimEvent",
    "ToolPermissionError",
    "orchestrator",
]
