"""
New agent/department scaffold for AI-VH (STEP 54 / P9.4).

`generate_agent_scaffold` emits every artifact a new clinical agent needs --
agent class with tool stubs, versioned prompt, permission snippet, starter
tests, and a docs page with the implement/test/fix/gate checklist -- into an
output directory (repository paths by default, tmp paths in tests). Permission
snippets are emitted as files for deliberate application, never auto-merged.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_TOOLS = ["review_status", "record_note"]


def _class_name(role: str) -> str:
    clean = "".join(word.capitalize() for word in role.replace("-", "_").split("_") if word)
    return f"{clean}Agent" if clean else "CustomAgent"


def _agent_source(role: str, class_name: str, tools: List[str]) -> str:
    methods = []
    for tool in tools:
        if tool == "record_note":
            methods.append(
                f'    def record_note(self, note: str = "") -> Dict[str, Any]:\n'
                f'        """Record a {role} note. STUB: implement before use."""\n'
                f'        raise NotImplementedError("{tool} not yet implemented for {role}.")\n'
            )
        else:
            methods.append(
                f'    def {tool}(self) -> Dict[str, Any]:\n'
                f'        """STUB: implement before use."""\n'
                f'        raise NotImplementedError("{tool} not yet implemented for {role}.")\n'
            )
    body = "\n".join(methods)
    return f'''"""
{role.title()} specialist agent for AI-VH (scaffolded).
STUB IMPLEMENTATION: replace each NotImplementedError with real logic,
following the implement/test/fix/gate checklist in docs/agents/{role}.md.
"""

from typing import Any, Dict, Optional

from vh.agents.roles.base import BaseAgent
from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment


class {class_name}(BaseAgent):
    """{role.title()} agent operating over an isolated AgentView."""

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[Any] = None,
        prompt_template_spec: str = "{role}@1.0.0",
    ) -> None:
        super().__init__(
            role="{role}",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )

{body}'''


def _prompt_source(role: str, department: str) -> str:
    department_line = f"Assigned department: {department}." if department else ""
    return f"""# {role.title()} Agent System Prompt v1.0.0

You are the {role} specialist in the AI Virtual Hospital.
{department_line}

## Clinical Protocol:
1. Operate strictly over the isolated AgentView; never request hidden data.
2. Execute only tools permitted for your role.
3. Ground every statement in released findings.

## Constraints:
- Scaffold prompt: refine during implementation, then freeze as a new version.
"""


def _permissions_snippet(role: str, tools: List[str]) -> str:
    allowed = "\n".join(f'    - "{tool}"' for tool in tools)
    return f"""# Permission snippet for role '{role}' (generated scaffold).
# Apply deliberately to configs/agents/permissions.yaml after review.
{role}:
  role: "{role}"
  description: "Scaffolded {role} specialist (refine during implementation)"
  allowed_tools:
{allowed}
  forbidden_tools:
    - "order_medication"
    - "diagnose"
    - "order_lab"
    - "order_imaging"
    - "submit_report"
"""


def _tests_source(role: str, class_name: str, tools: List[str]) -> str:
    stub_calls = "\n".join(
        f'    with pytest.raises(NotImplementedError):\n        agent.invoke_tool("{tool}")'
        if tool != "record_note"
        else f'    with pytest.raises(NotImplementedError):\n        agent.invoke_tool("{tool}", note="x")'
        for tool in tools
    )
    return f'''"""
