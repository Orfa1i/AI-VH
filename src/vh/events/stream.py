"""
Read-only encounter event stream for AI-VH (STEP 46 / P8.1).

The visual hospital is a view on top of the Phase 5 event log: this service
READS events and never writes anything clinical. It offers JSON paging, an
SSE stream with replay-speed control, resume-from-id after reconnects, and a
live tail. There are no write endpoints by construction (proven by test).
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse

from vh.agents.events import EventStore, SimEvent

ROUTE_METHOD_ALLOWLIST = {"GET"}


def events_after(events: List[SimEvent], after_id: Optional[str]) -> List[SimEvent]:
    """Events strictly after a cursor id. Unknown ids raise KeyError (fail closed)."""
    if after_id is None:
        return list(events)
    for index, event in enumerate(events):
        if event.event_id == after_id:
            return list(events[index + 1 :])
    raise KeyError(f"Unknown event id for resume: {after_id!r}")


class EventStream:
    """Ordered, immutable view over an event log with live-tail support."""

    def __init__(
        self,
        events: List[SimEvent],
        store: Optional[EventStore] = None,
        run_id: Optional[str] = None,
    ) -> None:
        self.events: List[SimEvent] = list(events)
        self._store = store
        self._run_id = run_id
        # Tail starts at the beginning: dashboards get history then live
        # updates; resume-from-id is handled by the `after` cursor instead.
        self._cursor = 0

    @classmethod
    def from_event_store(cls, store: EventStore, run_id: Optional[str] = None) -> "EventStream":
        return cls(store.get_events(run_id), store=store, run_id=run_id)

    @classmethod
    def from_replay_bundle(cls, bundle_path: str) -> "EventStream":
        data = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        events = [SimEvent(**item) for item in data.get("event_log", [])]
        return cls(events)

    def tail(self, poll_interval: float = 0.05, max_events: Optional[int] = None) -> Iterator[SimEvent]:
        """Yield appended events in order as they land in the store."""
        if self._store is None:
            raise ValueError("Live tail requires an event store source.")
        yielded = 0
        while max_events is None or yielded < max_events:
            current = self._store.get_events(self._run_id)
            while self._cursor < len(current):
                event = current[self._cursor]
                self._cursor += 1
                yielded += 1
                yield event
                if max_events is not None and yielded >= max_events:
                    return
            if poll_interval > 0:
                time.sleep(poll_interval)


class ReplayController:
    """Deterministic replay of a recorded log at adjustable speed."""

    def __init__(self, events: List[SimEvent], speed: float = float("inf")) -> None:
        if not (speed > 0):
            raise ValueError(f"Replay speed must be positive, got {speed!r}.")
        self.events = list(events)
        self.speed = speed

    def planned_delays(self) -> List[float]:
        """Wall-clock gaps between consecutive events in seconds."""
        if self.speed == float("inf"):
            return [0.0] * max(0, len(self.events) - 1)
        delays: List[float] = []
        for previous, current in zip(self.events, self.events[1:]):
            gap_minutes = max(0, current.sim_time - previous.sim_time)
            delays.append(gap_minutes * 60.0 / self.speed)
        return delays

    def play(self) -> List[SimEvent]:
        """The recorded log, identically ordered (timing applied by the endpoint)."""
        return list(self.events)


def _parse_speed(raw: str) -> float:
    try:
        speed = float(raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"Invalid replay speed: {raw!r}.")
    if not (speed > 0):
        raise HTTPException(status_code=422, detail="Replay speed must be positive.")
    return speed


def _event_frame(event: SimEvent) -> str:
    payload = {
        "run_id": event.run_id,
        "sim_time": event.sim_time,
        "wall_time": event.wall_time,
        "actor": event.actor,
        "payload": event.payload,
        "result_ref": event.result_ref,
    }
    return f"id: {event.event_id}\nevent: {event.action}\ndata: {json.dumps(payload)}\n\n"


def create_event_app(
    store: Optional[EventStore] = None,
    replay_path: Optional[str] = None,
) -> FastAPI:
    """Build the read-only event-stream FastAPI application."""
    if replay_path is not None:
        stream = EventStream.from_replay_bundle(replay_path)
    elif store is not None:
        stream = EventStream.from_event_store(store)
    else:
        stream = EventStream([])

    app = FastAPI(title="AI-VH Event Stream (read-only)")
    app.state.stream = stream

    @app.get("/events")
    def list_events(
        after: Optional[str] = Query(default=None),
        limit: Optional[int] = Query(default=None, ge=1),
    ) -> Dict[str, Any]:
        try:
            selected = events_after(stream.events, after)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        if limit is not None:
            selected = selected[:limit]
        return {"events": [e.model_dump() for e in selected], "count": len(selected)}

    @app.get("/events/stream")
    def stream_events(
        after: Optional[str] = Query(default=None),
        speed: str = Query(default="inf"),
        live: bool = Query(default=False),
        limit: Optional[int] = Query(default=None, ge=1),
    ) -> StreamingResponse:
        try:
            selected = events_after(stream.events, after)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        if live and stream._store is None:
            raise HTTPException(status_code=400, detail="Live tail needs a store source.")
        if not live and limit is not None:
            selected = selected[:limit]
        rate = _parse_speed(speed)

        def _generate() -> Iterator[str]:
            if live:
                # Stream arrivals incrementally; the connection stays open for
                # new events (proper live semantics) with a bounded poll.
                assert stream._store is not None
                for event in stream.tail(poll_interval=0.5, max_events=limit or 1000):
                    yield _event_frame(event)
                return
            controller = ReplayController(selected, speed=rate)
            delays = controller.planned_delays()
            for index, event in enumerate(controller.play()):
                if index > 0 and delays[index - 1] > 0:
                    time.sleep(min(delays[index - 1], 30.0))
                yield _event_frame(event)

        return StreamingResponse(_generate(), media_type="text/event-stream")

    return app
