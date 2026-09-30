"""
Acceptance criteria tests for STEP 33 (P5.3):
Orchestrator, Budgets, and Loop Detection.

Criteria:
1. Tests for every termination path: completed, budget_exceeded (step, token, cost, sim_time), loop_detected (repeated action, stagnation), error.
2. Each budget is strictly enforced.
3. A loop scenario triggers loop_detected.
4. An agent failure ends the encounter with status error, never silent success.
5. An end-to-end run of 10 golden cases completes.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from vh.cases.schema import GoldenCase
from vh.cases.spec import CaseSpec, HiddenResult, VisiblePresentation
from vh.cases.schema import GroundTruth
from vh.agents.orchestrator import (
    EncounterBudget,
    EncounterState,
    EncounterStatus,
    HospitalOrchestrator,
    LoopDetectionConfig,
)
from vh.agents.roles.doctor import DoctorAgent

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_V1_DIR = REPO_ROOT / "eval" / "golden" / "v1"


@pytest.fixture
def sample_case_spec() -> CaseSpec:
    """Construct a standardized clinical case for orchestrator testing."""
    visible = VisiblePresentation(
        presentation="52-year-old female presenting with acute pleuritic chest pain and dyspnea.",
        demographics={"age": 52, "gender": "female"},
        history="Recent long-haul flight 3 days ago, mild obesity.",
        current_medications=["Oral contraceptive pill"],
        allergies=["Penicillin"],
        initial_vitals={"bp": "128/82", "hr": 110, "rr": 24, "spo2": 93, "temp": 37.3},
        exam="Tachycardic, clear lungs, right calf mild swelling and tenderness.",
    )
    hidden = [
        HiddenResult(
            order_code="LAB-DDIMER",
            order_name="D-Dimer Quantitative",
            result="2400 ng/mL (elevated, ref < 500 ng/mL)",
            turnaround_time_minutes=20,
            category="laboratory",
        ),
        HiddenResult(
            order_code="DX-CTPA",
            order_name="CT Pulmonary Angiogram",
            result="Segmental pulmonary embolism in right lower lobe.",
            turnaround_time_minutes=45,
            category="imaging",
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Acute Pulmonary Embolism",
        acceptable_differential=["Pneumonia", "Pleurisy", "Pericarditis"],
        expected_workup=["D-Dimer", "CT Pulmonary Angiogram", "Electrocardiogram", "Lower Extremity Ultrasound"],
        red_flags=["Right ventricular strain", "Hypotension", "Hypoxia"],
    )
    return CaseSpec(
        case_id="CASE-ORCH-001",
        specialty="Emergency Medicine",
        patient_ref="PAT-ORCH-001",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
        status="verified",
        version="1.0.0",
    )


def test_terminal_state_completed(sample_case_spec):
    """
    Acceptance criterion 1: Encounter runs to successful completion.
    Nurse vitals -> Doctor orders -> clock advance -> findings -> report submission -> status COMPLETED.
    """
    orchestrator = HospitalOrchestrator(
        budget=EncounterBudget(max_steps=20, max_tokens=10000, max_cost=1.0, max_sim_time_minutes=300),
    )
    state = orchestrator.run_encounter(case_spec=sample_case_spec)

    assert state.status == EncounterStatus.COMPLETED
    assert state.termination_reason == "report_submitted_and_verified"
    assert state.report is not None
    assert state.step_count > 0
    assert state.sim_time_minutes > 0
    assert len(state.history) > 0


def test_budget_enforcement_max_steps(sample_case_spec):
    """
    Acceptance criterion 2: Step budget is strictly enforced.
    Terminates with status BUDGET_EXCEEDED when step limit is hit.
    """
    budget = EncounterBudget(max_steps=2, max_tokens=10000, max_cost=1.0, max_sim_time_minutes=300)
    orchestrator = HospitalOrchestrator(budget=budget)
    state = orchestrator.run_encounter(case_spec=sample_case_spec)

    assert state.status == EncounterStatus.BUDGET_EXCEEDED
    assert "max_steps" in state.termination_reason.lower()
    assert state.step_count == 2


def test_budget_enforcement_max_tokens(sample_case_spec):
    """
    Acceptance criterion 2: Token budget is strictly enforced.
    Terminates with status BUDGET_EXCEEDED when token usage exceeds limit.
    """
    budget = EncounterBudget(max_steps=20, max_tokens=100, max_cost=1.0, max_sim_time_minutes=300)
    orchestrator = HospitalOrchestrator(budget=budget)

    # Force simulated token usage on each step
    state = orchestrator.run_encounter(case_spec=sample_case_spec, step_token_cost=60)

    assert state.status == EncounterStatus.BUDGET_EXCEEDED
    assert "token" in state.termination_reason.lower()
    assert state.token_count >= 100


def test_budget_enforcement_max_cost(sample_case_spec):
    """
    Acceptance criterion 2: Cost budget is strictly enforced.
    Terminates with status BUDGET_EXCEEDED when monetary cost exceeds limit.
    """
    budget = EncounterBudget(max_steps=20, max_tokens=10000, max_cost=0.04, max_sim_time_minutes=300)
    orchestrator = HospitalOrchestrator(budget=budget)

    state = orchestrator.run_encounter(case_spec=sample_case_spec, step_monetary_cost=0.025)

    assert state.status == EncounterStatus.BUDGET_EXCEEDED
    assert "cost" in state.termination_reason.lower()
    assert state.cost >= 0.04


def test_budget_enforcement_max_sim_time(sample_case_spec):
    """
    Acceptance criterion 2: Simulation clock budget is strictly enforced.
    Terminates with status BUDGET_EXCEEDED when clock exceeds max simulation time.
    """
    budget = EncounterBudget(max_steps=20, max_tokens=10000, max_cost=1.0, max_sim_time_minutes=30)
    orchestrator = HospitalOrchestrator(budget=budget)

    # Case has lab with turnaround 20 and CTPA with turnaround 45. Advancing to complete CTPA exceeds 30 min.
    state = orchestrator.run_encounter(case_spec=sample_case_spec)

    assert state.status == EncounterStatus.BUDGET_EXCEEDED
    assert "sim_time" in state.termination_reason.lower()
    assert state.sim_time_minutes >= 30


def test_loop_detection_repeated_actions(sample_case_spec):
    """
    Acceptance criterion 3: Repeated identical actions trigger LOOP_DETECTED.
    The same action with the same arguments repeated K times ends the encounter.
    """
    loop_cfg = LoopDetectionConfig(max_repeated_actions=3, max_stagnant_steps=10)
    orchestrator = HospitalOrchestrator(loop_config=loop_cfg)

    # Custom step handler that deterministically repeats the same action
    def repetitive_driver(env, agents, encounter_state):
        doctor = agents["doctor"]
        return doctor.order_lab("LAB-DDIMER")

    state = orchestrator.run_custom_loop(
        case_spec=sample_case_spec,
        driver_fn=repetitive_driver,
    )

    assert state.status == EncounterStatus.LOOP_DETECTED
    assert "repeated_action" in state.termination_reason
    assert "LAB-DDIMER" in state.termination_reason


def test_loop_detection_stagnation(sample_case_spec):
    """
    Acceptance criterion 3: Stagnation without progress triggers LOOP_DETECTED.
    M steps without new findings or notes ends the encounter with loop_detected.
    """
    loop_cfg = LoopDetectionConfig(max_repeated_actions=10, max_stagnant_steps=4)
    orchestrator = HospitalOrchestrator(loop_config=loop_cfg)

    # Driver that executes varying dummy actions that yield no new clinical findings or state progress
    counter = {"i": 0}

    def stagnant_driver(env, agents, encounter_state):
        counter["i"] += 1
        doctor = agents["doctor"]
        return doctor.order_lab(f"LAB-UNKNOWN-{counter['i']}")

    state = orchestrator.run_custom_loop(
        case_spec=sample_case_spec,
        driver_fn=stagnant_driver,
    )

    assert state.status == EncounterStatus.LOOP_DETECTED
    assert "stagnation" in state.termination_reason


def test_agent_failure_routes_to_error_state(sample_case_spec):
    """
    Acceptance criterion 4: Agent failure ends encounter with status ERROR.
    Never silent success.
    """
    orchestrator = HospitalOrchestrator()

    def faulty_driver(env, agents, encounter_state):
        raise ValueError("Diagnostic device hardware failure / model inference timeout")

    state = orchestrator.run_custom_loop(
        case_spec=sample_case_spec,
        driver_fn=faulty_driver,
    )

    assert state.status == EncounterStatus.ERROR
    assert "Diagnostic device hardware failure" in state.termination_reason


def test_end_to_end_10_golden_cases():
    """
    Acceptance criterion 5: An end-to-end run of 10 golden cases completes.
    Every encounter terminates in a valid terminal state with full event history.
    """
    golden_files = sorted(GOLDEN_V1_DIR.glob("*.json"))
    golden_cases = [
        GoldenCase.model_validate(json.loads(f.read_text(encoding="utf-8")))
        for f in golden_files
        if f.name != "manifest.json"
    ][:10]

    assert len(golden_cases) == 10, f"Expected 10 golden cases, found {len(golden_cases)}"

    orchestrator = HospitalOrchestrator(
        budget=EncounterBudget(max_steps=25, max_tokens=10000, max_cost=1.0, max_sim_time_minutes=360),
    )

    completed_count = 0
    for idx, golden in enumerate(golden_cases):
        case_spec = CaseSpec.from_golden_case(golden)
        state = orchestrator.run_encounter(case_spec=case_spec)

        # Invariant: must end in an explicit terminal state
        assert state.status in {
            EncounterStatus.COMPLETED,
            EncounterStatus.BUDGET_EXCEEDED,
            EncounterStatus.LOOP_DETECTED,
            EncounterStatus.ERROR,
        }
        assert state.termination_reason is not None
        assert state.step_count > 0
        assert len(state.history) > 0

        if state.status == EncounterStatus.COMPLETED:
            completed_count += 1
            assert state.report is not None

    # Across the 10 golden cases, at least 90% must complete successfully end-to-end
    assert completed_count >= 9, f"Expected >= 9 of 10 golden cases to complete, got {completed_count}"
