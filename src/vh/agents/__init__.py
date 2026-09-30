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

try:
    from backend.simulation.orchestrator import orchestrator
except ImportError:
    orchestrator = None

__all__ = [
    "ActionResponse",
    "BaseAgent",
    "DoctorAgent",
    "EventStore",
    "HospitalEnvironment",
    "LabAgent",
    "NurseAgent",
    "OrderStatus",
    "PharmacyAgent",
    "RadiologyAgent",
    "SimEvent",
    "ToolPermissionError",
    "orchestrator",
]
