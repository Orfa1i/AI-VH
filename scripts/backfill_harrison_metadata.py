"""
Phase 1 Harrison metadata backfill (JSON only, never .npy).

- Verifies a backup_phase1_* directory exists under data/knowledge before change.
- Refuses to touch any .npy embedding file (hash + mtime verified unchanged).
- Enriches harrison_full_collection.json (+ 20-item harrison_chunks.json and
  internal_medicine_collection.json) in place: adds nullable edition,
  chapter_number, chapter_title, section_heading. Preserves id order + text.
  Unknown values become null; page numbers are never guessed.

Usage:
    py -3.13 scripts/backfill_harrison_metadata.py [--apply] [--backup-dir NAME]

Default is --apply (required for Phase 1). Run once, then report counts.

Owner: Software Engineer.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vh.rag.sources.harrison import enrich_harrison_metadata  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "data" / "knowledge"
TARGETS = [
    "harrison_full_collection.json",
    "harrison_chunks.json",
    "internal_medicine_collection.json",
]
NPY_FILES = [
    "harrison_embeddings.npy",
    "braunwald_embeddings.npy",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 Harrison JSON metadata backfill")
    parser.add_argument("--backup-dir", type=str, default=None)
    args = parser.parse_args()

    backups = sorted(KNOWLEDGE_DIR.glob("backup_phase1_*"))
    if args.backup_dir:
        backup = KNOWLEDGE_DIR / args.backup_dir
    elif backups:
        backup = backups[-1]
    else:
        print("ERROR: no data/knowledge/backup_phase1_* directory found. Take a full backup first.")
        return 2
    print(f"Using backup: {backup}")
    for name in TARGETS:
        src = KNOWLEDGE_DIR / name
        bkp = backup / name
        if src.exists() and not bkp.exists():
            print(f"ERROR: backup missing {name} in {backup}. Aborting.")
            return 2

    npy_hashes = {}
    for name in NPY_FILES:
        p = KNOWLEDGE_DIR / name
        if p.exists():
            npy_hashes[name] = (sha256_file(p), p.stat().st_mtime)

    total_full = 0
    total_partial = 0
    total_null_page = 0
    total = 0

    for name in TARGETS:
        path = KNOWLEDGE_DIR / name
        if not path.exists():
            print(f"Skipping missing {name}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"Skipping {name}: not a list")
            continue

        changed = 0
        for entry in data:
            if not isinstance(entry, dict):
                continue
            meta = enrich_harrison_metadata(entry)
            # Always write the four nullable fields explicitly (null when unknown);
            # never alter id/text/page values.
            for key in ("edition", "chapter_number", "chapter_title", "section_heading"):
                if entry.get(key) != meta[key]:
                    entry[key] = meta[key]
                    changed += 1
                elif key not in entry:
                    entry[key] = meta[key]
                    changed += 1
            total += 1
            has_edition = meta["edition"] is not None
            has_chapter = meta["chapter_title"] is not None
            has_page = meta["page"] is not None
            if has_edition and has_chapter and has_page:
                total_full += 1
            else:
                total_partial += 1
            if not has_page:
                total_null_page += 1

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Backfilled {name}: {len(data)} entries, {changed} new field values.")

    for name, (before_hash, before_mtime) in npy_hashes.items():
        p = KNOWLEDGE_DIR / name
        after_hash = sha256_file(p)
        after_mtime = p.stat().st_mtime
        status = "UNCHANGED" if (after_hash == before_hash and after_mtime == before_mtime) else "MODIFIED!"
        print(f".npy check {name}: {status}")
        if after_hash != before_hash:
            print(f"ERROR: {name} hash changed. Restore from backup immediately.")
            return 3

    print(f"CENSUS total={total} full={total_full} partial={total_partial} null_page={total_null_page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
