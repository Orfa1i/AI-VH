"""
Clinical simulation event bus and event streaming module for AI-VH.
Provides event pub/sub, WebSocket streaming, and deterministic replay logs.
"""

try:
    from backend.simulation.event_bus import event_bus
    from backend.simulation.events import HospitalEvent, EventType
except ImportError:
    event_bus = None
    HospitalEvent = None
    EventType = None

__all__ = ["event_bus", "HospitalEvent", "EventType"]
