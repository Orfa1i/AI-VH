"""
Evaluation harness runner for AI Virtual Hospital (AI-VH).
Executes clinical pipelines across frozen golden sets, evaluates outputs via registered scorers,
enforces strict thresholds from configs/thresholds.yaml, and emits deterministic reports.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from vh.cases.schema import CaseView, GoldenCase
from vh.common.thresholds import load_thresholds
from .interfaces import DummyPipeline, DummyScorer, Pipeline, PipelineResult, Scorer
from .manifest import validate_manifest


class EvaluationRunReport(BaseModel):
    run_id: str
    golden_version: str
    pipeline: str
    total_cases: int
    cases_evaluated: int
    overall_status: str
    metrics: Dict[str, Dict[str, Any]]
    timestamp: str
    duration_seconds: float = 0.0


# Directional comparator: metrics ending with _max, _count, or latency_s compare <= threshold
MAX_METRIC_SUBSTRINGS = ("_max", "_count", "latency_s")


def evaluate_metrics_against_thresholds(
    computed_metrics: Dict[str, float],
    thresholds_path: Optional[Union[str, Path]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Compare computed metrics against configs/thresholds.yaml.
    Strict rule: Any metric with no threshold, or with null threshold, evaluates to FAIL.
    """
    loader = load_thresholds(thresholds_path, reload=True)
    results: Dict[str, Dict[str, Any]] = {}

    for metric_name, candidate_value in computed_metrics.items():
        # Find which section in thresholds defines this metric
        target_section: Optional[str] = None
        for section_name, section_dict in loader._raw_data.items():
            if isinstance(section_dict, dict) and metric_name in section_dict:
                target_section = section_name
                break

        if target_section is None:
            results[metric_name] = {
                "observed": candidate_value,
                "threshold": None,
                "status": "FAIL",
                "reason": "NO_THRESHOLD_DEFINED"
            }
            continue

        raw_threshold = loader.get(target_section, metric_name)

        if raw_threshold is None:
            results[metric_name] = {
                "observed": candidate_value,
                "threshold": None,
                "status": "FAIL",
                "reason": "THRESHOLD_NOT_SET"
            }
            continue

        # Evaluate comparison
        is_max_metric = any(sub in metric_name for sub in MAX_METRIC_SUBSTRINGS)
        comparator = "<=" if is_max_metric else ">="
        passed = loader.evaluate_gate(target_section, metric_name, candidate_value, comparator=comparator)

        results[metric_name] = {
            "observed": candidate_value,
            "threshold": raw_threshold,
            "status": "PASS" if passed else "FAIL",
            "reason": "SATISFIED" if passed else f"FAILED_THRESHOLD ({comparator} {raw_threshold})"
        }

    return results


def load_verified_cases(golden_dir: Path) -> List[GoldenCase]:
    """Load all verified golden cases from the specified release directory."""
    cases: List[GoldenCase] = []
    for f in sorted(golden_dir.glob("*.json")):
        if f.name == "manifest.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        case = GoldenCase(**data)
        if case.status == "verified":
            cases.append(case)
    return cases


