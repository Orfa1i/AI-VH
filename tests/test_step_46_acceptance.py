"""
Acceptance tests for STEP 46 (P8.1): read-only event stream API.

Criteria (from plan/prompts/phase-8-virtual-hospital/STEP-46_P8.1_event-stream-api.md):
1. Ordering guaranteed; resume works after a forced disconnect.
2. No write endpoints exist on this service.
Plus: replay mode at adjustable speed; unknown resume cursors fail closed.
"""

import json
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from vh.agents.events import EventStore, SimEvent
from vh.events.stream import (
    EventStream,
    ReplayController,
    create_event_app,
    events_after,
)


def _make_store(n: int = 5, run_id: str = "run-p46") -> EventStore:
    store = EventStore()
    for i in range(n):
        store.append(
            SimEvent(
                run_id=run_id,
                sim_time=i * 10,
                actor="doctor" if i % 2 == 0 else "system",
                action=f"step_{i}",
                payload={"index": i},
                result_ref=None,
            )
        )
    return store


@pytest.fixture
def client(tmp_path):
    store = _make_store()
    app = create_event_app(store=store)
    with TestClient(app) as test_client:
        yield test_client


def test_event_ordering_guaranteed(client: TestClient):
    """Criterion 1: JSON paging and SSE both preserve append order."""
    page = client.get("/events").json()
    assert [e["payload"]["index"] for e in page["events"]] == [0, 1, 2, 3, 4]
    assert page["events"][0]["sim_time"] == 0

    resp = client.get("/events/stream?speed=inf")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    ids = [
        line.split("id: ", 1)[1]
        for line in resp.text.splitlines()
        if line.startswith("id: ")
    ]
    assert ids == [e["event_id"] for e in page["events"]]
    assert len(set(ids)) == len(ids)


def test_resume_after_forced_disconnect(client: TestClient):
    """Criterion 1: reconnecting with after=<id> yields exactly the remainder."""
    page = client.get("/events").json()
    events = page["events"]
    cutoff = events[1]["event_id"]

    # Simulate a dropped client that only saw the first two events.
    resumed = client.get(f"/events?after={cutoff}").json()
    assert [e["payload"]["index"] for e in resumed["events"]] == [2, 3, 4]

    stream = client.get(f"/events/stream?after={cutoff}&speed=inf").text
    streamed_ids = [l.split("id: ", 1)[1] for l in stream.splitlines() if l.startswith("id: ")]
    assert streamed_ids == [e["event_id"] for e in events[2:]]


def test_unknown_resume_cursor_fails_closed(client: TestClient):
    """Unknown event ids never silently restart or truncate the log."""
    resp = client.get("/events?after=evt_does_not_exist")
    assert resp.status_code == 404
    resp = client.get("/events/stream?after=evt_does_not_exist&speed=inf")
    assert resp.status_code == 404


def test_no_write_endpoints_exist(client: TestClient):
    """Criterion 2: the service is read-only; CME-style audit of routes."""
    from vh.events.stream import ROUTE_METHOD_ALLOWLIST

    assert ROUTE_METHOD_ALLOWLIST == {"GET"}
    for route in client.app.routes:
        methods = set(getattr(route, "methods", set()) or set())
        methods.discard("HEAD")
        methods.discard("OPTIONS")
        assert methods <= {"GET"}, f"write method on {getattr(route, 'path', route)}: {methods}"

    for method in ("post", "put", "patch"):
        resp = getattr(client, method)("/events", json={})
        assert resp.status_code in (404, 405), f"{method} unexpectedly allowed"
    resp = client.delete("/events")
    assert resp.status_code in (404, 405), "delete unexpectedly allowed"


def test_replay_mode_adjustable_speed():
    """Replay emits the recorded log identically; speed scales timing math."""
    store = _make_store(n=4)
    stream = EventStream.from_event_store(store)
    controller = ReplayController(stream.events, speed=float("inf"))
    assert [e.sim_time for e in controller.play()] == [0, 10, 20, 30]

    controller = ReplayController(stream.events, speed=2.0)
    delays = controller.planned_delays()
    # 10 sim-minutes at 2x speed -> 300 wall seconds per gap.
    assert delays == [300.0, 300.0, 300.0]
    assert controller.play() == stream.events


def test_live_tail_picks_up_appended_events():
    """The tail generator yields appended events in order without loss."""
    import threading

    store = _make_store(n=2)
    stream = EventStream.from_event_store(store)
    seen: List[Dict[str, Any]] = []

    def _consume() -> None:
        for event in stream.tail(poll_interval=0.001, max_events=4):
            seen.append(event.model_dump())

    consumer = threading.Thread(target=_consume, daemon=True)
    consumer.start()
    store.append(
        SimEvent(run_id="run-p46", sim_time=20, actor="lab", action="step_2", payload={})
    )
    store.append(
        SimEvent(run_id="run-p46", sim_time=30, actor="lab", action="step_3", payload={})
    )
    consumer.join(timeout=30)
    assert not consumer.is_alive(), "tail consumer stalled"
    assert [e["sim_time"] for e in seen] == [0, 10, 20, 30]


def test_events_after_helper():
    """Cursor helper slices strictly after the id; unknown ids raise."""
    store = _make_store(n=3)
    events = store.get_events()
    assert events_after(events, events[0].event_id) == events[1:]
    assert events_after(events, events[2].event_id) == []
    with pytest.raises(KeyError):
        events_after(events, "evt_missing")


def test_replay_from_recorded_bundle(tmp_path):
    """Replay sources include recorded encounter bundles (Phase 5 synergy)."""
    from vh.events.stream import EventStream as Stream

    bundle_path = tmp_path / "bundle.json"
    events = [
        {
            "event_id": f"evt_{i}",
            "run_id": "run_bundle",
            "sim_time": i * 5,
            "actor": "doctor",
            "action": "order_lab",
            "payload": {"i": i},
            "result_ref": None,
        }
        for i in range(3)
    ]
    bundle_path.write_text(
        json.dumps({"run_id": "run_bundle", "event_log": events}), encoding="utf-8"
    )
    stream = Stream.from_replay_bundle(str(bundle_path))
    assert [e.action for e in stream.events] == ["order_lab"] * 3
    assert [e.sim_time for e in stream.events] == [0, 5, 10]
