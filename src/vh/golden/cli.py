"""
Golden Case authoring, validation, review packet export, sign-off import, and release CLI.
Usage:
    python -m vh.golden.cli new --case-id <id> --specialty <spec> --output <path>
    python -m vh.golden.cli validate --path <file_or_dir>
    python -m vh.golden.cli export --drafts-dir <dir> --output-md <path> [--output-pdf <path>]
    python -m vh.golden.cli import-signoff --signoff <path> --drafts-dir <dir>
    python -m vh.golden.cli release --drafts-dir <dir> --target-dir <dir> --version <vN>
"""

import argparse
import json
import sys
from pathlib import Path

from vh.cases.schema import CaseView, GoldenCase, GroundTruth, SupportingReference
from .exporter import export_reviewer_packet
from .importer import import_signoff
from .releaser import build_release
from .validator import validate_case_dict


def cmd_new(args: argparse.Namespace) -> int:
    """Create a new skeleton draft case."""
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)

    skeleton = GoldenCase(
        case_id=args.case_id,
        specialty=args.specialty,
        patient_ref=f"PAT-{args.case_id}",
        visible_presentation={
            "chief_complaint": "Enter chief complaint here",
            "history": "Enter clinical history here",
            "vitals": {"bp": "120/80", "hr": 72, "rr": 16, "spo2": 99, "temp": 37.0},
            "exam": "Enter physical examination findings here"
        },
        hidden_results=[
            {"order": "Enter lab/imaging test name", "result": "Enter test result value"}
        ],
        ground_truth=GroundTruth(
            primary_dx="Enter primary diagnosis",
            acceptable_differential=["Enter acceptable alternative differential 1"],
            expected_workup=["Enter required diagnostic order 1"],
            red_flags=["Enter emergency warning sign 1"]
        ),
        supporting_references=[
            SupportingReference(
                source="Harrison's Principles of Internal Medicine",
                locator="Chapter Number",
                note="Clinical guideline summary"
            )
        ],
        status="draft",
        version="1.0.0"
    )

    dest.write_text(json.dumps(skeleton.model_dump(), indent=2), encoding="utf-8")
    print(f"Created new draft golden case template: {dest}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a single case file or a directory of cases."""
    target = Path(args.path)
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("*.json"))
        files = [f for f in files if f.name != "manifest.json"]
    else:
        print(f"Error: Target path '{target}' not found.")
        return 1

    errors = 0
    validated = 0
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            validate_case_dict(data, allow_verified=args.allow_verified)
            validated += 1
        except Exception as e:
            print(f"Validation failure in {f.name}: {e}")
            errors += 1

    print(f"Validation finished: {validated} passed, {errors} failed.")
    return 0 if errors == 0 else 1


def cmd_export(args: argparse.Namespace) -> int:
    """Export draft cases to markdown and PDF reviewer packet."""
    drafts_dir = Path(args.drafts_dir)
    output_md = Path(args.output_md)
    output_pdf = Path(args.output_pdf) if args.output_pdf else None

    res = export_reviewer_packet(drafts_dir, output_md, output_pdf)
    print(f"Exported {res['cases_exported']} cases to:")
    print(f"  Markdown: {res['markdown_packet']}")
    if res["pdf_packet"]:
        print(f"  PDF:      {res['pdf_packet']}")
    return 0


def cmd_import_signoff(args: argparse.Namespace) -> int:
    """Import signed-off case approvals from markdown signoff file."""
    signoff_path = Path(args.signoff)
    drafts_dir = Path(args.drafts_dir)

    res = import_signoff(signoff_path, drafts_dir)
    print("Sign-off Import Completed:")
    print(f"  Sign-off file: {res['signoff_file']}")
    print(f"  Reviewer:      {res['reviewer']}")
    print(f"  Date:          {res['reviewed_at']}")
    print(f"  Approved found:{res['approved_cases_found']}")
    print(f"  Promoted cases:{res['promoted_cases_count']}")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    """Package verified cases into release directory with cryptographic manifest."""
    drafts_dir = Path(args.drafts_dir)
    target_dir = Path(args.target_dir)

    res = build_release(drafts_dir, target_dir, version_tag=args.version)
    print("Golden Set Release Built:")
    print(f"  Version:   {res['release_version']}")
    print(f"  Cases:     {res['cases_released']}")
    print(f"  Directory: {res['target_directory']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-VH Golden Set Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # new
    p_new = subparsers.add_parser("new", help="Create new draft case skeleton")
    p_new.add_argument("--case-id", required=True, help="Unique case identifier")
    p_new.add_argument("--specialty", required=True, help="Clinical specialty (e.g. Cardiology)")
    p_new.add_argument("--output", required=True, help="Destination JSON file path")
    p_new.set_defaults(func=cmd_new)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate case files against schema and rules")
    p_val.add_argument("--path", required=True, help="Path to JSON file or directory")
    p_val.add_argument("--allow-verified", action="store_true", help="Allow status: verified without sign-off")
    p_val.set_defaults(func=cmd_validate)

    # export
    p_exp = subparsers.add_parser("export", help="Render reviewer packet in Markdown and PDF")
    p_exp.add_argument("--drafts-dir", default="eval/golden/drafts", help="Path to draft cases directory")
    p_exp.add_argument("--output-md", default="docs/signoffs/golden-v1-packet.md", help="Output markdown packet path")
    p_exp.add_argument("--output-pdf", default="docs/signoffs/golden-v1-packet.pdf", help="Output PDF packet path")
    p_exp.set_defaults(func=cmd_export)

    # import-signoff
    p_imp = subparsers.add_parser("import-signoff", help="Import physician sign-off approvals")
    p_imp.add_argument("--signoff", required=True, help="Path to signed markdown file")
    p_imp.add_argument("--drafts-dir", default="eval/golden/drafts", help="Path to draft cases directory")
    p_imp.set_defaults(func=cmd_import_signoff)

    # release
    p_rel = subparsers.add_parser("release", help="Build frozen release from verified cases")
    p_rel.add_argument("--drafts-dir", default="eval/golden/drafts", help="Source directory with verified cases")
    p_rel.add_argument("--target-dir", default="eval/golden/v1", help="Target release directory")
    p_rel.add_argument("--version", default="v1", help="Release version tag (e.g. v1)")
    p_rel.set_defaults(func=cmd_release)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
