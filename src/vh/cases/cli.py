"""
Command-line interface for AI-VH clinical case validation and spot-check review export.
Usage:
  vh cases spotcheck --n 50 [--seed 42] [--output PATH]
  vh cases validate [--batch-size 500] [--seed 1337] [--report PATH]
"""

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from .builder import CaseBuilder, CaseBuilderConfig
from .validation import BatchCaseValidator, generate_spotcheck_packet

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def run_spotcheck(
    sample_size: int = 50,
    seed: int = 42,
    output_path: Optional[Path] = None,
) -> int:
    """Generate and export a physician spot-check packet."""
    print(f"\n[AI-VH Case Builder] Generating {sample_size}-case spot-check review packet (seed: {seed})...")
    builder = CaseBuilder(config=CaseBuilderConfig(batch_size=sample_size * 2, seed=seed))
    cases = builder.build_batch(count=sample_size * 2, seed=seed)

    target_file = output_path or (REPO_ROOT / "docs" / "signoffs" / "phase-1-spotcheck-packet.md")
    result = generate_spotcheck_packet(
        cases=cases,
        sample_size=sample_size,
        seed=seed,
        output_file=target_file,
    )
    print(f"[AI-VH Case Builder] Successfully generated spot-check packet with {result['cases_sampled']} cases.")
    print(f"[AI-VH Case Builder] Output file: {result['packet_path']}")
    return 0


def run_validate(
    batch_size: int = 500,
    seed: int = 1337,
    report_path: Optional[Path] = None,
) -> int:
    """Validate a batch of clinical cases against plausibility rules and thresholds."""
    print(f"\n[AI-VH Case Validator] Validating {batch_size}-case cohort across all plausibility rules (seed: {seed})...")
    builder = CaseBuilder(config=CaseBuilderConfig(batch_size=batch_size, seed=seed))
    cases = builder.build_batch(count=batch_size, seed=seed)

    target_report = report_path or (REPO_ROOT / "eval" / "reports" / "cases_validation_report.json")
    batch_validator = BatchCaseValidator()
    report = batch_validator.validate_batch(cases, report_path=target_report)

    pass_rate = report.get("plausibility_pass_rate", 0.0)
    leakage = report.get("leakage_count", 0)

    print(f"[AI-VH Case Validator] Evaluated: {report['total_cases']} cases")
    print(f"[AI-VH Case Validator] Plausibility Pass Rate: {pass_rate * 100:.2f}%")
    print(f"[AI-VH Case Validator] Diagnostic Leakage Count: {leakage}")
    print(f"[AI-VH Case Validator] Report saved to: {target_report}")

    if pass_rate == 1.0 and leakage == 0:
        print("[AI-VH Case Validator] ALL CASES SATISFY GOVERNANCE THRESHOLDS (100% PASS).")
        return 0
    else:
        print("[AI-VH Case Validator] VALIDATION DEFECTS DETECTED.")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vh cases",
        description="AI-VH Clinical Cases Management and Validation CLI"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Cases subcommands")

    # spotcheck subcommand
    spotcheck_parser = subparsers.add_parser("spotcheck", help="Generate physician spot-check review packet")
    spotcheck_parser.add_argument("--n", type=int, default=50, help="Number of cases to sample (default: 50)")
    spotcheck_parser.add_argument("--seed", type=int, default=42, help="Random sampling seed (default: 42)")
    spotcheck_parser.add_argument("--output", type=str, default=None, help="Output markdown packet path")

    # validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate case batch against plausibility rules")
    validate_parser.add_argument("--batch-size", type=int, default=500, help="Number of cases to validate (default: 500)")
    validate_parser.add_argument("--seed", type=int, default=1337, help="Random generation seed (default: 1337)")
    validate_parser.add_argument("--report", type=str, default=None, help="Output validation report JSON path")

    args = parser.parse_args(argv)

    if args.subcommand == "spotcheck":
        out = Path(args.output) if args.output else None
        return run_spotcheck(sample_size=args.n, seed=args.seed, output_path=out)
    elif args.subcommand == "validate":
        rep = Path(args.report) if args.report else None
        return run_validate(batch_size=args.batch_size, seed=args.seed, report_path=rep)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
