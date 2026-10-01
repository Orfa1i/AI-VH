"""
Intensive Care Unit (ICU) monitoring agent for AI-VH (STEP 54 proof agent).

Deterministic, AgentView-derived monitoring: vital-sign flagging against
documented critical/watch thresholds (mirroring red-flag criteria) and
acuity summaries. No diagnosis, no prescribing, no orders.
"""

from typing import Any, Dict, List, Optional

from vh.agents.roles.base import BaseAgent
from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter

# Thresholds mirror the red-flag criteria tables (presentation of data, not diagnosis).
CRITICAL_LIMITS = {"hr_high": 120.0, "spo2_low": 90.0, "sbp_low": 90.0}
WATCH_LIMITS = {"hr_high": 100.0, "spo2_low": 94.0, "sbp_low": 100.0}


def _parse_sbp(bp: Any) -> Optional[float]:
    try:
        return float(str(bp).split("/")[0])
    except (ValueError, IndexError, AttributeError):
        return None


def flag_vitals(vitals: Dict[str, Any]) -> List[str]:
    """Flag threshold crossings in triage vitals. Pure function."""
    flags: List[str] = []
    try:
        hr = float(vitals.get("hr", 0) or 0)
    except (ValueError, TypeError):
        hr = 0.0
    try:
        spo2 = float(vitals.get("spo2", 100) or 100)
    except (ValueError, TypeError):
        spo2 = 100.0
    sbp = _parse_sbp(vitals.get("bp", ""))
    if hr >= CRITICAL_LIMITS["hr_high"]:
        flags.append("tachycardia: heart rate critically elevated")
    elif hr >= WATCH_LIMITS["hr_high"]:
        flags.append("tachycardia watch: heart rate elevated")
    if spo2 <= CRITICAL_LIMITS["spo2_low"]:
        flags.append("hypoxemia: SpO2 critically low")
    elif spo2 <= WATCH_LIMITS["spo2_low"]:
        flags.append("hypoxemia watch: SpO2 low")
    if sbp is not None:
        if sbp <= CRITICAL_LIMITS["sbp_low"]:
            flags.append("hypotension: systolic pressure critically low")
        elif sbp <= WATCH_LIMITS["sbp_low"]:
            flags.append("hypotension watch: systolic pressure low")
    return flags


def acuity_status(flags: List[str]) -> str:
    """Summarize flags into an acuity band. Deterministic."""
    if any("critically" in flag for flag in flags):
        return "critical"
    if flags:
        return "watch"
    return "stable"


class ICUAgent(BaseAgent):
    """ICU monitoring agent operating over an isolated AgentView."""

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: str = "icu@1.0.0",
    ) -> None:
        super().__init__(
            role="icu",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )

    def monitor_vitals(self) -> Dict[str, Any]:
        """Return current vitals with threshold flags."""
        vitals = dict(self.agent_view.initial_vitals)
        flags = flag_vitals(vitals)
        res = {"vitals": vitals, "flags": flags}
        self.record_event(action="monitor_vitals", payload={"flags": flags})
        return res

    def assess_acuity(self) -> Dict[str, Any]:
        """Deterministic acuity summary over the live view."""
        vitals = dict(self.agent_view.initial_vitals)
        flags = flag_vitals(vitals)
        res = {"status": acuity_status(flags), "flags": flags, "vitals": vitals}
        self.record_event(action="assess_acuity", payload={"status": res["status"]})
        return res

    def record_icu_note(self, note: str = "") -> Dict[str, Any]:
        """Record an ICU observation note."""
        res = {"status": "noted", "note": str(note)}
        self.record_event(action="record_icu_note", payload=res)
        return res
