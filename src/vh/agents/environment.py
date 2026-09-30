"""
Headless hospital environment simulator for AI-VH.
Controls simulation clock, turnaround times, and strictly isolated AgentView release.
Ensures zero data leakage, append-only event recording, and faithful clinical order handling.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field

from vh.cases.spec import AgentView, CaseSpec, DataIsolationError, HiddenResult, ReleasedResult
from vh.agents.events import EventStore, SimEvent


class OrderStatus(str, Enum):
    """Execution status for diagnostic orders within the environment."""
    PENDING = "pending"
    RELEASED = "released"
    RESULT_UNAVAILABLE = "result_unavailable"


class ActionResponse(BaseModel):
    """
    Standardized typed response returned to clinical agents following an order action.
    """
    status: OrderStatus = Field(description="Order lifecycle status")
    order_code: Optional[str] = Field(default=None, description="Diagnostic order code")
    order_name: Optional[str] = Field(default=None, description="Diagnostic order name")
    turnaround_time_minutes: int = Field(default=0, description="Clinical turnaround time in minutes")
    result: Optional[Any] = Field(default=None, description="Diagnostic result payload if released")
    message: str = Field(default="", description="System message or status description")
    category: Optional[str] = Field(default=None, description="Diagnostic modality category")

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class PendingOrder(BaseModel):
    """
    Internal tracking structure for diagnostic tests in progress.
    """
    order_code: str
    order_name: str
    category: Optional[str] = None
    ordered_at_sim_time: int
    ready_at_sim_time: int
    actor: str


_FORBIDDEN_ENV_ATTRIBUTES = {
    "ground_truth",
    "_ground_truth",
    "primary_dx",
    "acceptable_differential",
    "expected_workup",
    "red_flags",
}


class HospitalEnvironment:
    """
    Hospital Environment Simulator for AI-VH multi-agent workflows.
    
    Owns:
    1. AgentView: Sanitized, strictly isolated patient view.
    2. Hidden results: CaseSpec diagnostic findings released only upon elapsed turnaround time.
    3. Simulation clock: Sim time in minutes tracking clinical elapsed duration.
    4. Event store: Append-only ledger recording all environment and agent actions.
    
    Architectural Guarantees:
    - Ground truth is strictly inaccessible through any action or environment inspection.
    - Turnaround times are enforced against the simulation clock.
    - Unavailable orders return result_unavailable without hallucinating data.
    - Every action produces exactly one append-only event in the event store.
    """

    def __init__(
        self,
        case_spec: CaseSpec,
        seed: Optional[int] = None,
        run_id: Optional[str] = None,
        event_store: Optional[EventStore] = None,
    ) -> None:
        self._case_spec = case_spec
        self._seed = seed if seed is not None else 42
        self._run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        self._sim_time_minutes: int = 0
        self._agent_view: AgentView = case_spec.to_agent_view()
        self._event_store: EventStore = event_store if event_store is not None else EventStore()
        self._pending_orders: Dict[str, PendingOrder] = {}

    def __getattr__(self, name: str) -> Any:
        name_lower = name.lower()
        if name in _FORBIDDEN_ENV_ATTRIBUTES or name_lower in _FORBIDDEN_ENV_ATTRIBUTES:
            raise DataIsolationError(
                f"Data Isolation Breach: '{name}' is strictly isolated and inaccessible from HospitalEnvironment."
            )
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def agent_view(self) -> AgentView:
        """Return the current immutable, sanitized AgentView."""
        return self._agent_view

    @property
    def sim_time_minutes(self) -> int:
        """Current elapsed simulation time in minutes."""
        return self._sim_time_minutes

    @property
    def run_id(self) -> str:
        """Unique simulation run identifier."""
        return self._run_id

    @property
    def event_store(self) -> EventStore:
        """Underlying append-only event repository."""
        return self._event_store

    def _find_hidden_result(self, code_or_name: str) -> Optional[HiddenResult]:
        """Find a hidden diagnostic finding in the case spec matching code or name."""
        target = str(code_or_name).strip().lower()
        if not target:
            return None
        for item in self._case_spec.hidden:
            if item.order_code.strip().lower() == target or item.order_name.strip().lower() == target:
                return item
        return None

    def request_vitals(self, actor: str = "nurse") -> Dict[str, Any]:
        """
        Request current patient vital signs.
        Produces exactly one event.
        """
        vitals = dict(self._agent_view.visible.initial_vitals)
        event = SimEvent(
            run_id=self._run_id,
            sim_time=self._sim_time_minutes,
            actor=actor,
            action="request_vitals",
            payload={"vitals": vitals},
            result_ref=None,
        )
        self._event_store.append(event)
        return vitals

    def _handle_diagnostic_order(
        self,
        code: str,
        action_name: str,
        actor: str,
        expected_category: Optional[str] = None,
    ) -> ActionResponse:
        """Internal dispatch for laboratory and imaging diagnostic orders."""
        matched = self._find_hidden_result(code)

        if matched is None:
            response = ActionResponse(
                status=OrderStatus.RESULT_UNAVAILABLE,
                order_code=code,
                order_name=None,
                turnaround_time_minutes=0,
                result=None,
                message=f"Diagnostic order '{code}' is unavailable in this case.",
                category=expected_category,
            )
            event = SimEvent(
                run_id=self._run_id,
                sim_time=self._sim_time_minutes,
                actor=actor,
                action=action_name,
                payload={"order_code": code, "status": "result_unavailable"},
                result_ref=None,
            )
            self._event_store.append(event)
            return response

        # Check if already released
        if self._agent_view.has_released(matched.order_code):
            released_val = self._agent_view.get_released_result(matched.order_code)
            response = ActionResponse(
                status=OrderStatus.RELEASED,
                order_code=matched.order_code,
                order_name=matched.order_name,
                turnaround_time_minutes=matched.turnaround_time_minutes,
                result=released_val,
                message=f"Order '{matched.order_name}' has already been released.",
                category=matched.category,
            )
            event = SimEvent(
                run_id=self._run_id,
                sim_time=self._sim_time_minutes,
                actor=actor,
                action=action_name,
                payload={"order_code": matched.order_code, "status": "already_released"},
                result_ref=matched.order_code,
            )
            self._event_store.append(event)
            return response

        # Check if already pending
        if matched.order_code in self._pending_orders:
            pending = self._pending_orders[matched.order_code]
            remaining = max(0, pending.ready_at_sim_time - self._sim_time_minutes)
            response = ActionResponse(
                status=OrderStatus.PENDING,
                order_code=matched.order_code,
                order_name=matched.order_name,
                turnaround_time_minutes=matched.turnaround_time_minutes,
                result=None,
                message=f"Order '{matched.order_name}' is currently in progress. Ready in {remaining} minutes.",
                category=matched.category,
            )
            event = SimEvent(
                run_id=self._run_id,
                sim_time=self._sim_time_minutes,
                actor=actor,
                action=action_name,
                payload={"order_code": matched.order_code, "status": "already_pending", "remaining_minutes": remaining},
                result_ref=matched.order_code,
            )
            self._event_store.append(event)
            return response

        # New order: evaluate turnaround time
        tat = matched.turnaround_time_minutes
        if tat <= 0:
            # Immediate release
            self._agent_view = self._case_spec.release_to_view(self._agent_view, matched.order_code)
            response = ActionResponse(
                status=OrderStatus.RELEASED,
                order_code=matched.order_code,
                order_name=matched.order_name,
                turnaround_time_minutes=0,
                result=matched.result,
                message=f"Order '{matched.order_name}' completed immediately.",
                category=matched.category,
            )
            event = SimEvent(
                run_id=self._run_id,
                sim_time=self._sim_time_minutes,
                actor=actor,
                action=action_name,
                payload={"order_code": matched.order_code, "status": "released", "turnaround_time_minutes": 0},
                result_ref=matched.order_code,
            )
            self._event_store.append(event)
            return response

        # Enqueued pending order
        ready_at = self._sim_time_minutes + tat
        self._pending_orders[matched.order_code] = PendingOrder(
            order_code=matched.order_code,
            order_name=matched.order_name,
            category=matched.category,
            ordered_at_sim_time=self._sim_time_minutes,
            ready_at_sim_time=ready_at,
            actor=actor,
        )
        response = ActionResponse(
            status=OrderStatus.PENDING,
            order_code=matched.order_code,
            order_name=matched.order_name,
            turnaround_time_minutes=tat,
            result=None,
            message=f"Order '{matched.order_name}' placed. Estimated turnaround: {tat} minutes.",
            category=matched.category,
        )
        event = SimEvent(
            run_id=self._run_id,
            sim_time=self._sim_time_minutes,
            actor=actor,
            action=action_name,
            payload={"order_code": matched.order_code, "status": "pending", "turnaround_time_minutes": tat, "ready_at": ready_at},
            result_ref=matched.order_code,
        )
        self._event_store.append(event)
        return response

    def order_lab(self, code: str, actor: str = "doctor") -> ActionResponse:
        """
        Order a laboratory test.
        Enforces turnaround time and validates against hidden case data.
        Produces exactly one event.
        """
        return self._handle_diagnostic_order(
            code=code,
            action_name="order_lab",
            actor=actor,
            expected_category="laboratory",
        )

    def order_imaging(self, code: str, actor: str = "doctor") -> ActionResponse:
        """
        Order an imaging study or diagnostic tracing (ECG, X-Ray, CT, etc.).
        Enforces turnaround time and validates against hidden case data.
        Produces exactly one event.
        """
        return self._handle_diagnostic_order(
            code=code,
            action_name="order_imaging",
            actor=actor,
            expected_category="imaging",
        )

    def request_medication_info(self, drug_name: str, actor: str = "pharmacist") -> Dict[str, Any]:
        """
        Request medication profile or patient home medication details.
        Produces exactly one event.
        """
        clean_name = str(drug_name).strip().lower()
        current_meds = self._agent_view.visible.current_medications
        allergies = self._agent_view.visible.allergies

        matched_meds = [m for m in current_meds if clean_name in m.lower()]
        matched_allergies = [a for a in allergies if clean_name in a.lower()]

        info = {
            "query": drug_name,
            "patient_on_drug": len(matched_meds) > 0,
            "matched_home_medications": matched_meds,
            "matched_allergies": matched_allergies,
            "documented_allergies": list(allergies),
        }

        event = SimEvent(
            run_id=self._run_id,
            sim_time=self._sim_time_minutes,
            actor=actor,
            action="request_medication_info",
            payload={"drug_name": drug_name, "info": info},
            result_ref=None,
        )
        self._event_store.append(event)
        return info

    def consult(self, role: str, query: str, actor: str = "doctor") -> Dict[str, Any]:
        """
        Request a specialist consultation.
        Produces exactly one event.
        """
        consult_data = {
            "status": "acknowledged",
            "role": role,
            "query": query,
            "consult_id": f"cns_{uuid.uuid4().hex[:8]}",
        }
        event = SimEvent(
            run_id=self._run_id,
            sim_time=self._sim_time_minutes,
            actor=actor,
            action="consult",
            payload={"role": role, "query": query, "consult_data": consult_data},
            result_ref=consult_data["consult_id"],
        )
        self._event_store.append(event)
        return consult_data

    def submit_report(self, report: Dict[str, Any], actor: str = "doctor") -> Dict[str, Any]:
        """
        Submit final clinical workup or discharge report.
        Produces exactly one event.
        """
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        submission_result = {
            "status": "submitted",
            "report_id": report_id,
            "sim_time": self._sim_time_minutes,
        }
        event = SimEvent(
            run_id=self._run_id,
            sim_time=self._sim_time_minutes,
            actor=actor,
            action="submit_report",
            payload={"report": dict(report), "submission": submission_result},
            result_ref=report_id,
        )
        self._event_store.append(event)
        return submission_result

    def advance_clock(self, minutes: int, actor: str = "system") -> int:
        """
        Advance simulation clock by specified minutes.
        Releases any pending orders whose turnaround time has now elapsed.
        Produces exactly one event.
        """
        if minutes < 0:
            raise ValueError("Cannot advance simulation clock by negative minutes.")

        self._sim_time_minutes += minutes

        # Check and release pending orders whose ready time has been reached
        ready_orders: List[str] = []
        for code, pending in list(self._pending_orders.items()):
            if self._sim_time_minutes >= pending.ready_at_sim_time:
                self._agent_view = self._case_spec.release_to_view(self._agent_view, pending.order_code)
                ready_orders.append(pending.order_code)
                del self._pending_orders[code]

        event = SimEvent(
            run_id=self._run_id,
            sim_time=self._sim_time_minutes,
            actor=actor,
            action="advance_clock",
            payload={
                "minutes_advanced": minutes,
                "new_sim_time": self._sim_time_minutes,
                "released_orders": ready_orders,
            },
            result_ref=None,
        )
        self._event_store.append(event)
        return self._sim_time_minutes