def generate_markdown_report(report: EvaluationRunReport) -> str:
    """Format evaluation run report as structured Markdown table."""
    lines = [
        f"# AI-VH Evaluation Report: {report.run_id}",
        "",
        f"- **Golden Version:** {report.golden_version}",
        f"- **Pipeline:** {report.pipeline}",
        f"- **Cases Evaluated:** {report.cases_evaluated} of {report.total_cases}",
        f"- **Overall Gate Outcome:** **{report.overall_status}**",
        f"- **Timestamp:** {report.timestamp}",
        "",
        "## Metric Performance vs Governance Thresholds",
        "",
        "| Metric | Observed | Threshold | Gate Status | Detail |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for metric_name, mdata in sorted(report.metrics.items()):
        obs_str = f"{mdata['observed']:.4f}" if isinstance(mdata['observed'], float) else str(mdata['observed'])
        thresh_str = str(mdata['threshold']) if mdata['threshold'] is not None else "NOT SET"
        status_badge = f"**{mdata['status']}**"
        lines.append(f"| `{metric_name}` | {obs_str} | {thresh_str} | {status_badge} | {mdata['reason']} |")

    lines.append("")
    return "\n".join(lines)


def run_evaluation(
    golden_version: str = "v1",
    pipeline_name: str = "dummy",
    pipeline_instance: Optional[Pipeline] = None,
    scorer_instance: Optional[Scorer] = None,
    run_id: Optional[str] = None,
    golden_base_dir: Optional[str] = None,
    reports_dir: Optional[str] = None,
    thresholds_path: Optional[str] = None
) -> EvaluationRunReport:
    """
    Execute full evaluation suite:
    1. Validates frozen golden set manifest (raises if tampered).
    2. Runs pipeline on every verified case (passing strictly CaseView).
    3. Scores results via Scorer.
    4. Compares metrics against thresholds.yaml.
    5. Writes report.json and report.md.
    """
    start_time = time.perf_counter()
    effective_run_id = run_id or f"eval-{golden_version}-{pipeline_name}-{int(time.time())}"

    base_golden = Path(golden_base_dir) if golden_base_dir else (REPO_ROOT / "eval" / "golden")
    golden_dir = base_golden / golden_version

    if not golden_dir.exists():
        raise FileNotFoundError(f"Golden set release directory not found: {golden_dir}")

    # Step 1: Enforce frozen release integrity
    validate_manifest(golden_dir)

    # Step 2: Load verified cases
    golden_cases = load_verified_cases(golden_dir)
    if not golden_cases:
        raise ValueError(f"No verified cases found in golden set {golden_dir}")

    # Resolve pipeline
    if pipeline_instance is not None:
        pipeline = pipeline_instance
    elif pipeline_name == "dummy":
        pipeline = DummyPipeline()
    else:
        raise ValueError(f"Unknown pipeline: '{pipeline_name}'")

    # Resolve scorer
    scorer = scorer_instance or DummyScorer()

    # Step 3: Run pipeline passing strictly CaseView (isolation guarantee)
    results: List[Tuple[CaseView, PipelineResult]] = []
    for gcase in golden_cases:
        case_view = gcase.to_case_view()
        out = pipeline.run(case_view)
        results.append((case_view, out))

    # Step 4: Compute score metrics
    computed_metrics = scorer.score(results, golden_cases)

    # Step 5: Evaluate against governance thresholds
    metric_results = evaluate_metrics_against_thresholds(computed_metrics, thresholds_path=thresholds_path)

    all_passed = all(m["status"] == "PASS" for m in metric_results.values())
    overall_status = "PASS" if all_passed else "FAIL"

    duration = round(time.perf_counter() - start_time, 4)
    timestamp_str = datetime.now(timezone.utc).isoformat()

    report = EvaluationRunReport(
        run_id=effective_run_id,
        golden_version=golden_version,
        pipeline=pipeline_name,
        total_cases=len(golden_cases),
        cases_evaluated=len(results),
        overall_status=overall_status,
        metrics=metric_results,
        timestamp=timestamp_str,
        duration_seconds=duration
    )

    # Step 6: Write reports to disk
    base_reports = Path(reports_dir) if reports_dir else (REPO_ROOT / "eval" / "reports")
    out_dir = base_reports / effective_run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "report.json"
    json_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")

    md_path = out_dir / "report.md"
    md_path.write_text(generate_markdown_report(report), encoding="utf-8")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-VH Evaluation Harness Runner")
    parser.add_argument("--golden", default="v1", help="Golden set release version (e.g. v1)")
    parser.add_argument("--pipeline", default="dummy", help="Pipeline name to evaluate (default: dummy)")
    parser.add_argument("--run-id", default=None, help="Explicit evaluation run ID")
    args = parser.parse_args()

    try:
        report = run_evaluation(
            golden_version=args.golden,
            pipeline_name=args.pipeline,
            run_id=args.run_id
        )
        print(f"\nEvaluation Run Completed: {report.run_id}")
        print(f"Outcome: {report.overall_status} ({report.cases_evaluated} cases evaluated)")
        for mname, mdata in report.metrics.items():
            print(f"  - {mname}: observed={mdata['observed']} | threshold={mdata['threshold']} -> {mdata['status']}")
        return 0 if report.overall_status == "PASS" else 1
    except Exception as e:
        sys.stderr.write(f"Evaluation failed: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
