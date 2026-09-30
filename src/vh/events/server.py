"""
Runnable encounter event-stream server for AI-VH (STEP 47 / P8.2).

Serves the STEP-46 read-only event API over HTTP for the department board.
Demo seeding (`EVENT_DEMO_SEED=1`) writes a fixed two-run encounter log when
the log file is empty: dev/test use only, never clinical data.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vh.agents.events import EventStore, SimEvent
from vh.events.stream import create_event_app

LOG_PATH = os.environ.get("EVENT_LOG_PATH", "data/events-demo.jsonl")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "EVENT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

DEMO_RUNS = [
    {
        "run_id": "DEMO-RUN-1",
        "case_id": "CASE-E2E-BOARD-1",
        "steps": [
            ("nurse", "request_vitals", 0, {"vitals": {"hr": 110}}),
            ("doctor", "order_lab", 5, {"order_code": "LAB-DEMO"}),
            ("system", "advance_clock", 30, {"minutes_advanced": 25}),
            ("diagnostics", "report_findings", 30, {"findings": {"LAB-DEMO": "High"}}),
            (
                "doctor",
                "submit_report",
                45,
                {"report": {"patient_summary": "E2E board summary."}},
            ),
        ],
        "result_ref": "rep_demo1",
    },
    {
        "run_id": "DEMO-RUN-2",
        "case_id": "CASE-E2E-BOARD-2",
        "steps": [
            ("nurse", "request_vitals", 0, {"vitals": {"hr": 88}}),
            ("doctor", "order_lab", 5, {"order_code": "LAB-DEMO"}),
        ],
        "result_ref": None,
    },
]


def seed_demo(log_path: str = LOG_PATH) -> int:
    """Write the fixed demo encounter log. Returns the event count."""
    store = EventStore(persist_path=log_path)
    if len(store) > 0:
        return len(store)
    for run in DEMO_RUNS:
        for actor, action, sim_time, extra in run["steps"]:
            payload = {"case_id": run["case_id"], **extra}
            store.append(
                SimEvent(
                    run_id=run["run_id"],
                    sim_time=sim_time,
                    actor=actor,
                    action=action,
                    payload=payload,
                    result_ref=run["result_ref"] if action == "submit_report" else None,
                )
            )
    return len(store)


if os.environ.get("EVENT_DEMO_SEED") == "1":
    seed_demo(LOG_PATH)

app: FastAPI = create_event_app(store=EventStore(persist_path=LOG_PATH))
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)

if __name__ == "__main__":
    import uvicorn

    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    uvicorn.run("vh.events.server:app", host="127.0.0.1", port=8101)
