"""
`vh feedback` command suite for AI-VH (STEP 39 / P6.4).
Usage:
    vh feedback snapshot --db <path> --output <dir> --version <vN>
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
for _p in (str(SRC_ROOT), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def cmd_snapshot(args: argparse.Namespace) -> int:
    from vh.feedback.models import FeedbackStore
    from vh.feedback.snapshot import build_snapshot

    store = FeedbackStore(db_path=args.db)
    try:
        result = build_snapshot(
            store,
            output_dir=args.output,
            version=args.version,
            registry_db=args.registry_db,
        )
    finally:
        store.close()
    print(f"Feedback snapshot {result['version']} written to {result['output_dir']}")
    print(f"Dataset sha256: {result['dataset_sha256']}")
    print(f"Counts: {result['counts']}")
    if result["artifact_id"]:
        print(f"Artifact: {result['artifact_id']}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AI-VH doctor feedback commands")
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot", help="Export a versioned feedback dataset snapshot")
    snap.add_argument("--db", required=True, help="Feedback SQLite database path")
    snap.add_argument("--output", required=True, help="Snapshot output directory")
    snap.add_argument("--version", required=True, help="Snapshot version label")
    snap.add_argument("--registry-db", default=None, help="Artifact registry database path")
    args = parser.parse_args(argv)

    if args.command == "snapshot":
        return cmd_snapshot(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
