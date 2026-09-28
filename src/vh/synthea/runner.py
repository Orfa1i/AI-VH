"""
Synthea runner orchestration: execution, bundle validation, output hashing, and artifact registry tracking.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from vh.common.artifacts import ArtifactKind, ArtifactRegistry
from .config import SyntheaGenerationConfig
from .generator import generate_deterministic_population
from .validator import BundleValidationReport, validate_bundle_directory

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class SyntheaRunResult(BaseModel):
    """Result of a Synthea population generation run."""
    output_dir: Path
    config: SyntheaGenerationConfig
    bundle_count: int
    output_hash: str
    bundle_hashes: Dict[str, str] = Field(default_factory=dict)
    artifact_id: Optional[str] = None
    validation_report: BundleValidationReport


class SyntheaRunner:
    """
    Orchestrates reproducible Synthea FHIR generation, bundle validation,
    cryptographic output hashing, and dataset artifact registration.
    """

    def __init__(
        self,
        base_output_dir: Optional[Union[Path, str]] = None,
        registry: Optional[ArtifactRegistry] = None
    ):
        self.base_output_dir = Path(base_output_dir) if base_output_dir else (REPO_ROOT / "data" / "synthea")
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry or ArtifactRegistry()

    def generate(
        self,
        config: SyntheaGenerationConfig,
        output_subdir: Optional[str] = None
    ) -> SyntheaRunResult:
        """
        Generate FHIR R4 bundles according to configuration, validate 100% of bundles,
        compute deterministic output hash, and record dataset artifact in registry.
        """
        sub_name = output_subdir or f"run_{config.seed}_{config.clinician_seed}_p{config.population}"
        target_dir = self.base_output_dir / sub_name

        # Clean destination directory if it already exists
        if target_dir.exists():
            for f in target_dir.glob("*.json"):
                f.unlink()
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate bundles
        bundle_files = generate_deterministic_population(config, target_dir)

        # Validate 100% of generated bundles
        val_report = validate_bundle_directory(target_dir)
        if val_report.pass_rate < 1.0 or val_report.valid_bundles != len(bundle_files):
            err_details = "; ".join(f"{k}: {v}" for k, v in val_report.errors.items())
            raise ValueError(f"Synthea bundle validation failed ({val_report.valid_bundles}/{val_report.total_bundles}): {err_details}")

        # Compute per-bundle and aggregate SHA-256 hashes
        bundle_hashes: Dict[str, str] = {}
        hasher = hashlib.sha256()

        for bf in sorted(bundle_files, key=lambda p: p.name):
            content_bytes = bf.read_bytes()
            b_hash = hashlib.sha256(content_bytes).hexdigest()
            bundle_hashes[bf.name] = b_hash
            hasher.update(content_bytes)

        combined_hash = hasher.hexdigest()

        # Register dataset artifact in registry
        artifact_manifest = {
            "config": config.model_dump(),
            "output_hash": combined_hash,
            "bundle_count": len(bundle_files),
            "files": bundle_hashes,
        }
        manifest_bytes = json.dumps(artifact_manifest, indent=2, sort_keys=True).encode("utf-8")

        artifact_name = f"synthea_{config.state.lower().replace(' ', '_')}"
        artifact_version = f"{config.synthea_version}-s{config.seed}-p{config.population}"

        record = self.registry.register_artifact(
            kind=ArtifactKind.DATASET,
            name=artifact_name,
            version=artifact_version,
            content=manifest_bytes,
            metadata=config.model_dump()
        )

        return SyntheaRunResult(
            output_dir=target_dir,
            config=config,
            bundle_count=len(bundle_files),
            output_hash=combined_hash,
            bundle_hashes=bundle_hashes,
            artifact_id=record.id,
            validation_report=val_report
        )

    def reproduce_from_artifact(
        self,
        artifact_id: str,
        reproduction_subdir: Optional[str] = None
    ) -> SyntheaRunResult:
        """
        Reconstruct exact patient generation solely from registered artifact metadata.
        """
        record = self.registry.load_artifact_by_id(artifact_id)
        if not record:
            raise KeyError(f"Artifact ID not found in registry: {artifact_id}")

        config_data = record.metadata
        if not config_data:
            raise ValueError(f"Artifact {artifact_id} contains no configuration metadata")

        config = SyntheaGenerationConfig(**config_data)
        sub_name = reproduction_subdir or f"reproduced_{record.id[:8]}"
        return self.generate(config, output_subdir=sub_name)
