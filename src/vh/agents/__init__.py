"""
Multi-agent clinical orchestration module for AI-VH.
Coordinates specialized agents: Triage, Attending, Pharmacist, Lab, and Reviewers.
"""

from .events import EventStore, SimEvent
from .environment import ActionResponse, HospitalEnvironment, OrderStatus

try:
    from backend.simulation.orchestrator import orchestrator
except ImportError:
    orchestrator = None

__all__ = [
    "ActionResponse",
    "EventStore",
    "HospitalEnvironment",
    "OrderStatus",
    "SimEvent",
    "orchestrator",
]
