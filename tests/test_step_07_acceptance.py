"""
Acceptance tests for Phase 1 | STEP 07 (P1.1: Synthea runner - reproducible FHIR export).
Written before implementation to verify red-to-green TDD cycle.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.unit
def test_synthea_config_schema_and_command_args():
    """Verify SyntheaGenerationConfig validates fields and produces deterministic CLI arguments."""
    from vh.synthea.config import SyntheaGenerationConfig

    cfg = SyntheaGenerationConfig(
        seed=12345,
        clinician_seed=67890,
        reference_date="2026-01-01",
        population=5,
        state="Massachusetts",
        city="Boston",
        modules=["cardiovascular"],
        synthea_version="v3.3.0"
    )

    args = cfg.to_command_args()
    assert "-s" in args and "12345" in args
    assert "-cs" in args and "67890" in args
    assert "-p" in args and "5" in args
    assert "Massachusetts" in args
    assert "Boston" in args
    assert cfg.synthea_version == "v3.3.0"


@pytest.mark.unit
def test_synthea_deterministic_identical_output_hash(tmp_path):
    """Verify that identical seed, clinician seed, reference date, and version yield identical output hash."""
    from vh.synthea.config import SyntheaGenerationConfig
    from vh.synthea.runner import SyntheaRunner

    cfg1 = SyntheaGenerationConfig(
        seed=4242,
        clinician_seed=9999,
        reference_date="2026-03-15",
        population=3,
        state="Massachusetts",
        synthea_version="v3.3.0"
    )
    cfg2 = SyntheaGenerationConfig(
        seed=4242,
        clinician_seed=9999,
        reference_date="2026-03-15",
        population=3,
        state="Massachusetts",
        synthea_version="v3.3.0"
    )

    runner = SyntheaRunner(base_output_dir=tmp_path)
    res1 = runner.generate(cfg1)
    res2 = runner.generate(cfg2)

    assert res1.bundle_count == 3
    assert res2.bundle_count == 3
    assert res1.output_hash == res2.output_hash, "Deterministic runs must produce identical output hashes"
    assert res1.bundle_hashes == res2.bundle_hashes


@pytest.mark.unit
def test_all_generated_bundles_pass_fhir_r4_validation(tmp_path):
    """Verify that 100% of generated bundles are validated against FHIR R4 specification."""
    from vh.synthea.config import SyntheaGenerationConfig
    from vh.synthea.runner import SyntheaRunner
    from vh.synthea.validator import validate_bundle_directory

    cfg = SyntheaGenerationConfig(
        seed=777,
        clinician_seed=888,
        reference_date="2026-05-01",
        population=4,
        synthea_version="v3.3.0"
    )

    runner = SyntheaRunner(base_output_dir=tmp_path)
    res = runner.generate(cfg)

    report = validate_bundle_directory(res.output_dir)
    assert report.total_bundles == 4
    assert report.valid_bundles == 4
    assert report.pass_rate == 1.0, "100% of bundles must pass FHIR R4 validation"
    assert len(report.errors) == 0


@pytest.mark.unit
def test_generation_reproducible_from_artifact_metadata_alone(tmp_path):
    """Verify that generation can be reproduced strictly from the registered artifact metadata."""
    from vh.synthea.config import SyntheaGenerationConfig
    from vh.synthea.runner import SyntheaRunner

    cfg = SyntheaGenerationConfig(
        seed=10101,
        clinician_seed=20202,
        reference_date="2026-06-01",
        population=2,
        synthea_version="v3.3.0"
    )

    runner = SyntheaRunner(base_output_dir=tmp_path)
    original_res = runner.generate(cfg)
    assert original_res.artifact_id is not None

    # Reproduce solely using artifact_id
    reproduced_res = runner.reproduce_from_artifact(original_res.artifact_id)

    assert reproduced_res.bundle_count == original_res.bundle_count
    assert reproduced_res.output_hash == original_res.output_hash
    assert reproduced_res.bundle_hashes == original_res.bundle_hashes


@pytest.mark.unit
def test_cli_synthea_generate_and_validate(tmp_path):
    """Verify CLI interface for vh synthea generate and vh synthea validate."""
    from vh.synthea.cli import main as synthea_cli

    out_dir = tmp_path / "cli_output"
    args = [
        "generate",
        "--seed", "555",
        "--clinician-seed", "666",
        "--reference-date", "2026-07-01",
        "--population", "2",
        "--output-dir", str(out_dir)
    ]

    ret = synthea_cli(args)
    assert ret == 0
    assert out_dir.exists()
    bundle_files = list(out_dir.glob("*.json"))
    assert len(bundle_files) == 2

    # CLI validate
    val_args = ["validate", "--path", str(out_dir)]
    val_ret = synthea_cli(val_args)
    assert val_ret == 0
