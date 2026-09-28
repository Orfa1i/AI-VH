"""
Acceptance tests for Phase 0 | STEP 04 (P0.4: Evaluation harness and frozen golden-set mechanism).
Written before implementation to verify red-to-green TDD cycle.
"""

import json
import shutil
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


@pytest.mark.unit
def test_dummy_pipeline_scores_end_to_end_and_writes_reports(tmp_path):
    """Verify that the dummy pipeline is scored end-to-end and reports are generated."""
    from eval.harness.runner import run_evaluation

    run_id = "test-run-dummy-001"
    output_dir = tmp_path / "reports"

    report_result = run_evaluation(
        golden_version="v1",
        pipeline_name="dummy",
        run_id=run_id,
        reports_dir=str(output_dir)
    )

    assert report_result is not None
    assert report_result.total_cases > 0
    assert report_result.run_id == run_id

    # Verify report files were generated on disk
    json_report = output_dir / run_id / "report.json"
    md_report = output_dir / run_id / "report.md"
    assert json_report.exists(), "report.json must be written"
    assert md_report.exists(), "report.md must be written"

    # Verify report structure
    data = json.loads(json_report.read_text(encoding="utf-8"))
    assert "metrics" in data
    assert "overall_status" in data
    assert "cases_evaluated" in data
    assert len(data["metrics"]) > 0


@pytest.mark.unit
def test_modifying_frozen_version_refuses_with_clear_error(tmp_path):
    """Verify that modifying any file in a frozen release makes the harness refuse with a clear error."""
    from eval.harness.manifest import GoldenSetIntegrityError
    from eval.harness.runner import run_evaluation

    # Copy golden set v1 to a temporary isolated directory to tamper with
    temp_golden_dir = tmp_path / "eval" / "golden"
    shutil.copytree(REPO_ROOT / "eval" / "golden", temp_golden_dir)

    # Tamper with one case file
    target_case = list((temp_golden_dir / "v1").glob("*.json"))[0]
    tampered_content = target_case.read_text(encoding="utf-8") + " "
    target_case.write_text(tampered_content, encoding="utf-8")

    # Harness MUST refuse to run and raise GoldenSetIntegrityError
    with pytest.raises(GoldenSetIntegrityError) as exc_info:
        run_evaluation(
            golden_version="v1",
            pipeline_name="dummy",
            golden_base_dir=str(temp_golden_dir)
        )

    assert "integrity mismatch" in str(exc_info.value).lower() or "tampered" in str(exc_info.value).lower() or "hash" in str(exc_info.value).lower()


@pytest.mark.unit
def test_metric_with_no_or_null_threshold_reports_fail():
    """Verify that a metric with no threshold, or a null threshold, reports FAIL (never silent PASS)."""
    from eval.harness.runner import evaluate_metrics_against_thresholds

    # Metrics where one has a set threshold, one has null threshold, one has no threshold
    computed_metrics = {
        "schema_valid_rate": 1.0,      # In thresholds: 1.0 (PASS)
        "dx_top3_min": 0.95,           # In thresholds: null (NOT SET -> MUST FAIL)
        "unregistered_metric": 0.88    # Not in thresholds -> MUST FAIL
    }

    results = evaluate_metrics_against_thresholds(computed_metrics)

    # schema_valid_rate passes
    assert results["schema_valid_rate"]["status"] == "PASS"

    # dx_top3_min (null threshold) MUST FAIL
    assert results["dx_top3_min"]["status"] == "FAIL"
    assert results["dx_top3_min"]["reason"] in ("NOT_SET", "THRESHOLD_NOT_SET")

    # unregistered_metric (no threshold) MUST FAIL
    assert results["unregistered_metric"]["status"] == "FAIL"
    assert "MISSING" in results["unregistered_metric"]["reason"] or "NO_THRESHOLD" in results["unregistered_metric"]["reason"]


@pytest.mark.unit
def test_identical_inputs_give_identical_report(tmp_path):
    """Verify that identical inputs produce an identical report (ignoring timestamps)."""
    from eval.harness.runner import run_evaluation

    dir_a = tmp_path / "reports_a"
    dir_b = tmp_path / "reports_b"

    rep_a = run_evaluation(golden_version="v1", pipeline_name="dummy", run_id="run-a", reports_dir=str(dir_a))
    rep_b = run_evaluation(golden_version="v1", pipeline_name="dummy", run_id="run-b", reports_dir=str(dir_b))

    json_a = json.loads((dir_a / "run-a" / "report.json").read_text(encoding="utf-8"))
    json_b = json.loads((dir_b / "run-b" / "report.json").read_text(encoding="utf-8"))

    # Remove non-deterministic timestamps and run_ids before equality comparison
    for rep in (json_a, json_b):
        rep.pop("timestamp", None)
        rep.pop("run_id", None)
        rep.pop("duration_seconds", None)

    assert json_a == json_b, "Evaluation reports must be strictly deterministic for identical inputs"


@pytest.mark.unit
def test_pipeline_never_receives_ground_truth():
    """Verify that the harness passes only the CaseView to the pipeline, never ground truth."""
    from eval.harness.interfaces import CaseView, SpyPipeline
    from eval.harness.runner import run_evaluation

    spy = SpyPipeline()
    run_evaluation(golden_version="v1", pipeline_instance=spy)

    assert len(spy.received_cases) > 0, "Spy pipeline must have processed cases"

    for case_view in spy.received_cases:
        assert isinstance(case_view, CaseView)
        assert not hasattr(case_view, "ground_truth"), "CaseView must not expose ground_truth attribute"
        assert "ground_truth" not in case_view.model_dump(), "CaseView dictionary representation must omit ground_truth"
