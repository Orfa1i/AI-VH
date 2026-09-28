"""
Acceptance tests for Phase 0 | STEP 06 (P0.G: Phase 0 GATE).
Written before final gate verification to confirm all Phase 0 governance and technical criteria.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.unit
def test_all_phase_0_step_reports_exist_and_marked_done():
    """Verify STEP-01 through STEP-05 reports exist and have Status: DONE."""
    steps_dir = REPO_ROOT / "docs" / "steps"
    assert steps_dir.exists(), "docs/steps directory must exist"

    for step_num in range(1, 6):
        report_file = steps_dir / f"STEP-{step_num:02d}.md"
        assert report_file.exists(), f"Missing step report: {report_file}"
        content = report_file.read_text(encoding="utf-8")
        assert (
            "Status: DONE" in content
            or "**Status**: DONE" in content
            or "**Status:** DONE" in content
            or "Status: **DONE**" in content
        ), f"Step report {report_file.name} does not state Status: DONE"


@pytest.mark.unit
def test_required_governance_signoffs_exist_and_pass():
    """Verify H0.1 governance and H0.2 golden set signoffs exist, are dated, name reviewer, and state PASS."""
    signoffs_dir = REPO_ROOT / "docs" / "signoffs"
    assert signoffs_dir.exists(), "docs/signoffs directory must exist"

    h01_file = signoffs_dir / "H0.1-governance.md"
    assert h01_file.exists(), "H0.1 governance sign-off must exist"
    h01_content = h01_file.read_text(encoding="utf-8")
    assert "**Result:** PASS" in h01_content
    assert "**Reviewer:**" in h01_content
    assert "**Date:**" in h01_content

    golden_file = signoffs_dir / "golden-v1.md"
    assert golden_file.exists(), "H0.2 golden-v1 physician sign-off must exist"
    golden_content = golden_file.read_text(encoding="utf-8")
    assert "**Result:** PASS" in golden_content
    assert "**Reviewer:**" in golden_content
    assert "**Date:**" in golden_content
    assert "## Approved items" in golden_content


@pytest.mark.unit
def test_golden_v1_satisfies_min_verified_cases_and_manifest():
    """Verify golden set v1 has at least min_verified_cases (50) and matches manifest."""
    from eval.harness.manifest import validate_manifest
    from vh.common.thresholds import load_thresholds

    golden_v1_dir = REPO_ROOT / "eval" / "golden" / "v1"
    assert golden_v1_dir.exists(), "eval/golden/v1 directory must exist"

    # Validate cryptographic manifest
    validate_manifest(golden_v1_dir)

    # Count verified cases
    cases = [p for p in golden_v1_dir.glob("*.json") if p.name != "manifest.json"]
    thresholds = load_thresholds()
    min_required = thresholds.get("golden", "min_verified_cases")

    assert min_required is not None, "golden.min_verified_cases must be set in thresholds.yaml"
    assert len(cases) >= min_required, (
        f"Golden v1 has {len(cases)} cases, but thresholds require at least {min_required}"
    )


@pytest.mark.unit
def test_phase_0_gate_evaluation_runner_passes_cleanly(tmp_path):
    """Verify evaluation harness runs on golden v1 and passes all evaluated thresholds."""
    from eval.harness.runner import run_evaluation

    run_id = "test-phase-0-gate-eval"
    report = run_evaluation(
        golden_version="v1",
        pipeline_name="dummy",
        run_id=run_id,
        reports_dir=str(tmp_path / "reports")
    )

    assert report.overall_status == "PASS"
    assert report.cases_evaluated >= 50
    assert "min_verified_cases" in report.metrics
    assert report.metrics["min_verified_cases"]["status"] == "PASS"


@pytest.mark.unit
def test_phase_0_gate_fails_closed_on_insufficient_cases(tmp_path):
    """Verify that gate evaluation fails closed if verified cases count is below threshold."""
    import shutil
    from eval.harness.manifest import generate_manifest
    from eval.harness.runner import run_evaluation

    # Create an undersized golden set with only 2 cases
    mock_golden_dir = tmp_path / "golden" / "undersized"
    mock_golden_dir.mkdir(parents=True)

    src_cases = list((REPO_ROOT / "eval" / "golden" / "v1").glob("*.json"))[:2]
    for sc in src_cases:
        shutil.copy(sc, mock_golden_dir / sc.name)
    generate_manifest(mock_golden_dir, version_tag="undersized")

    report = run_evaluation(
        golden_version="undersized",
        pipeline_name="dummy",
        golden_base_dir=str(tmp_path / "golden"),
        reports_dir=str(tmp_path / "reports")
    )

    # Must fail closed because 2 < 50
    assert report.overall_status == "FAIL"
    assert report.metrics["min_verified_cases"]["status"] == "FAIL"
