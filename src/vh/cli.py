"""
Main CLI dispatcher for AI Virtual Hospital (AI-VH).
Routes subcommands:
  vh golden   : Golden case authoring, validation, export, and release
  vh synthea  : Synthea FHIR population generation and module runner
  vh cases    : Case builder, validation suite, and spot-check review export
"""

import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        print("AI Virtual Hospital (AI-VH) Master CLI")
        print("\nAvailable command suites:")
        print("  vh golden   : Golden case authoring, validation, export, and release")
        print("  vh synthea  : Synthea FHIR population generation and module runner")
        print("  vh cases    : Case builder, validation suite, and spot-check export")
        return 0

    command = argv[0].lower()
    sub_args = argv[1:]

    if command == "golden":
        from vh.golden.cli import main as golden_main
        return golden_main(sub_args)
    elif command == "synthea":
        from vh.synthea.cli import main as synthea_main
        return synthea_main(sub_args)
    elif command == "cases":
        from vh.cases.cli import main as cases_main
        return cases_main(sub_args)
    else:
        print(f"Unknown command suite: '{command}'. Available: golden, synthea, cases.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
