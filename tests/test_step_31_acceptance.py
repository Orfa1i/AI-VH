"""
Acceptance criteria tests for STEP 31 (P5.1):
Hospital Environment Simulator and Event Log.

Criteria:
1. Ground truth is unreachable through any action (fuzz test over the action space).
2. Turnaround times respected: results released only when sim clock reaches elapsed turnaround time.
3. Unavailable orders return result_unavailable without inventing data.
4. Every action produces exactly one event; events are never updated or deleted.
"""

import json
from pathlib import Path
import random
import string
import pytest

from vh.cases.spec import CaseSpec, DataIsolationError, VisiblePresentation, HiddenResult
from vh.cases.schema import GroundTruth
from vh.agents.environment import HospitalEnvironment, ActionResponse, OrderStatus
from vh.agents.events import EventStore, SimEvent

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_case_spec() -> CaseSpec:
    """Construct a known, strictly isolated CaseSpec for environment testing."""
    visible = VisiblePresentation(
        presentation="58-year-old male presenting with acute squeezing retrosternal chest pain.",
        demographics={"age": 58, "gender": "male"},
        history="Hypertension, hyperlipidemia, 25 pack-year smoking history.",
        current_medications=["Atorvastatin 40mg daily", "Amlodipine 5mg daily"],
        allergies=["Aspirin (bronchospasm)"],
        initial_vitals={"bp": "154/92", "hr": 88, "rr": 18, "spo2": 97, "temp": 37.0},
        exam="Anxious, diaphoretic, regular rhythm, clear breath sounds bilaterally.",
    )
    hidden = [
        HiddenResult(
            order_code="LAB-TROP",
            order_name="High-Sensitivity Troponin I",
            result="180 ng/L (elevated, ref < 14 ng/L)",
            turnaround_time_minutes=30,
            category="laboratory",
            loinc_code="49563-0",
        ),
        HiddenResult(
            order_code="DX-ECG",
            order_name="12-Lead Electrocardiogram",
            result="ST elevations in leads II, III, and aVF with reciprocal depression in I and aVL.",
            turnaround_time_minutes=10,
            category="imaging",
        ),
        HiddenResult(
            order_code="LAB-CBC",
            order_name="Complete Blood Count",
            result="WBC 8.2, Hgb 14.5, Plt 240",
            turnaround_time_minutes=20,
            category="laboratory",
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Acute Inferior STEMI",
        acceptable_differential=["NSTEMI", "Acute Pericarditis", "Aortic Dissection"],
        expected_workup=["12-Lead ECG", "High-Sensitivity Troponin", "Echocardiogram", "Emergent Angiography"],
        red_flags=["Hypotension", "Right ventricular infarction", "Complete heart block"],
    )
    return CaseSpec(
        case_id="CASE-SIM-001",
        specialty="Cardiology",
        patient_ref="PAT-SIM-001",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
        status="verified",
        version="1.0.0",
    )


def test_turnaround_times_respected(sample_case_spec):
    """
    Acceptance criterion 2: Turnaround times respected.
    Results are released to AgentView only once turnaround time has elapsed on the simulation clock.
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    assert env.sim_time_minutes == 0
    assert len(env.agent_view.released_results) == 0

    # Order ECG (turnaround time = 10 minutes)
    resp_ecg = env.order_imaging("DX-ECG", actor="doctor")
    assert resp_ecg.status == OrderStatus.PENDING
    assert resp_ecg.turnaround_time_minutes == 10
    assert not env.agent_view.has_released("DX-ECG")

    # Advance clock to 5 minutes: ECG should still be pending
    env.advance_clock(5)
    assert env.sim_time_minutes == 5
    assert not env.agent_view.has_released("DX-ECG")

    # Advance clock by another 5 minutes (sim_time = 10): ECG should now be released
    env.advance_clock(5)
    assert env.sim_time_minutes == 10
    assert env.agent_view.has_released("DX-ECG")
    ecg_result = env.agent_view.get_released_result("DX-ECG")
    assert "ST elevations in leads II, III, and aVF" in str(ecg_result)

    # Order Troponin at sim_time = 10 (turnaround time = 30 minutes, ready at sim_time = 40)
    resp_trop = env.order_lab("LAB-TROP", actor="doctor")
    assert resp_trop.status == OrderStatus.PENDING
    assert not env.agent_view.has_released("LAB-TROP")

    # Advance clock to 35 (sim_time = 35): elapsed from order = 25 minutes, still pending
    env.advance_clock(25)
    assert env.sim_time_minutes == 35
    assert not env.agent_view.has_released("LAB-TROP")

    # Advance clock to 40 (sim_time = 40): exactly 30 minutes elapsed, now released
    env.advance_clock(5)
    assert env.sim_time_minutes == 40
    assert env.agent_view.has_released("LAB-TROP")
    trop_result = env.agent_view.get_released_result("LAB-TROP")
    assert "180 ng/L" in str(trop_result)


def test_unavailable_orders_return_result_unavailable(sample_case_spec):
    """
    Acceptance criterion 3: Unavailable orders return result_unavailable.
    Never invent data.
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)

    # Order an unconfigured lab
    resp_lab = env.order_lab("LAB-AMYLASE-UNKNOWN", actor="doctor")
    assert resp_lab.status == OrderStatus.RESULT_UNAVAILABLE
    assert resp_lab.result is None
    assert "LAB-AMYLASE-UNKNOWN" in resp_lab.message
    assert not env.agent_view.has_released("LAB-AMYLASE-UNKNOWN")

    # Order an unconfigured imaging study
    resp_img = env.order_imaging("DX-MRI-BRAIN-UNKNOWN", actor="doctor")
    assert resp_img.status == OrderStatus.RESULT_UNAVAILABLE
    assert resp_img.result is None
    assert not env.agent_view.has_released("DX-MRI-BRAIN-UNKNOWN")

    # Advance clock by 120 minutes: unavailable orders must never materialize
    env.advance_clock(120)
    assert not env.agent_view.has_released("LAB-AMYLASE-UNKNOWN")
    assert not env.agent_view.has_released("DX-MRI-BRAIN-UNKNOWN")
    assert len(env.agent_view.released_results) == 0


