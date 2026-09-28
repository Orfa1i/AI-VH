"""
Golden set release builder and freezing utility for AI Virtual Hospital (AI-VH).
Packages verified golden cases into release directories and computes cryptographic manifests.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from eval.harness.manifest import generate_manifest
from vh.cases.schema import GoldenCase
from .validator import validate_case_dict


def build_release(
    source_dir: Path,
    target_dir: Path,
    version_tag: str = "v1"
) -> Dict[str, Any]:
    """
    Scan source_dir for golden cases, filter strictly for status: verified,
    copy to target_dir, and generate manifest.json.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    verified_cases = 0

    for file_path in sorted(source_dir.glob("*.json")):
        if file_path.name == "manifest.json":
            continue

        data = json.loads(file_path.read_text(encoding="utf-8"))
        case = validate_case_dict(data, allow_verified=True)

        # Strictly include only verified cases
        if case.status == "verified":
            dest_file = target_dir / file_path.name
            dest_file.write_text(json.dumps(case.model_dump(), indent=2), encoding="utf-8")
            verified_cases += 1

    if verified_cases == 0:
        raise ValueError(f"Cannot build release: No cases with status: verified found in {source_dir}")

    manifest = generate_manifest(target_dir, version_tag=version_tag)

    return {
        "release_version": version_tag,
        "cases_released": verified_cases,
        "target_directory": str(target_dir),
        "manifest": manifest
    }
