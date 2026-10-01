"""
Acceptance tests for STEP 54 (P9.4): new agent / department scaffold.

Criteria (from plan/prompts/phase-9-advanced/STEP-54_P9.4_new-agent-template.md):
1. Generated tests fail before implementation and pass after.
2. The new agent passes the Phase 5 test suites (permission, leakage, scoring
   behavior; full Phase-5 suites stay green).
3. Full regression suite passes.
Plus: scaffold artifact completeness, idempotency, CLI wiring.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_generated_agent(tmp_path: Path, role: str = "testrole"):
    """Run the scaffold generator into tmp and import the stub agent module."""
    from vh.agents.scaffold import generate_agent_scaffold

    result = generate_agent_scaffold(role=role, output_dir=str(tmp_path))
    module_path = tmp_path / "roles" / f"{role}.py"
    assert module_path.exists()
    spec = importlib.util.spec_from_file_location(f"gen_{role}", str(module_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return result, module


def test_scaffold_generates_all_artifacts(tmp_path: Path):
    """Agent class, prompt, permission entry, tool stubs, tests, docs, checklist."""
    from vh.agents.scaffold import generate_agent_scaffold

    result = generate_agent_scaffold(role="icu", department="ICU", output_dir=str(tmp_path))
    assert result["role"] == "icu"
    for key in ("agent_class", "prompt", "permissions", "tests", "docs"):
        path = Path(result["files"][key])
        assert path.exists(), f"missing artifact: {key}"
        assert path.stat().st_size > 0
    prompt_text = Path(result["files"]["prompt"]).read_text(encoding="utf-8")
    assert "icu" in prompt_text.lower()
    docs_text = Path(result["files"]["docs"]).read_text(encoding="utf-8")
    for item in ("implement", "test", "fix", "gate"):
        assert item in docs_text.lower()


def test_generated_tests_fail_before_implementation(tmp_path: Path):
    """Red state: generated stub tools raise before the agent is implemented."""
    from vh.cases.spec import AgentView, VisiblePresentation

    result, module = _load_generated_agent(tmp_path, role="testrole")
    agent_class = next(
        obj for name, obj in vars(module).items() if name.lower().startswith("testrole")
    )
    view = AgentView(
        case_id="CASE-TMP-001",
        specialty="Test",
        patient_ref="PAT-TMP-001",
        visible=VisiblePresentation(presentation="Test."),
        released_results=[],
        version="1.0.0",
    )
    agent = agent_class(agent_view=view, environment=None)
    assert agent.prompt_template_spec == result["prompt_spec"]
    with pytest.raises(NotImplementedError, match="not yet implemented"):
        agent.review_status()
    with pytest.raises(NotImplementedError, match="not yet implemented"):
        agent.record_note(note="hello")


def test_new_agent_passes_phase5_suites():
    """The shipped ICU proof agent: permission gating, isolation, live data."""
    from vh.agents.roles.icu import ICUAgent
    from vh.agents.roles.base import ToolPermissionError
    from vh.cases.spec import AgentView, CaseSpec, DataIsolationError, VisiblePresentation
    from vh.cases.schema import GroundTruth

    view = AgentView(
        case_id="CASE-ICU-001",
        specialty="Critical Care",
        patient_ref="PAT-ICU-001",
        visible=VisiblePresentation(
            presentation="Test.",
            initial_vitals={"hr": 130, "spo2": 88, "bp": "85/55"},
        ),
        released_results=[],
        version="1.0.0",
    )
    agent = ICUAgent(agent_view=view, environment=None)
    assert agent.role == "icu"

    # Permission: allowed tools execute, forbidden tools are blocked + logged.
    vitals = agent.invoke_tool("monitor_vitals")
    assert vitals["vitals"]["hr"] == 130
    assert any("tachycardia" in flag for flag in vitals["flags"])
    with pytest.raises(ToolPermissionError):
        agent.invoke_tool("diagnose", diagnosis="X")
    with pytest.raises(ToolPermissionError):
        agent.invoke_tool("order_medication", medication="X")

    # Leakage: CaseSpec injection is rejected; AgentView only.
    assert isinstance(agent.agent_view, AgentView)
    with pytest.raises(DataIsolationError):
        ICUAgent(
            agent_view=CaseSpec(  # type: ignore[arg-type]
                case_id="x",
                specialty="x",
                patient_ref="x",
                visible=VisiblePresentation(presentation="x"),
                ground_truth=GroundTruth(
                    primary_dx="x", acceptable_differential=[], expected_workup=[], red_flags=[]
                ),
            ),
            environment=None,
        )

    # Scoring behavior: deterministic summary over the live view.
    summary = agent.invoke_tool("assess_acuity")
    assert summary["status"] in ("stable", "watch", "critical")
    assert summary["status"] == "critical"


def test_scaffold_permission_entry_and_idempotency(tmp_path: Path):
    """Permission snippet appends cleanly once; re-runs are no-ops."""
    from vh.agents.scaffold import generate_agent_scaffold

    first = generate_agent_scaffold(role="icu", department="ICU", output_dir=str(tmp_path))
    snippet = Path(first["files"]["permissions"]).read_text(encoding="utf-8")
    assert "icu:" in snippet
    assert "review_status" in snippet and "record_note" in snippet
    second = generate_agent_scaffold(role="icu", department="ICU", output_dir=str(tmp_path))
    assert Path(second["files"]["permissions"]).read_text(encoding="utf-8") == snippet


def test_scaffold_prompt_versioned_and_loadable(tmp_path: Path):
    """Generated prompt follows the name@version convention."""
    from vh.agents.scaffold import generate_agent_scaffold

    result = generate_agent_scaffold(role="icu", department="ICU", output_dir=str(tmp_path))
    assert result["prompt_spec"] == "icu@1.0.0"
    assert Path(result["files"]["prompt"]).name == "1.0.0.md"


def test_new_agent_cli_wired():
    """`vh new-agent --help` exposes the scaffold command."""
    proc = subprocess.run(
        [sys.executable, "-m", "vh.cli", "new-agent", "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr
    assert "role" in proc.stdout.lower()
