"""
Base clinical agent definition and tool-layer permission enforcement for AI-VH.
Guarantees that permissions are checked and blocked in the tool layer, never in prompt text alone.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import yaml

from vh.cases.spec import AgentView, CaseSpec, DataIsolationError
from vh.agents.environment import HospitalEnvironment
from vh.agents.events import SimEvent
from vh.common.prompts import load_prompt_template
from vh.generation.medgemma import MedGemmaAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
PERMISSIONS_CONFIG_PATH = REPO_ROOT / "configs" / "agents" / "permissions.yaml"


class ToolPermissionError(PermissionError):
    """Raised when an agent attempts to execute a tool not permitted for its role."""
    pass


def load_permissions_for_role(role: str) -> Dict[str, Set[str]]:
    """Load allowed and forbidden tool sets for a role from permissions.yaml."""
    if not PERMISSIONS_CONFIG_PATH.exists():
        return {"allowed_tools": set(), "forbidden_tools": set()}
    with open(PERMISSIONS_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    role_cfg = data.get(role, {})
    return {
        "allowed_tools": set(role_cfg.get("allowed_tools", [])),
        "forbidden_tools": set(role_cfg.get("forbidden_tools", [])),
    }


class BaseAgent:
    """
    Abstract clinical agent base class.
    
    Guarantees:
    1. Operates exclusively over AgentView-derived data. Direct CaseSpec injection is rejected.
    2. Tool execution is checked strictly against role permissions in configs/agents/permissions.yaml.
    3. Blocked tool executions raise ToolPermissionError and are logged in the agent's event stream.
    4. LLM calls route through MedGemmaAdapter using versioned prompt templates.
    """

    def __init__(
        self,
        role: str,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: Optional[str] = None,
    ) -> None:
        # Strict isolation check: reject CaseSpec or any non-AgentView object
        if not isinstance(agent_view, AgentView) or isinstance(agent_view, CaseSpec):
            raise DataIsolationError(
                "Data Isolation Breach: Agents must never receive a CaseSpec or ground truth directly. "
                "Agents must be initialized with an AgentView."
            )

        self.role: str = role
        self._agent_view: AgentView = agent_view
        self.environment: Optional[HospitalEnvironment] = environment
        self.adapter: Optional[MedGemmaAdapter] = adapter
        self.prompt_template_spec: str = prompt_template_spec or f"{role}@1.0.0"
        self.events: List[SimEvent] = []

        # Load role tool permissions
        perm_data = load_permissions_for_role(self.role)
        self.allowed_tools: Set[str] = perm_data["allowed_tools"]
        self.forbidden_tools: Set[str] = perm_data["forbidden_tools"]

    @property
    def agent_view(self) -> AgentView:
        """Return live AgentView from environment if attached, otherwise initial AgentView."""
        if self.environment is not None:
            return self.environment.agent_view
        return self._agent_view

    def load_system_prompt(self) -> str:
        """Load the versioned prompt template for this agent role."""
        return load_prompt_template(self.prompt_template_spec)

    def record_event(
        self,
        action: str,
        payload: Dict[str, Any],
        result_ref: Optional[str] = None,
    ) -> SimEvent:
        """Record an action event in the agent's internal history and environment store if present."""
        sim_time = self.environment.sim_time_minutes if self.environment else 0
        run_id = self.environment.run_id if self.environment else "local_run"

        event = SimEvent(
            run_id=run_id,
            sim_time=sim_time,
            actor=self.role,
            action=action,
            payload=payload,
            result_ref=result_ref,
        )
        self.events.append(event)

        if self.environment and hasattr(self.environment, "event_store"):
            self.environment.event_store.append(event)

        return event

    def invoke_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Execute a tool by name with strict tool-layer permission checking.
        If the tool is forbidden or unlisted, raises ToolPermissionError and logs the violation.
        """
        is_forbidden = tool_name in self.forbidden_tools
        is_not_allowed = tool_name not in self.allowed_tools

        if is_forbidden or is_not_allowed:
            # Log the blocked attempt
            self.record_event(
                action="tool_blocked",
                payload={
                    "tool_name": tool_name,
                    "reason": "permission_denied",
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                },
                result_ref=None,
            )
            raise ToolPermissionError(
                f"Role '{self.role}' is not permitted to execute tool '{tool_name}'."
            )

        # Dispatch to implementation method on self
        method = getattr(self, tool_name, None)
        if method is None:
            raise NotImplementedError(
                f"Tool '{tool_name}' is declared allowed for role '{self.role}', but no method implementation was found."
            )

        return method(**kwargs)