Acceptance tests for the {role} agent (scaffolded).
Prerequisite: apply the permission snippet to configs/agents/permissions.yaml.
RED: allowed tools raise NotImplementedError (they clear permission gating).
Implement the agent, then GREEN.
"""

import pytest

from vh.agents.roles.base import ToolPermissionError
from vh.cases.schema import GroundTruth
from vh.cases.spec import AgentView, CaseSpec, DataIsolationError, VisiblePresentation


def _view() -> AgentView:
    return AgentView(
        case_id="CASE-{role.upper()}-001",
        specialty="General",
        patient_ref="PAT-{role.upper()}-001",
        visible=VisiblePresentation(presentation="Scaffold fixture."),
        released_results=[],
        version="1.0.0",
    )


def _spec() -> CaseSpec:
    return CaseSpec(
        case_id="CASE-{role.upper()}-001",
        specialty="General",
        patient_ref="PAT-{role.upper()}-001",
        visible=VisiblePresentation(presentation="Scaffold fixture."),
        ground_truth=GroundTruth(
            primary_dx="X", acceptable_differential=[], expected_workup=[], red_flags=[]
        ),
    )


def test_permission_gating():
    """Allowed tools pass the permission layer; forbidden tools are blocked."""
    from vh.agents.roles.{role} import {class_name}

    agent = {class_name}(agent_view=_view(), environment=None)
    # Before implementation the allowed tools raise NotImplementedError
    # (proves they cleared permission gating instead of ToolPermissionError).
{stub_calls}
    with pytest.raises(ToolPermissionError):
        agent.invoke_tool("diagnose", diagnosis="X")


def test_agent_view_isolation():
    """The agent rejects CaseSpec injection (no leakage)."""
    from vh.agents.roles.{role} import {class_name}

    with pytest.raises(DataIsolationError):
        {class_name}(agent_view=_spec(), environment=None)  # type: ignore[arg-type]
    assert isinstance({class_name}(agent_view=_view(), environment=None).agent_view, AgentView)


def test_scoring_behavior():
    """Deterministic summaries over the live AgentView (fill in per agent)."""
    from vh.agents.roles.{role} import {class_name}

    first = {class_name}(agent_view=_view(), environment=None)
    second = {class_name}(agent_view=_view(), environment=None)
    assert first.role == second.role == "{role}"
'''


def _docs_source(role: str, department: str, tools: List[str]) -> str:
    department_line = f"Department: {department}\n" if department else ""
    return f"""# {role.title()} Agent

Role: `{role}`
{department_line}Prompt: `{role}@1.0.0`
Tools: {", ".join(f"`{tool}`" for tool in tools)}

## Checklist (implement, test, fix, gate)

1. **Implement**: replace every `NotImplementedError` stub in
   `src/vh/agents/roles/{role}.py` with real AgentView-derived logic.
   Refine the prompt, then freeze any change as a new version.
2. **Test**: fill in `tests/test_{role}_agent.py`; run it RED, implement,
   re-run GREEN. Cover permission gating, AgentView isolation, and scoring
   behavior (deterministic summaries over the live view).
3. **Fix**: apply the permission snippet to `configs/agents/permissions.yaml`
   deliberately (never auto-merged); register exports in
   `src/vh/agents/roles/__init__.py`.
4. **Gate**: run the Phase-5 suites plus the full regression suite; record the
   outcome in the step report before merging.
"""


def generate_agent_scaffold(
    role: str,
    department: str = "",
    tools: Optional[List[str]] = None,
    output_dir: str = ".",
) -> Dict[str, Any]:
    """Generate all scaffold artifacts for a new agent role. Returns manifest."""
    clean_role = role.strip().lower().replace(" ", "_")
    if not clean_role or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_" for ch in clean_role):
        raise ValueError(f"Invalid role name: {role!r}. Use lowercase letters, digits, underscores.")
    tool_list = list(tools) if tools else list(DEFAULT_TOOLS)
    class_name = _class_name(clean_role)
    root = Path(output_dir)

    files = {
        "agent_class": root / "roles" / f"{clean_role}.py",
        "prompt": root / "prompts" / clean_role / "1.0.0.md",
        "permissions": root / "permissions" / f"{clean_role}.yaml",
        "tests": root / "tests" / f"test_{clean_role}_agent.py",
        "docs": root / "docs" / f"{clean_role}.md",
    }
    contents = {
        "agent_class": _agent_source(clean_role, class_name, tool_list),
        "prompt": _prompt_source(clean_role, department),
        "permissions": _permissions_snippet(clean_role, tool_list),
        "tests": _tests_source(clean_role, class_name, tool_list),
        "docs": _docs_source(clean_role, department, tool_list),
    }
    for key, path in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents[key], encoding="utf-8")
    return {
        "role": clean_role,
        "class_name": class_name,
        "prompt_spec": f"{clean_role}@1.0.0",
        "tools": tool_list,
        "files": {key: str(path) for key, path in files.items()},
    }
