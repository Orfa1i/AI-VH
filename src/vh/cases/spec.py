"""
Case specification schema, AgentView isolation, and clinical data models for AI-VH.
Enforces structural separation between visible patient presentation, hidden diagnostic
results, and gold-standard ground truth to make information leakage impossible.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, Set
from pydantic import BaseModel, Field, field_validator

from .schema import GoldenCase, GroundTruth, SupportingReference


class DataIsolationError(PermissionError):
    """
    Raised when an unauthorized attempt is made to access isolated ground truth
    or unreleased hidden diagnostic findings from an AgentView.
    """
    pass


_FORBIDDEN_AGENTVIEW_ATTRIBUTES: Set[str] = {
    "hidden",
    "hidden_results",
    "_hidden",
    "_hidden_results",
    "ground_truth",
    "_ground_truth",
    "primary_dx",
    "acceptable_differential",
    "expected_workup",
    "red_flags",
}


class VisiblePresentation(BaseModel):
    """
    Visible clinical data available to agents and clinicians at time of initial presentation.
    Contains initial triage information, history, medications, allergies, and vitals.
    """
    presentation: str = Field(
        default="",
        description="Clinical presentation narrative, chief complaint, or history of present illness"
    )
    demographics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Patient demographic attributes including age, gender, and administrative baseline"
    )
    history: str = Field(
        default="",
        description="Past medical, past surgical, social, and relevant family history"
    )
    current_medications: List[str] = Field(
        default_factory=list,
        description="Current outpatient and home medications prior to encounter"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="Documented drug, food, and environmental allergies"
    )
    initial_vitals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Initial triage vital signs (blood pressure, heart rate, respiratory rate, SpO2, temperature)"
    )
    exam: Optional[str] = Field(
        default=None,
        description="Physical examination observations conducted during triage"
    )
    raw_attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preserved raw presentation dictionary for lossless GoldenCase round-tripping"
    )


class HiddenResult(BaseModel):
    """
    Diagnostic laboratory, imaging, or procedural finding released only on request.
    Includes turnaround time and standard order identification.
    """
    order_code: str = Field(
        description="Order identifier or catalog code (e.g. LAB-TROP, DX-ECG, 49563-0)"
    )
    order_name: str = Field(
        description="Clinical display name of the test, procedure, or diagnostic study"
    )
    result: Any = Field(
        description="Diagnostic report, quantitative laboratory value, or structured finding"
    )
    turnaround_time_minutes: int = Field(
        default=30,
        description="Simulated clinical turnaround time in minutes before result becomes available"
    )
    category: Optional[str] = Field(
        default=None,
        description="Diagnostic modality: laboratory, imaging, electrocardiography, or procedure"
    )
    loinc_code: Optional[str] = Field(
        default=None,
        description="Standard LOINC code for interoperable laboratory mapping"
    )
    status: str = Field(
        default="completed",
        description="Order execution status"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw finding dictionary for lossless GoldenCase round-tripping"
    )


class ReleasedResult(BaseModel):
    """
    Diagnostic result that has been explicitly ordered, completed, and released to an AgentView.
    """
    order_code: str = Field(description="Order identifier")
    order_name: str = Field(description="Clinical order name")
    result: Any = Field(description="Released diagnostic result")
    turnaround_time_minutes: int = Field(default=30, description="Elapsed turnaround time in minutes")
    category: Optional[str] = Field(default=None, description="Diagnostic modality")
    loinc_code: Optional[str] = Field(default=None, description="Standard LOINC code")
    released_at: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp when result was released to the agent view"
    )


class AgentView(BaseModel):
    """
    Sanitized, strictly isolated patient view. The ONLY object clinical agents,
    RAG pipelines, or LLM generators receive during simulation and evaluation.
    
    Architectural Guarantees:
    1. Holds no reference to hidden results or ground truth.
    2. Any attempt to inspect forbidden fields raises DataIsolationError.
    3. Serialization produces zero hidden or ground-truth keys.
    4. Immutable and frozen to prevent unauthorized client modifications.
    """
    case_id: str = Field(description="Case identifier")
    specialty: str = Field(description="Clinical specialty or target cohort")
    patient_ref: str = Field(description="Reference identifier to underlying synthetic patient record")
    visible: VisiblePresentation = Field(description="Visible clinical presentation data")
    released_results: List[ReleasedResult] = Field(
        default_factory=list,
        description="Diagnostic results explicitly requested and released by simulation environment"
    )
    version: str = Field(default="1.0.0", description="Schema specification version")

    model_config = {
        "extra": "forbid",
        "frozen": True,
        "validate_assignment": True,
    }

    def __getattr__(self, name: str) -> Any:
        name_lower = name.lower()
        if name in _FORBIDDEN_AGENTVIEW_ATTRIBUTES or name_lower in _FORBIDDEN_AGENTVIEW_ATTRIBUTES:
            raise DataIsolationError(
                f"Data Isolation Breach: '{name}' is strictly isolated and inaccessible from AgentView."
            )
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __getitem__(self, item: str) -> Any:
        item_lower = item.lower()
        if item in _FORBIDDEN_AGENTVIEW_ATTRIBUTES or item_lower in _FORBIDDEN_AGENTVIEW_ATTRIBUTES:
            raise DataIsolationError(
                f"Data Isolation Breach: '{item}' is strictly isolated and inaccessible from AgentView."
            )
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(f"'{item}' not present in AgentView")

    def get(self, key: str, default: Any = None) -> Any:
        key_lower = key.lower()
        if key in _FORBIDDEN_AGENTVIEW_ATTRIBUTES or key_lower in _FORBIDDEN_AGENTVIEW_ATTRIBUTES:
            raise DataIsolationError(
                f"Data Isolation Breach: '{key}' is strictly isolated and inaccessible from AgentView."
            )
        if hasattr(self, key):
            return getattr(self, key)
        return default

    # Convenience clinical properties
    @property
    def presentation(self) -> str:
        return self.visible.presentation

    @property
    def demographics(self) -> Dict[str, Any]:
        return self.visible.demographics

    @property
    def history(self) -> str:
        return self.visible.history

    @property
    def current_medications(self) -> List[str]:
        return self.visible.current_medications

    @property
    def allergies(self) -> List[str]:
        return self.visible.allergies

    @property
    def initial_vitals(self) -> Dict[str, Any]:
        return self.visible.initial_vitals

    @property
    def exam(self) -> Optional[str]:
        return self.visible.exam

    def has_released(self, order_identifier: str) -> bool:
        """Check whether an order has been released into this view."""
        target = order_identifier.strip().lower()
        return any(
            r.order_code.strip().lower() == target or r.order_name.strip().lower() == target
            for r in self.released_results
        )

    def get_released_result(self, order_identifier: str) -> Optional[Any]:
        """Retrieve finding for a released order, or None if not released."""
        target = order_identifier.strip().lower()
        for r in self.released_results:
            if r.order_code.strip().lower() == target or r.order_name.strip().lower() == target:
                return r.result
        return None

    def with_released_result(self, released: ReleasedResult) -> "AgentView":
        """Return a new immutable AgentView incorporating the newly released diagnostic result."""
        # Replace existing result for same order code if present, otherwise append
        filtered = [r for r in self.released_results if r.order_code != released.order_code]
        updated_list = filtered + [released]
        return AgentView(
            case_id=self.case_id,
            specialty=self.specialty,
            patient_ref=self.patient_ref,
            visible=self.visible,
            released_results=updated_list,
            version=self.version,
        )


class CaseSpec(BaseModel):
    """
    Complete clinical case specification containing visible presentation, hidden diagnostic
    results, and authoritative gold-standard ground truth.
    
    Used exclusively by simulation environments, evaluation scorers, and attending reviewers.
    Agents and generation pipelines must NEVER receive a CaseSpec directly.
    """
    case_id: str = Field(description="Unique case identifier")
    specialty: str = Field(description="Clinical specialty")
    patient_ref: str = Field(description="Synthetic patient reference identifier")
    visible: VisiblePresentation = Field(description="Visible presentation details")
    hidden: List[HiddenResult] = Field(
        default_factory=list,
        description="Hidden diagnostic findings released only on request"
    )
    ground_truth: GroundTruth = Field(description="Gold-standard clinical ground truth")
    supporting_references: List[SupportingReference] = Field(
        default_factory=list,
        description="Medical textbook and peer-reviewed literature citations"
    )
    status: Literal["draft", "verified"] = "draft"
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_agent_view(self, released_orders: Optional[List[str]] = None) -> AgentView:
        """
        Generate a strictly isolated AgentView.
        If released_orders is provided, populates only those requested findings.
        Ground truth and remaining hidden results are completely excluded.
        """
        released_list: List[ReleasedResult] = []
        if released_orders:
            for order in released_orders:
                try:
                    rel = self.release(order)
                    released_list.append(rel)
                except KeyError:
                    pass

        return AgentView(
            case_id=self.case_id,
            specialty=self.specialty,
            patient_ref=self.patient_ref,
            visible=self.visible,
            released_results=released_list,
            version=self.version,
        )

    def release(
        self,
        order: str,
        audit_logger: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ReleasedResult:
        """
        Release a single hidden diagnostic finding matching the specified order name or code.
        Logs the release event if an audit_logger callback is provided.
        """
        target = order.strip().lower()
        matched: Optional[HiddenResult] = None
        for item in self.hidden:
            if item.order_code.strip().lower() == target or item.order_name.strip().lower() == target:
                matched = item
                break

        if matched is None:
            raise KeyError(f"Order '{order}' not found in hidden case results for case {self.case_id}")

        released = ReleasedResult(
            order_code=matched.order_code,
            order_name=matched.order_name,
            result=matched.result,
            turnaround_time_minutes=matched.turnaround_time_minutes,
            category=matched.category,
            loinc_code=matched.loinc_code,
            released_at=datetime.now(timezone.utc).isoformat(),
        )

        if audit_logger is not None:
            audit_logger({
                "timestamp": released.released_at,
                "case_id": self.case_id,
                "order_code": matched.order_code,
                "order_name": matched.order_name,
                "turnaround_time_minutes": matched.turnaround_time_minutes,
                "status": "released",
            })

        return released

    def release_to_view(
        self,
        view: AgentView,
        order: str,
        audit_logger: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> AgentView:
        """
        Release a diagnostic finding and return an updated AgentView containing the result.
        """
        released = self.release(order, audit_logger=audit_logger)
        return view.with_released_result(released)

    @classmethod
    def from_golden_case(cls, golden_case: GoldenCase) -> "CaseSpec":
        """
        Convert a GoldenCase instance into a CaseSpec with 100% lossless fidelity.
        """
        vis_raw = golden_case.visible_presentation
        pres = str(vis_raw.get("presentation") or vis_raw.get("chief_complaint") or "")
        history = str(vis_raw.get("history") or "")
        meds = list(vis_raw.get("current_medications") or [])
        allergies = list(vis_raw.get("allergies") or [])
        vitals = dict(vis_raw.get("initial_vitals") or vis_raw.get("vitals") or {})
        demographics = dict(vis_raw.get("demographics") or {})
        exam = vis_raw.get("exam")

        visible = VisiblePresentation(
            presentation=pres,
            demographics=demographics,
            history=history,
            current_medications=meds,
            allergies=allergies,
            initial_vitals=vitals,
            exam=exam,
            raw_attributes=dict(vis_raw),
        )

        hidden_items: List[HiddenResult] = []
        for raw_item in golden_case.hidden_results:
            order_code = str(raw_item.get("order_code") or raw_item.get("order") or "UNKNOWN")
            order_name = str(raw_item.get("order_name") or raw_item.get("order") or order_code)
            result = raw_item.get("result")
            tat = int(raw_item.get("turnaround_time_minutes") or raw_item.get("turnaround_time") or 30)
            category = raw_item.get("category")
            loinc = raw_item.get("loinc_code")

            hidden_items.append(
                HiddenResult(
                    order_code=order_code,
                    order_name=order_name,
                    result=result,
                    turnaround_time_minutes=tat,
                    category=category,
                    loinc_code=loinc,
                    metadata=dict(raw_item),
                )
            )

        return cls(
            case_id=golden_case.case_id,
            specialty=golden_case.specialty,
            patient_ref=golden_case.patient_ref,
            visible=visible,
            hidden=hidden_items,
            ground_truth=golden_case.ground_truth,
            supporting_references=golden_case.supporting_references,
            status=golden_case.status,
            reviewer=golden_case.reviewer,
            reviewed_at=golden_case.reviewed_at,
            version=golden_case.version,
        )

    def to_golden_case(self) -> GoldenCase:
        """
        Reconstruct a GoldenCase instance from this CaseSpec with 100% lossless fidelity.
        """
        if self.visible.raw_attributes:
            visible_dict = dict(self.visible.raw_attributes)
        else:
            visible_dict = {
                "chief_complaint": self.visible.presentation,
                "history": self.visible.history,
                "vitals": self.visible.initial_vitals,
                "demographics": self.visible.demographics,
                "current_medications": self.visible.current_medications,
                "allergies": self.visible.allergies,
            }
            if self.visible.exam:
                visible_dict["exam"] = self.visible.exam

        hidden_list: List[Dict[str, Any]] = []
        for item in self.hidden:
            if item.metadata:
                hidden_list.append(dict(item.metadata))
            else:
                hidden_list.append({
                    "order": item.order_name,
                    "result": item.result,
                    "order_code": item.order_code,
                    "turnaround_time_minutes": item.turnaround_time_minutes,
                })

        return GoldenCase(
            case_id=self.case_id,
            specialty=self.specialty,
            patient_ref=self.patient_ref,
            visible_presentation=visible_dict,
            hidden_results=hidden_list,
            ground_truth=self.ground_truth,
            supporting_references=self.supporting_references,
            status=self.status,
            reviewer=self.reviewer,
            reviewed_at=self.reviewed_at,
            version=self.version,
        )
