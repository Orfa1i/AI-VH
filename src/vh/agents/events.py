"""
Append-only clinical event store and simulation event schema for AI-VH.
Enforces strict immutability, zero-tampering guarantees, and lossless persistence.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field


class SimEvent(BaseModel):
    """
    Immutable representation of an environment or agent action event.
    Schema conforms to: {event_id, run_id, sim_time, wall_time, actor, action, payload, result_ref}.
    """
    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}",
        description="Unique event identifier"
    )
    run_id: str = Field(
        description="Unique simulation run identifier"
    )
    sim_time: int = Field(
        description="Simulation clock time in elapsed minutes from encounter start"
    )
    wall_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of execution"
    )
    actor: str = Field(
        description="Agent or system role executing the action (e.g. doctor, nurse, pharmacist, system)"
    )
    action: str = Field(
        description="Typed action name (e.g. request_vitals, order_lab, order_imaging, consult, submit_report, advance_clock)"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action parameters, query, or metadata"
    )
    result_ref: Optional[str] = Field(
        default=None,
        description="Reference identifier to released result, artifact, or order code if applicable"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class EventStore:
    """
    Append-only repository for simulation events.
    Guarantees:
    1. Events can only be appended.
    2. Modification, update, or deletion of recorded events is strictly forbidden.
    3. Optional atomic file persistence in JSON Lines (JSONL) format.
    """
    def __init__(self, persist_path: Optional[Union[str, Path]] = None) -> None:
        self._events: List[SimEvent] = []
        self._persist_path: Optional[Path] = Path(persist_path).resolve() if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            if self._persist_path.exists():
                with open(self._persist_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str:
                            data = json.loads(line_str)
                            self._events.append(SimEvent(**data))
            else:
                self._persist_path.touch()

    def append(self, event: SimEvent) -> None:
        """Append an event to the in-memory store and optional persistence log."""
        if not isinstance(event, SimEvent):
            raise TypeError(f"Expected SimEvent instance, got {type(event).__name__}")

        self._events.append(event)

        if self._persist_path:
            line = json.dumps(event.model_dump()) + "\n"
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(line)

    def get_events(self, run_id: Optional[str] = None) -> List[SimEvent]:
        """Return a copy of logged events, optionally filtered by run_id."""
        if run_id is None:
            return list(self._events)
        return [evt for evt in self._events if evt.run_id == run_id]

    def get_event(self, event_id: str) -> Optional[SimEvent]:
        """Retrieve a single event by event_id, or None if not found."""
        for evt in self._events:
            if evt.event_id == event_id:
                return evt
        return None

    def __len__(self) -> int:
        return len(self._events)

    def __getitem__(self, index: int) -> SimEvent:
        return self._events[index]

    def __setitem__(self, index: int, value: Any) -> None:
        raise PermissionError("EventStore is strictly append-only: event mutation is forbidden.")

    def __delitem__(self, index: int) -> None:
        raise PermissionError("EventStore is strictly append-only: event deletion is forbidden.")
