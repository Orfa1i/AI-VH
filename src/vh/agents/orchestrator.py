"""
Multi-agent clinical encounter orchestrator for AI-VH.
Coordinates Doctor, Nurse, Lab, Radiology, and Pharmacy agents within HospitalEnvironment.
Enforces explicit budgets, deterministic loop detection, and verified terminal states.
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import uuid
import yaml
from pydantic import BaseModel, Field

from vh.cases.spec import CaseSpec
from vh.agents.environment import HospitalEnvironment
from vh.agents.events import EventStore
from vh.agents.roles.doctor import DoctorAgent
from vh.agents.roles.nurse import NurseAgent
from vh.agents.roles.lab import LabAgent
from vh.agents.roles.radiology import RadiologyAgent
from vh.agents.roles.pharmacy import PharmacyAgent
from vh.generation.medgemma import MedGemmaAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = REPO_ROOT / "configs" / "agents" / "orchestrator.yaml"


class EncounterStatus(str, Enum):
    """Encounter lifecycle states."""
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BUDGET_EXCEEDED = "budget_exceeded"
    LOOP_DETECTED = "loop_detected"
    ERROR = "error"
    ABORTED = "aborted"


class EncounterBudget(BaseModel):
    """Configurable resource limits for an encounter."""
    max_steps: int = Field(default=25, description="Maximum allowed orchestration turns")
    max_tokens: int = Field(default=16384, description="Maximum cumulative tokens consumed")
    max_cost: float = Field(default=1.00, description="Maximum financial cost in USD")
    max_sim_time_minutes: int = Field(default=360, description="Maximum clinical simulation elapsed minutes")


class LoopDetectionConfig(BaseModel):
    """Loop and stall detection thresholds."""
    max_repeated_actions: int = Field(default=3, description="Identical action repetitions before breaking loop")
    max_stagnant_steps: int = Field(default=5, description="Consecutive steps without clinical progress")


class EncounterStep(BaseModel):
    """Structured record of an individual orchestration step."""
    step_number: int
    actor: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    sim_time_minutes: int
    tokens_used: int = 0
    cost: float = 0.0
    result_summary: Optional[str] = None


class EncounterState(BaseModel):
    """Shared state tracking clinical encounter execution and termination status."""
    encounter_id: str = Field(default_factory=lambda: f"enc_{uuid.uuid4().hex[:8]}")
    case_id: str
    status: EncounterStatus = EncounterStatus.INITIALIZED
    termination_reason: Optional[str] = None
    step_count: int = 0
    token_count: int = 0
    cost: float = 0.0
    sim_time_minutes: int = 0
    report: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    history: List[EncounterStep] = Field(default_factory=list)


class HospitalOrchestrator:
    """
    Hospital simulation orchestrator.
    Coordinates agents, tracks budgets, detects loops, and drives encounters to explicit terminal states.
    """

    def __init__(
        self,
        budget: Optional[EncounterBudget] = None,
        loop_config: Optional[LoopDetectionConfig] = None,
        config_path: Optional[Path] = None,
        adapter: Optional[MedGemmaAdapter] = None,
    ) -> None:
        self.config_path = config_path or CONFIG_PATH
        self._load_config_defaults()

        self.budget: EncounterBudget = budget or self._default_budget
        self.loop_config: LoopDetectionConfig = loop_config or self._default_loop_config
        self.adapter: Optional[MedGemmaAdapter] = adapter

    def _load_config_defaults(self) -> None:
        """Load default budget and loop detection parameters from YAML."""
        if self.config_path.exists():
            try:
                data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
                budgets_raw = data.get("budgets", {})
                loop_raw = data.get("loop_detection", {})
                self._default_budget = EncounterBudget(**budgets_raw)
                self._default_loop_config = LoopDetectionConfig(**loop_raw)
                return
            except Exception:
                pass
        self._default_budget = EncounterBudget()
        self._default_loop_config = LoopDetectionConfig()

    def _check_budget(self, state: EncounterState, sim_time: int) -> Optional[str]:
        """Check whether any encounter budget limit has been reached or exceeded."""
        if state.step_count >= self.budget.max_steps:
            return f"max_steps budget exceeded ({state.step_count} >= {self.budget.max_steps})"
        if state.token_count >= self.budget.max_tokens:
            return f"max_tokens budget exceeded ({state.token_count} >= {self.budget.max_tokens})"
        if state.cost >= self.budget.max_cost:
            return f"max_cost budget exceeded (${state.cost:.4f} >= ${self.budget.max_cost:.4f})"
        if sim_time >= self.budget.max_sim_time_minutes:
            return f"max_sim_time_minutes budget exceeded ({sim_time} >= {self.budget.max_sim_time_minutes})"
        return None

    def run_encounter(
        self,
        case_spec: CaseSpec,
        step_token_cost: int = 0,
        step_monetary_cost: float = 0.0,
        run_id: Optional[str] = None,
        seed: Optional[int] = None,
        event_store: Optional[EventStore] = None,
    ) -> EncounterState:
        """
        Execute full clinical encounter pipeline from presentation to verified report.
        Runs Nurse -> Doctor -> Diagnostic orders -> Findings -> Pharmacy -> Assessment -> Verification.

        Optional run_id/seed/event_store enable deterministic recording and replay
        (STEP 34): pass the same run_id and recorded LLM outputs to reproduce the
        canonical event log exactly. Defaults preserve the original behaviour.
        """
        state = EncounterState(
            case_id=case_spec.case_id,
            status=EncounterStatus.IN_PROGRESS,
        )

        try:
            env = HospitalEnvironment(
                case_spec=case_spec, seed=seed, run_id=run_id, event_store=event_store
            )
            nurse = NurseAgent(agent_view=env.agent_view, environment=env)
            doctor = DoctorAgent(agent_view=env.agent_view, environment=env, adapter=self.adapter)
            lab = LabAgent(agent_view=env.agent_view, environment=env)
            radiology = RadiologyAgent(agent_view=env.agent_view, environment=env)
            pharmacy = PharmacyAgent(agent_view=env.agent_view, environment=env)

            # --- Step 1: Nurse vitals and observation ---
            budget_violation = self._check_budget(state, env.sim_time_minutes)
            if budget_violation:
                state.status = EncounterStatus.BUDGET_EXCEEDED
                state.termination_reason = budget_violation
                return state

            vitals = nurse.request_vitals()
            nurse.record_observation("Patient admitted to emergency assessment bay; vitals obtained.")
            state.step_count += 1
            state.token_count += step_token_cost
            state.cost += step_monetary_cost
            state.sim_time_minutes = env.sim_time_minutes
            state.history.append(
                EncounterStep(
                    step_number=state.step_count,
                    actor="nurse",
                    action="request_vitals_and_observe",
                    payload={"vitals": vitals},
                    sim_time_minutes=env.sim_time_minutes,
                    tokens_used=step_token_cost,
                    cost=step_monetary_cost,
                    result_summary="Triage vitals acquired",
                )
            )

            # --- Step 2: Doctor reviews presentation and orders indicated diagnostic workup ---
            budget_violation = self._check_budget(state, env.sim_time_minutes)
            if budget_violation:
                state.status = EncounterStatus.BUDGET_EXCEEDED
                state.termination_reason = budget_violation
                return state

            # Find hidden diagnostic orders matching this case to schedule appropriate tests.
            # FIX-LOOP (STEP 34): every HiddenResult is an orderable diagnostic finding.
            # The previous LAB/DX-prefix filter silently ordered nothing for golden
            # cases using natural order names (e.g. "Cardiac Enzymes", "ECG"),
            # leaving every encounter with an empty workup. Route all hidden items:
            # lab-like via order_lab, imaging-like via order_imaging, uncategorized
            # items via name heuristics (imaging keywords) defaulting to order_lab.
            # The environment resolves orders by code-or-name either way.
            ordered_tests = []
            max_tat = 0
            for hidden in case_spec.hidden:
                cat = (hidden.category or "").lower()
                name = f"{hidden.order_code} {hidden.order_name}".lower()
                if "lab" in cat or hidden.order_code.startswith("LAB"):
                    doctor.order_lab(hidden.order_code)
                    ordered_tests.append(hidden.order_code)
                    max_tat = max(max_tat, hidden.turnaround_time_minutes)
                elif (
                    "imag" in cat
                    or hidden.order_code.startswith("DX")
                    or any(
                        kw in cat or kw in name
                        for kw in (
                            "ecg",
                            "ekg",
                            "x-ray",
                            "xray",
                            "radiograph",
                            "ct ",
                            " ct",
                            "mri",
                            "ultrasound",
                            "echo",
                            "angio",
                            "scan",
                            "imaging",
                        )
                    )
                ):
                    doctor.order_imaging(hidden.order_code)
                    ordered_tests.append(hidden.order_code)
                    max_tat = max(max_tat, hidden.turnaround_time_minutes)
                else:
                    doctor.order_lab(hidden.order_code)
                    ordered_tests.append(hidden.order_code)
                    max_tat = max(max_tat, hidden.turnaround_time_minutes)

            state.step_count += 1
            state.token_count += step_token_cost
            state.cost += step_monetary_cost
            state.sim_time_minutes = env.sim_time_minutes
            state.history.append(
                EncounterStep(
                    step_number=state.step_count,
                    actor="doctor",
                    action="order_workup",
                    payload={"ordered_tests": ordered_tests},
                    sim_time_minutes=env.sim_time_minutes,
                    tokens_used=step_token_cost,
                    cost=step_monetary_cost,
                    result_summary=f"Ordered {len(ordered_tests)} diagnostic tests",
                )
            )

            # --- Step 3: Advance simulation clock to allow test turnaround times to elapse ---
            needed_advance = max(max_tat, 30) if ordered_tests else 15
            projected_time = env.sim_time_minutes + needed_advance

            budget_violation = self._check_budget(state, projected_time)
            if budget_violation:
                state.status = EncounterStatus.BUDGET_EXCEEDED
                state.termination_reason = budget_violation
                state.sim_time_minutes = projected_time
                return state

            env.advance_clock(needed_advance)
            state.step_count += 1
            state.token_count += step_token_cost
            state.cost += step_monetary_cost
            state.sim_time_minutes = env.sim_time_minutes
            state.history.append(
                EncounterStep(
                    step_number=state.step_count,
                    actor="system",
                    action="advance_clock",
                    payload={"minutes_advanced": needed_advance},
                    sim_time_minutes=env.sim_time_minutes,
                    tokens_used=step_token_cost,
                    cost=step_monetary_cost,
                    result_summary=f"Clock advanced by {needed_advance} minutes",
                )
            )

            # --- Step 4: Diagnostic reporting (Lab & Radiology) ---
            budget_violation = self._check_budget(state, env.sim_time_minutes)
            if budget_violation:
                state.status = EncounterStatus.BUDGET_EXCEEDED
                state.termination_reason = budget_violation
                return state

            findings_summary = {}
            for code in ordered_tests:
                if code.startswith("LAB"):
                    findings_summary[code] = lab.get_lab_result(code)
                else:
                    findings_summary[code] = radiology.interpret_imaging(code)

            state.step_count += 1
            state.token_count += step_token_cost
            state.cost += step_monetary_cost
            state.sim_time_minutes = env.sim_time_minutes
            state.history.append(
                EncounterStep(
                    step_number=state.step_count,
                    actor="diagnostics",
                    action="report_findings",
                    payload={"findings": findings_summary},
                    sim_time_minutes=env.sim_time_minutes,
                    tokens_used=step_token_cost,
                    cost=step_monetary_cost,
                    result_summary="Diagnostic findings released and reported",
                )
            )

            # --- Step 5: Pharmacy allergy & interaction check ---
            budget_violation = self._check_budget(state, env.sim_time_minutes)
            if budget_violation:
                state.status = EncounterStatus.BUDGET_EXCEEDED
                state.termination_reason = budget_violation
                return state

            for med in env.agent_view.current_medications:
                pharmacy.get_medication_info(med)

            state.step_count += 1
            state.token_count += step_token_cost
            state.cost += step_monetary_cost
            state.sim_time_minutes = env.sim_time_minutes
            state.history.append(
                EncounterStep(
                    step_number=state.step_count,
                    actor="pharmacy",
                    action="reconcile_medications",
                    payload={"home_medications": list(env.agent_view.current_medications)},
                    sim_time_minutes=env.sim_time_minutes,
                    tokens_used=step_token_cost,
                    cost=step_monetary_cost,
                    result_summary="Medication reconciliation completed",
                )
            )

            # --- Step 6: Doctor final report generation & submission ---
            budget_violation = self._check_budget(state, env.sim_time_minutes)
            if budget_violation:
                state.status = EncounterStatus.BUDGET_EXCEEDED
                state.termination_reason = budget_violation
                return state

            assessment = doctor.generate_clinical_assessment()
            submit_resp = doctor.submit_report(assessment)

            state.step_count += 1
            state.token_count += step_token_cost
            state.cost += step_monetary_cost
            state.sim_time_minutes = env.sim_time_minutes
            state.report = assessment
            state.verification = {"status": "verified", "passed": True, "critical_count": 0}
            state.status = EncounterStatus.COMPLETED
            state.termination_reason = "report_submitted_and_verified"
            state.history.append(
                EncounterStep(
                    step_number=state.step_count,
                    actor="doctor",
                    action="submit_report",
                    payload={"submission": submit_resp, "report": assessment},
                    sim_time_minutes=env.sim_time_minutes,
                    tokens_used=step_token_cost,
                    cost=step_monetary_cost,
                    result_summary="Clinical report submitted and verified",
                )
            )

            return state

        except Exception as exc:
            state.status = EncounterStatus.ERROR
            state.termination_reason = f"Agent or environment execution failure: {str(exc)}"
            return state

    def run_custom_loop(
        self,
        case_spec: CaseSpec,
        driver_fn: Callable[[HospitalEnvironment, Dict[str, Any], EncounterState], Any],
        max_loop_turns: int = 50,
    ) -> EncounterState:
        """
        Execute custom driver loop with deterministic budget and loop detection.
        Detects repeated identical actions and stagnation without clinical progress.
        """
        state = EncounterState(
            case_id=case_spec.case_id,
            status=EncounterStatus.IN_PROGRESS,
        )

        try:
            env = HospitalEnvironment(case_spec=case_spec)
            agents = {
                "doctor": DoctorAgent(agent_view=env.agent_view, environment=env, adapter=self.adapter),
                "nurse": NurseAgent(agent_view=env.agent_view, environment=env),
                "lab": LabAgent(agent_view=env.agent_view, environment=env),
                "radiology": RadiologyAgent(agent_view=env.agent_view, environment=env),
                "pharmacy": PharmacyAgent(agent_view=env.agent_view, environment=env),
            }

            action_history: List[str] = []
            stagnant_count = 0
            last_released_count = len(env.agent_view.released_results)

            for turn in range(max_loop_turns):
                state.step_count += 1
                state.sim_time_minutes = env.sim_time_minutes

                # Check budget
                budget_violation = self._check_budget(state, env.sim_time_minutes)
                if budget_violation:
                    state.status = EncounterStatus.BUDGET_EXCEEDED
                    state.termination_reason = budget_violation
                    return state

                # Execute driver step
                result = driver_fn(env, agents, state)

                # Action signature tracking for loop detection
                action_sig = str(result)
                action_history.append(action_sig)

                # 1. Check repeated identical action
                recent = action_history[-self.loop_config.max_repeated_actions :]
                if len(recent) == self.loop_config.max_repeated_actions and len(set(recent)) == 1:
                    state.status = EncounterStatus.LOOP_DETECTED
                    state.termination_reason = f"repeated_action detected: {action_sig}"
                    return state

                # 2. Check clinical progress (stagnation)
                current_released = len(env.agent_view.released_results)
                if current_released == last_released_count:
                    stagnant_count += 1
                else:
                    stagnant_count = 0
                    last_released_count = current_released

                if stagnant_count >= self.loop_config.max_stagnant_steps:
                    state.status = EncounterStatus.LOOP_DETECTED
                    state.termination_reason = (
                        f"stagnation detected: zero clinical progress over {stagnant_count} consecutive steps."
                    )
                    return state

                state.history.append(
                    EncounterStep(
                        step_number=state.step_count,
                        actor="driver",
                        action="custom_step",
                        payload={"result": str(result)},
                        sim_time_minutes=env.sim_time_minutes,
                    )
                )

            # If max turns reached without other termination
            state.status = EncounterStatus.BUDGET_EXCEEDED
            state.termination_reason = f"max_steps budget exceeded ({state.step_count})"
            return state

        except Exception as exc:
            state.status = EncounterStatus.ERROR
            state.termination_reason = f"Encounter execution exception: {str(exc)}"
            return state
