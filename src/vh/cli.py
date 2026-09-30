"""
Main CLI dispatcher for AI Virtual Hospital (AI-VH).
Routes subcommands:
  vh golden   : Golden case authoring, validation, export, and release
  vh synthea  : Synthea FHIR population generation and module runner
  vh cases    : Case builder, validation suite, and spot-check review export
"""

from pathlib import Path
import sys
from typing import List, Optional

# Ensure src and repo root are in sys.path when CLI is executed directly
SRC_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SRC_ROOT.parent
for p in [str(SRC_ROOT), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        print("AI Virtual Hospital (AI-VH) Master CLI")
        print("\nAvailable command suites:")
        print("  vh golden   : Golden case authoring, validation, export, and release")
        print("  vh synthea  : Synthea FHIR population generation and module runner")
        print("  vh cases    : Case builder, validation suite, and spot-check export")
        print("  vh verify   : Clinical verification rules, grounding, and calibration")
        print("  vh replay   : Deterministic encounter replay from recorded LLM outputs")
        print("  vh feedback : Doctor feedback snapshot export")
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
    elif command == "verify":
        from vh.verification.cli import main as verify_main
        return verify_main(sub_args)
    elif command == "replay":
        from vh.agents.cli import main as replay_main
        return replay_main(["replay"] + sub_args)
    elif command == "feedback":
        from vh.feedback.cli import main as feedback_main
        return feedback_main(sub_args)
    else:
        print(f"Unknown command suite: '{command}'. Available: golden, synthea, cases, verify, replay, feedback.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
