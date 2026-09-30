"""
Agent encounter replay CLI for AI-VH (STEP 34 / P5.4).
Usage:
    vh replay <run_id> [--replays-dir DIR] [--golden-dir DIR]
Re-executes the recorded encounter deterministically from its LLM transcript
and compares the canonical event-log hash.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
for _p in (str(SRC_ROOT), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _find_case_file(case_id: str, golden_dir: Path) -> Optional[Path]:
    for path in sorted(golden_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("case_id") == case_id:
            return path
    return None


def cmd_replay(args: argparse.Namespace) -> int:
    from vh.agents.replay import REPLAY_DIR, hash_event_log, load_bundle, replay_encounter
    from vh.cases.schema import GoldenCase
    from vh.cases.spec import CaseSpec

    replays_dir = Path(args.replays_dir) if args.replays_dir else REPLAY_DIR
    golden_dir = Path(args.golden_dir) if args.golden_dir else (REPO_ROOT / "eval" / "golden" / "v1")

    try:
        bundle = load_bundle(args.run_id, directory=replays_dir)
    except FileNotFoundError as exc:
        print(f"Replay bundle not found for run_id '{args.run_id}': {exc}")
        return 1

    case_file = _find_case_file(bundle.case_id, golden_dir)
    if case_file is None:
        print(f"Golden case '{bundle.case_id}' not found in {golden_dir}.")
        return 1

    golden = GoldenCase.model_validate(json.loads(case_file.read_text(encoding="utf-8")))
    case_spec = CaseSpec.from_golden_case(golden)

    state, replayed_hash = replay_encounter(bundle, case_spec=case_spec)
    expected_hash = bundle.event_log_hash
    # Recompute from stored log to guard against tampering.
    stored_hash = hash_event_log(bundle.event_log)

    print(f"Run: {bundle.run_id} | Case: {bundle.case_id} | Seed: {bundle.seed}")
    print(f"Expected event-log hash: {expected_hash}")
    print(f"Stored-log hash:          {stored_hash}")
    print(f"Replayed event-log hash:  {replayed_hash}")
    print(f"Encounter status: {state.status} | Steps: {state.step_count}")

    if replayed_hash == expected_hash == stored_hash:
        print("REPLAY RESULT: MATCH -- deterministic replay reproduced the event log exactly.")
        return 0
    print("REPLAY RESULT: MISMATCH -- replayed event log differs from the recording.")
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AI-VH agent encounter replay CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    replay_p = sub.add_parser("replay", help="Re-execute a recorded encounter run")
    replay_p.add_argument("run_id", help="Recorded run identifier")
    replay_p.add_argument("--replays-dir", default=None, help="Replay bundle directory")
    replay_p.add_argument("--golden-dir", default=None, help="Golden set directory")
    args = parser.parse_args(argv)

    if args.command == "replay":
        return cmd_replay(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