def test_actions_produce_exactly_one_event_and_events_are_append_only(sample_case_spec, tmp_path):
    """
    Acceptance criterion 4: Every action produces exactly one event.
    Events are append-only and never updated or deleted.
    """
    persist_file = tmp_path / "sim_events.jsonl"
    store = EventStore(persist_path=persist_file)
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42, event_store=store)

    assert len(store.get_events()) == 0

    # 1. request_vitals
    vitals_resp = env.request_vitals(actor="nurse")
    assert vitals_resp["bp"] == "154/92"
    assert len(store.get_events()) == 1
    evt1 = store.get_events()[0]
    assert evt1.action == "request_vitals"
    assert evt1.actor == "nurse"
    assert evt1.sim_time == 0

    # 2. order_imaging
    env.order_imaging("DX-ECG", actor="doctor")
    assert len(store.get_events()) == 2
    evt2 = store.get_events()[1]
    assert evt2.action == "order_imaging"
    assert evt2.actor == "doctor"
    assert evt2.payload["order_code"] == "DX-ECG"

    # 3. advance_clock
    env.advance_clock(10, actor="system")
    assert len(store.get_events()) == 3
    evt3 = store.get_events()[2]
    assert evt3.action == "advance_clock"
    assert evt3.sim_time == 10
    assert evt3.payload["minutes_advanced"] == 10

    # 4. request_medication_info
    med_info = env.request_medication_info("Atorvastatin", actor="pharmacist")
    assert len(store.get_events()) == 4
    evt4 = store.get_events()[3]
    assert evt4.action == "request_medication_info"
    assert evt4.actor == "pharmacist"

    # 5. consult
    consult_resp = env.consult(role="cardiology", query="Recommend catheterization timing", actor="doctor")
    assert len(store.get_events()) == 5
    evt5 = store.get_events()[4]
    assert evt5.action == "consult"
    assert evt5.actor == "doctor"
    assert evt5.payload["role"] == "cardiology"

    # 6. submit_report
    report_data = {
        "primary_dx": "Acute Coronary Syndrome",
        "differential": ["STEMI", "NSTEMI"],
        "plan": "Emergent PCI",
    }
    submit_resp = env.submit_report(report=report_data, actor="doctor")
    assert submit_resp["status"] == "submitted"
    assert len(store.get_events()) == 6
    evt6 = store.get_events()[5]
    assert evt6.action == "submit_report"
    assert evt6.actor == "doctor"
    assert evt6.payload["report"] == report_data

    # Verify event schema
    for evt in store.get_events():
        assert evt.event_id.startswith("evt_")
        assert evt.run_id == env.run_id
        assert isinstance(evt.sim_time, int)
        assert isinstance(evt.wall_time, str)
        assert isinstance(evt.actor, str)
        assert isinstance(evt.action, str)
        assert isinstance(evt.payload, dict)

    # Verify immutability: attempting to mutate event attributes raises ValidationError
    with pytest.raises(Exception):
        evt1.action = "tampered_action"

    # Verify append-only: store has no delete or update methods
    assert not hasattr(store, "delete")
    assert not hasattr(store, "update")

    # Verify persistence file contains 6 JSON lines
    with open(persist_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 6


def test_ground_truth_unreachable_fuzz(sample_case_spec):
    """
    Acceptance criterion 1: Ground truth is unreachable through any action.
    Fuzz test over the entire action space with randomized and hostile inputs.
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=1337)

    forbidden_phrases = {
        "acute inferior stemi",
        "right ventricular infarction",
        "complete heart block",
        "emergent angiography",
        "ground_truth",
        "primary_dx",
        "acceptable_differential",
        "expected_workup",
        "red_flags",
    }

    # Helper function to check for leakage
    def assert_no_ground_truth_leakage(obj, path=""):
        if isinstance(obj, str):
            val_lower = obj.lower()
            for phrase in ["acute inferior stemi", "right ventricular infarction", "complete heart block"]:
                assert phrase not in val_lower, f"Ground truth leakage detected in {path}: '{phrase}' found!"
        elif isinstance(obj, dict):
            for k, v in obj.items():
                k_lower = str(k).lower()
                assert k_lower not in ["ground_truth", "primary_dx", "acceptable_differential", "expected_workup", "red_flags"], (
                    f"Forbidden key leaked in {path}.{k}"
                )
                assert_no_ground_truth_leakage(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                assert_no_ground_truth_leakage(item, f"{path}[{i}]")
        elif hasattr(obj, "__dict__"):
            assert_no_ground_truth_leakage(obj.__dict__, path)

    # 1. Check initial state: attempting to access ground truth raises DataIsolationError
    with pytest.raises(DataIsolationError):
        _ = env.agent_view.ground_truth
    with pytest.raises(DataIsolationError):
        _ = env.ground_truth
    assert_no_ground_truth_leakage(env.agent_view.model_dump())

    # 2. Fuzzing action space
    random.seed(1337)
    actions = [
        "request_vitals",
        "order_lab",
        "order_imaging",
        "request_medication_info",
        "consult",
        "submit_report",
        "advance_clock",
    ]

    hostile_payloads = [
        "ground_truth",
        "_ground_truth",
        "primary_dx",
        "acceptable_differential",
        "red_flags",
        "../../../etc/passwd",
        "<script>alert(1)</script>",
        "SELECT * FROM cases",
        "",
        "   ",
        "!@#$%^&*()",
        "A" * 1000,
    ]

    for trial in range(100):
        action = random.choice(actions)
        payload = random.choice(hostile_payloads)

        if action == "request_vitals":
            res = env.request_vitals(actor=random.choice(["doctor", "nurse", "unknown"]))
            assert_no_ground_truth_leakage(res, f"trial_{trial}_request_vitals")

        elif action == "order_lab":
            res = env.order_lab(code=payload, actor="doctor")
            assert_no_ground_truth_leakage(res.model_dump(), f"trial_{trial}_order_lab")

        elif action == "order_imaging":
            res = env.order_imaging(code=payload, actor="doctor")
            assert_no_ground_truth_leakage(res.model_dump(), f"trial_{trial}_order_imaging")

        elif action == "request_medication_info":
            res = env.request_medication_info(drug_name=payload, actor="pharmacist")
            assert_no_ground_truth_leakage(res, f"trial_{trial}_request_medication_info")

        elif action == "consult":
            res = env.consult(role=payload[:20], query=payload, actor="doctor")
            assert_no_ground_truth_leakage(res, f"trial_{trial}_consult")

        elif action == "submit_report":
            res = env.submit_report(report={"query": payload}, actor="doctor")
            assert_no_ground_truth_leakage(res, f"trial_{trial}_submit_report")

        elif action == "advance_clock":
            minutes = random.randint(0, 120)
            res = env.advance_clock(minutes=minutes, actor="system")
            assert isinstance(res, int)

        # Invariant check: agent_view must NEVER leak ground truth at any point in the simulation
        assert_no_ground_truth_leakage(env.agent_view.model_dump(), f"trial_{trial}_agent_view")

    # Invariant check: event store must NEVER leak ground truth in any recorded event
    for evt in env.event_store.get_events():
        assert_no_ground_truth_leakage(evt.model_dump(), f"event_{evt.event_id}")


def test_event_store_reload_from_disk(sample_case_spec, tmp_path):
    """Verify EventStore loads previous events when initialized with an existing log file."""
    persist_file = tmp_path / "persisted_events.jsonl"
    store1 = EventStore(persist_path=persist_file)
    env1 = HospitalEnvironment(case_spec=sample_case_spec, seed=42, event_store=store1)

    env1.request_vitals(actor="nurse")
    env1.order_lab("LAB-CBC", actor="doctor")
    assert len(store1) == 2

    # Initialize a new store pointing to the same file
    store2 = EventStore(persist_path=persist_file)
    assert len(store2) == 2
    assert store2[0].action == "request_vitals"
    assert store2[1].action == "order_lab"
    assert store2[0].event_id == store1[0].event_id

    # Append new event to store2
    evt_new = SimEvent(
        run_id=env1.run_id,
        sim_time=15,
        actor="system",
        action="advance_clock",
        payload={"minutes_advanced": 15},
    )
    store2.append(evt_new)
    assert len(store2) == 3


def test_advance_clock_validation_and_multi_orders(sample_case_spec):
    """Verify negative clock advance raises ValueError, and multi-order staging functions accurately."""
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)

    # Reject negative advance
    with pytest.raises(ValueError, match="Cannot advance simulation clock by negative minutes"):
        env.advance_clock(-10)

    # Order ECG (tat=10), CBC (tat=20), Trop (tat=30)
    resp_ecg = env.order_imaging("DX-ECG", actor="doctor")
    resp_cbc = env.order_lab("LAB-CBC", actor="doctor")
    resp_trop = env.order_lab("LAB-TROP", actor="doctor")

    assert resp_ecg.status == OrderStatus.PENDING
    assert resp_cbc.status == OrderStatus.PENDING
    assert resp_trop.status == OrderStatus.PENDING

    # Advance 15 min (sim_time = 15): ECG should be released, CBC and Trop still pending
    env.advance_clock(15)
    assert env.agent_view.has_released("DX-ECG")
    assert not env.agent_view.has_released("LAB-CBC")
    assert not env.agent_view.has_released("LAB-TROP")

    # Advance 10 min (sim_time = 25): CBC should be released (ordered at 0, ready at 20)
    env.advance_clock(10)
    assert env.agent_view.has_released("LAB-CBC")
    assert not env.agent_view.has_released("LAB-TROP")

    # Advance 10 min (sim_time = 35): Trop should be released (ordered at 0, ready at 30)
    env.advance_clock(10)
    assert env.agent_view.has_released("LAB-TROP")
    assert len(env.agent_view.released_results) == 3


def test_order_by_name_and_duplicate_orders(sample_case_spec):
    """Verify orders can be placed by name, and duplicate orders return appropriate statuses."""
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)

    # Order by display name
    resp = env.order_lab("High-Sensitivity Troponin I", actor="doctor")
    assert resp.status == OrderStatus.PENDING
    assert resp.order_code == "LAB-TROP"

    # Duplicate while pending returns already_pending status
    resp_dup = env.order_lab("LAB-TROP", actor="doctor")
    assert resp_dup.status == OrderStatus.PENDING
    assert "currently in progress" in resp_dup.message

    # Advance clock to release
    env.advance_clock(35)
    assert env.agent_view.has_released("LAB-TROP")

    # Duplicate after released returns already_released status
    resp_released = env.order_lab("LAB-TROP", actor="doctor")
    assert resp_released.status == OrderStatus.RELEASED
    assert "already been released" in resp_released.message
