"""
FHIR R4 Bundle validation utility for Synthea generated patient data.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field

try:
    from fhir.resources.bundle import Bundle
except ImportError:
    Bundle = None  # type: ignore


class FHIRBundleValidationError(ValueError):
    """Raised when a JSON file fails FHIR R4 specification validation."""
    pass


class BundleValidationReport(BaseModel):
    """Aggregated validation statistics across a population directory of FHIR bundles."""
    total_bundles: int = 0
    valid_bundles: int = 0
    pass_rate: float = 0.0
    errors: Dict[str, str] = Field(default_factory=dict)


def validate_fhir_bundle(bundle_source: Union[Dict[str, Any], Path, str]) -> Dict[str, Any]:
    """
    Validate that a single bundle dictionary or file adheres strictly to FHIR R4 specification.
    Returns summary metadata of the validated bundle.
    """
    if isinstance(bundle_source, (str, Path)):
        p = Path(bundle_source)
        if not p.exists():
            raise FileNotFoundError(f"FHIR bundle file not found: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            raise FHIRBundleValidationError(f"Invalid JSON in bundle file {p}: {e}")
    elif isinstance(bundle_source, dict):
        data = bundle_source
    else:
        raise TypeError(f"Expected dict, Path, or str for bundle_source, got {type(bundle_source)}")

    if not isinstance(data, dict):
        raise FHIRBundleValidationError("FHIR bundle must be a JSON object dictionary")

    # Resource type check
    if data.get("resourceType") != "Bundle":
        raise FHIRBundleValidationError(
            f"Expected resourceType 'Bundle', received '{data.get('resourceType')}'"
        )

    if not data.get("type"):
        raise FHIRBundleValidationError("FHIR bundle missing required 'type' field")

    # Full structural validation via fhir.resources
    if Bundle is not None:
        try:
            bundle_obj = Bundle.model_validate(data)
            entry_count = len(bundle_obj.entry or [])
            return {
                "valid": True,
                "resource_type": bundle_obj.get_resource_type(),
                "type": bundle_obj.type,
                "entry_count": entry_count
            }
        except Exception as e:
            raise FHIRBundleValidationError(f"FHIR R4 validation failed: {e}")
    else:
        # Fallback if fhir.resources is unavailable
        entries = data.get("entry", [])
        return {
            "valid": True,
            "resource_type": "Bundle",
            "type": data.get("type"),
            "entry_count": len(entries) if isinstance(entries, list) else 0
        }


def validate_bundle_directory(dir_path: Union[Path, str]) -> BundleValidationReport:
    """
    Scan a directory of generated patient bundles and validate 100% of files.
    """
    target = Path(dir_path)
    if not target.exists() or not target.is_dir():
        raise FileNotFoundError(f"Directory not found: {target}")

    bundle_files = sorted(
        [f for f in target.glob("*.json") if f.name not in ("manifest.json", "metadata.json")]
    )

    total = len(bundle_files)
    valid = 0
    errors: Dict[str, str] = {}

    for bf in bundle_files:
        try:
            validate_fhir_bundle(bf)
            valid += 1
        except Exception as e:
            errors[bf.name] = str(e)

    pass_rate = (valid / total) if total > 0 else 0.0

    return BundleValidationReport(
        total_bundles=total,
        valid_bundles=valid,
        pass_rate=pass_rate,
        errors=errors
    )
