"""
Configuration loader for fault type classification in AI-VH.
Loads and validates the taxonomy of critical and non-critical faults.
"""

from pathlib import Path
from typing import Optional
import yaml

from .models import (
    FaultClassificationConfig,
    FaultClassificationInfo,
    FaultSeverity,
    FaultType,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "verification" / "fault_classification.yaml"


def load_fault_classification(
    config_path: Optional[Path] = None,
) -> FaultClassificationConfig:
    """
    Loads and validates fault classification taxonomy from YAML.
    """
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Fault classification config not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    meta = data.get("metadata", {})
    faults_dict = data.get("faults", {})

    classifications = {}
    for fault_key, info_dict in faults_dict.items():
        try:
            ft = FaultType(fault_key)
        except ValueError:
            continue

        severity_str = info_dict.get("severity", "non_critical")
        severity = FaultSeverity(severity_str)

        classifications[ft] = FaultClassificationInfo(
            severity=severity,
            category=info_dict.get("category", "general"),
            description=info_dict.get("description", ""),
            clinical_risk=info_dict.get("clinical_risk", ""),
        )

    return FaultClassificationConfig(
        config_id=meta.get("config_id", "FAULT-CONFIG-DEFAULT"),
        version=meta.get("version", "1.0.0"),
        description=meta.get("description", ""),
        classifications=classifications,
    )
