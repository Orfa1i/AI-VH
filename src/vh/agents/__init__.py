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
from .replay import (
    RecordingAdapter,
    ReplayAdapter,
    ReplayBundle,
    TranscriptEntry,
    hash_event_log,
    load_bundle,
    record_encounter,
    replay_encounter,
    save_bundle,
)
from .scoring import EncounterScore, EncounterScorer, aggregate_encounter_scores

try:
    from backend.simulation.orchestrator import orchestrator
except ImportError:
    orchestrator = None

__all__ = [
    "ActionResponse",
    "BaseAgent",
    "DoctorAgent",
    "EncounterBudget",
    "EncounterScore",
    "EncounterScorer",
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
    "RecordingAdapter",
    "ReplayAdapter",
    "ReplayBundle",
    "SimEvent",
    "ToolPermissionError",
    "TranscriptEntry",
    "aggregate_encounter_scores",
    "hash_event_log",
    "load_bundle",
    "orchestrator",
    "record_encounter",
    "replay_encounter",
    "save_bundle",
]
