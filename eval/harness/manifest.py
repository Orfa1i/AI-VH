"""
Golden set manifest generator and cryptographic integrity validator.
Enforces frozen release guarantees for AI-VH benchmark sets.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class GoldenSetIntegrityError(ValueError):
    """Raised when a frozen golden set file has been modified, tampered with, or corrupted."""
    pass


def calculate_file_sha256(file_path: Path) -> str:
    """Compute standard SHA-256 hash for a file."""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def generate_manifest(golden_dir: Path, version_tag: str = "v1") -> Dict[str, Any]:
    """Generate and write manifest.json containing cryptographic hashes for all cases in golden_dir."""
    files_map: Dict[str, str] = {}
    for file_path in sorted(golden_dir.glob("*.json")):
        if file_path.name == "manifest.json":
            continue
        files_map[file_path.name] = calculate_file_sha256(file_path)

    manifest_data = {
        "version": version_tag,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(files_map),
        "files": files_map
    }

    manifest_file = golden_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    return manifest_data


def validate_manifest(golden_dir: Path) -> None:
    """
    Validate that all files in a frozen golden set match their recorded SHA-256 hashes exactly.
    Raises GoldenSetIntegrityError if any file is missing, altered, or extra files are found.
    """
    manifest_file = golden_dir / "manifest.json"
    if not manifest_file.exists():
        raise GoldenSetIntegrityError(f"Missing manifest.json in frozen golden set directory: {golden_dir}")

    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise GoldenSetIntegrityError(f"Corrupt manifest.json in {golden_dir}: {e}")

    recorded_files = manifest.get("files", {})
    if not isinstance(recorded_files, dict) or not recorded_files:
        raise GoldenSetIntegrityError(f"Invalid or empty files map in manifest.json at {golden_dir}")

    # Check that each tracked file exists and has matching sha256
    for filename, expected_hash in recorded_files.items():
        file_path = golden_dir / filename
        if not file_path.exists():
            raise GoldenSetIntegrityError(
                f"Golden set integrity mismatch: Tracked file '{filename}' is missing in {golden_dir}"
            )
        actual_hash = calculate_file_sha256(file_path)
        if actual_hash != expected_hash:
            raise GoldenSetIntegrityError(
                f"Golden set integrity mismatch in '{filename}': expected sha256 {expected_hash}, got {actual_hash}. "
                "Frozen golden releases are immutable; changes require a new release version."
            )

    # Check for untracked JSON files
    actual_files = {p.name for p in golden_dir.glob("*.json") if p.name != "manifest.json"}
    untracked = actual_files - set(recorded_files.keys())
    if untracked:
        raise GoldenSetIntegrityError(
            f"Golden set integrity mismatch: Found untracked files in frozen release {golden_dir}: {sorted(untracked)}"
        )
