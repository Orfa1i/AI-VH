"""
CLI for AI-VH Synthea patient generator, bundle validation, and deterministic reproduction.
Usage:
    python -m vh.synthea.cli generate --seed 42 --population 10 --output-dir data/synthea/run_1
    python -m vh.synthea.cli validate --path data/synthea/run_1
    python -m vh.synthea.cli reproduce --artifact-id <artifact_id> --output-dir data/synthea/reproduced
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import SyntheaGenerationConfig
from .runner import SyntheaRunner
from .validator import validate_bundle_directory, validate_fhir_bundle


def cmd_generate(args: argparse.Namespace) -> int:
    """Run deterministic Synthea generation according to command arguments."""
    modules_list = args.modules.split(",") if args.modules else None

    config = SyntheaGenerationConfig(
        seed=args.seed,
        clinician_seed=args.clinician_seed,
        reference_date=args.reference_date,
        population=args.population,
        state=args.state,
        city=args.city,
        gender=args.gender,
        modules=modules_list,
        synthea_version=args.version
    )

    out_dir = Path(args.output_dir) if args.output_dir else None
    base_dir = out_dir.parent if out_dir else None
    sub_dir = out_dir.name if out_dir else None

    runner = SyntheaRunner(base_output_dir=base_dir)
    res = runner.generate(config, output_subdir=sub_dir)

    print(f"Synthea Generation Completed:")
    print(f"  Output Directory: {res.output_dir}")
    print(f"  Bundles Generated:{res.bundle_count}")
    print(f"  Output Hash:      {res.output_hash}")
    print(f"  Artifact ID:      {res.artifact_id}")
    print(f"  Validation Rate:  {res.validation_report.pass_rate * 100:.1f}%")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a single FHIR bundle or an entire directory of bundles."""
    target = Path(args.path)
    if not target.exists():
        print(f"Error: Target path does not exist: {target}", file=sys.stderr)
        return 1

    if target.is_file():
        try:
            res = validate_fhir_bundle(target)
            print(f"Bundle Validated: {target.name}")
            print(f"  Resource Type: {res['resource_type']}")
            print(f"  Entries:       {res['entry_count']}")
            return 0
        except Exception as e:
            print(f"Validation Error: {e}", file=sys.stderr)
            return 1
    else:
        report = validate_bundle_directory(target)
        print(f"Directory Validation Completed:")
        print(f"  Total Bundles: {report.total_bundles}")
        print(f"  Valid Bundles: {report.valid_bundles}")
        print(f"  Pass Rate:     {report.pass_rate * 100:.1f}%")
        if report.errors:
            print("Errors:")
            for fn, err in report.errors.items():
                print(f"  - {fn}: {err}")
            return 1
        return 0


def cmd_reproduce(args: argparse.Namespace) -> int:
    """Reproduce synthetic population strictly from registered artifact metadata."""
    runner = SyntheaRunner(base_output_dir=Path(args.output_dir).parent if args.output_dir else None)
    sub_dir = Path(args.output_dir).name if args.output_dir else None
    res = runner.reproduce_from_artifact(args.artifact_id, reproduction_subdir=sub_dir)

    print(f"Population Reproduced Successfully:")
    print(f"  Output Directory: {res.output_dir}")
    print(f"  Bundles Count:    {res.bundle_count}")
    print(f"  Output Hash:      {res.output_hash}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AI-VH Synthea Patient Generator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic FHIR patient bundles")
    p_gen.add_argument("--seed", type=int, default=42, help="Random seed for patient demographics")
    p_gen.add_argument("--clinician-seed", type=int, default=101, help="Random seed for clinician IDs")
    p_gen.add_argument("--reference-date", default="2026-01-01", help="Reference date YYYY-MM-DD")
    p_gen.add_argument("--population", type=int, default=1, help="Number of patients to generate")
    p_gen.add_argument("--state", default="Massachusetts", help="US State")
    p_gen.add_argument("--city", default=None, help="City within state")
    p_gen.add_argument("--gender", default=None, help="Gender filter (M/F)")
    p_gen.add_argument("--modules", default=None, help="Comma-separated list of modules")
    p_gen.add_argument("--version", default="v3.3.0", help="Pinned Synthea version")
    p_gen.add_argument("--output-dir", default=None, help="Destination directory for bundles")
    p_gen.set_defaults(func=cmd_generate)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate FHIR R4 bundles")
    p_val.add_argument("--path", required=True, help="Path to bundle JSON file or directory")
    p_val.set_defaults(func=cmd_validate)

    # reproduce
    p_rep = subparsers.add_parser("reproduce", help="Reproduce generation from artifact metadata")
    p_rep.add_argument("--artifact-id", required=True, help="Registered artifact ID")
    p_rep.add_argument("--output-dir", default=None, help="Target reproduction directory")
    p_rep.set_defaults(func=cmd_reproduce)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
