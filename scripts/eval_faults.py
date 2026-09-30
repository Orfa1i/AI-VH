"""
CLI and CI runner for the verification fault-injection suite in AI-VH.
Generates synthetic corrupted and clean cases, registers fault set as a versioned artifact,
scores the ClinicalVerificationRouter against verification.* thresholds, and enforces quality gates.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root and src to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from vh.common.artifacts import get_artifact_registry
from eval.faults import FaultGenerator, FaultInjectionScorer


def run_fault_evaluation(instances_per_fault: int = 25, register_artifact: bool = True) -> int:
    """
    Executes fault injection generation, artifact registration, and evaluation.
    Returns 0 if all thresholds pass, 1 if any threshold is violated.
    """
    print("================================================================================")
    print(" AI-VH Verification Fault-Injection Suite")
    print("================================================================================")
    print(f">> Generating fault set with {instances_per_fault} instances per fault type...")

    generator = FaultGenerator()
    fault_set = generator.generate_fault_set(instances_per_fault=instances_per_fault)

    print(f">> Generated {len(fault_set.clean_cases)} clean cases and {len(fault_set.corrupted_cases)} corrupted cases.")

    if register_artifact:
        registry = get_artifact_registry()
        record = generator.register_as_artifact(fault_set=fault_set, registry=registry)
        print(f">> Registered fault set artifact: id={record.id}, version={record.version}, sha256={record.sha256[:12]}")

    print("\n>> Executing verification evaluation across all cases...")
    scorer = FaultInjectionScorer()
    report = scorer.evaluate(fault_set)

    print("\n--------------------------------------------------------------------------------")
    print(" Detection Results by Fault Type:")
    print("--------------------------------------------------------------------------------")
    for ft_name, stats in report.detection_by_fault_type.items():
        rate_pct = stats["rate"] * 100.0
        print(f" - {ft_name:<30} [{stats['severity']:<12}]: {stats['detected']}/{stats['total']} ({rate_pct:6.2f}%)")

    print("\n--------------------------------------------------------------------------------")
    print(" Threshold Comparison:")
    print("--------------------------------------------------------------------------------")
    crit_thresh = report.thresholds["critical_fault_detection"]
    noncrit_thresh = report.thresholds["noncritical_fault_detection"]
    false_max = report.thresholds["false_flag_rate_max"]

    crit_pct = report.critical_detection_rate * 100.0
    noncrit_pct = report.noncritical_detection_rate * 100.0
    false_pct = report.false_flag_rate * 100.0

    crit_status = "PASS" if report.critical_detection_rate >= crit_thresh else "FAIL"
    noncrit_status = "PASS" if report.noncritical_detection_rate >= noncrit_thresh else "FAIL"
    false_status = "PASS" if report.false_flag_rate <= false_max else "FAIL"

    print(f" Critical Fault Detection:    {crit_pct:6.2f}% (required >= {crit_thresh * 100:.1f}%) -> [{crit_status}]")
    print(f" Non-Critical Detection:      {noncrit_pct:6.2f}% (required >= {noncrit_thresh * 100:.1f}%) -> [{noncrit_status}]")
    print(f" Clean Case False-Flag Rate:  {false_pct:6.2f}% (required <= {false_max * 100:.1f}%) -> [{false_status}]")
    print("--------------------------------------------------------------------------------")

    if report.passed:
        print("\n>> VERDICT: ALL VERIFICATION FAULT GATES PASSED")
        return 0
    else:
        print("\n>> VERDICT: GATE FAILED: Verification thresholds not met.")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run AI-VH Fault-Injection Evaluation Suite")
    parser.add_argument(
        "--instances-per-fault",
        type=int,
        default=25,
        help="Number of test instances generated per fault type (minimum 20)",
    )
    parser.add_argument(
        "--no-artifact",
        action="store_true",
        help="Skip registering the fault set into the artifact registry",
    )
    args = parser.parse_args()

    exit_code = run_fault_evaluation(
        instances_per_fault=args.instances_per_fault,
        register_artifact=not args.no_artifact,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
