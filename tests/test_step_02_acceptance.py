"""
Acceptance tests for Phase 0 | STEP 02 (P0.2: Project skeleton, configuration, CI).
Written before full implementation to verify red-to-green TDD cycle.
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


@pytest.mark.unit
def test_thresholds_yaml_exists():
    """Verify that configs/thresholds.yaml exists and is not empty."""
    thresholds_path = REPO_ROOT / "configs" / "thresholds.yaml"
    assert thresholds_path.exists(), "configs/thresholds.yaml must exist"
    content = thresholds_path.read_text(encoding="utf-8")
    assert len(content) > 100, "configs/thresholds.yaml must not be empty"


@pytest.mark.unit
def test_thresholds_loader_loads_successfully():
    """Verify loader reads configs/thresholds.yaml cleanly."""
    from vh.common.thresholds import load_thresholds

    thresholds = load_thresholds()
    assert thresholds is not None
    assert thresholds.golden.min_verified_cases == 50
    assert thresholds.retrieval.recall_at_10 == 0.85
    assert thresholds.cases.fhir_valid_rate == 1.0


@pytest.mark.unit
def test_thresholds_loader_missing_key_raises():
    """Verify that accessing or validating a missing key raises KeyError."""
    from vh.common.thresholds import ThresholdsLoader, MissingThresholdError

    loader = ThresholdsLoader()
    # Loading dict missing a mandatory section
    with pytest.raises((KeyError, MissingThresholdError)):
        loader.load_from_dict({"golden": {"min_verified_cases": 50}})

    # Accessing unknown key on a loaded instance
    thresholds = loader.load(REPO_ROOT / "configs" / "thresholds.yaml")
    with pytest.raises((KeyError, MissingThresholdError, AttributeError)):
        loader.get("generation", "non_existent_key")


@pytest.mark.unit
def test_thresholds_loader_null_reported_as_not_set():
    """Verify that null values in thresholds.yaml are reported as NOT SET and fail gates."""
    from vh.common.thresholds import load_thresholds, ThresholdStatus

    loader_obj = load_thresholds()

    # dx_top3_min is null in generation
    assert loader_obj.is_set("generation", "dx_top3_min") is False
    status_dx = loader_obj.get_status("generation", "dx_top3_min")
    assert status_dx == ThresholdStatus.NOT_SET

    # encounter_score_min is null in agents
    assert loader_obj.is_set("agents", "encounter_score_min") is False
    status_enc = loader_obj.get_status("agents", "encounter_score_min")
    assert status_enc == ThresholdStatus.NOT_SET

    # Evaluating a gate that uses a NOT SET threshold MUST fail
    gate_passed = loader_obj.evaluate_gate("generation", "dx_top3_min", candidate_value=0.95)
    assert gate_passed is False, "A gate using a NOT SET threshold must evaluate to False (fail)"


@pytest.mark.unit
def test_thresholds_exact_provisional_values():
    """Verify exact values specified in STEP 02 prompt are present."""
    from vh.common.thresholds import load_thresholds

    t = load_thresholds()
    assert t.golden.min_verified_cases == 50
    assert t.cases.fhir_valid_rate == 1.0
    assert t.cases.leakage_count == 0
    assert t.cases.plausibility_pass_rate == 1.0
    assert t.cases.spotcheck_defect_rate_max == 0.05
    assert t.retrieval.recall_at_10 == 0.85
    assert t.retrieval.mrr_min == 0.60
    assert t.retrieval.traceability_rate == 1.0
    assert t.retrieval.stale_retrieval_count == 0
    assert t.retrieval.p95_latency_s == 1.5
    assert t.generation.schema_valid_rate == 1.0
    assert t.generation.fabricated_citation_rate == 0.0
    assert t.generation.abstention_correct_rate == 0.90
    assert t.generation.rag_beats_baseline is True
    assert t.verification.critical_fault_detection == 1.0
    assert t.verification.noncritical_fault_detection == 0.90
    assert t.verification.false_flag_rate_max == 0.10
    assert t.verification.judge_kappa_min == 0.70
    assert t.verification.faithfulness_min == 0.90
    assert t.verification.contextual_relevancy_min == 0.80
    assert t.verification.p95_latency_s == 5.0
    assert t.agents.permission_violations == 0
    assert t.agents.runaway_loops == 0
    assert t.agents.replay_mismatch_count == 0
    assert t.review.kappa_min == 0.60
    assert t.review.overlap_fraction == 0.15
    assert t.training.min_reviewed_cases == 500
    assert t.training.safety_regressions == 0
    assert t.training.must_beat_production is True
    assert t.ui.min_fps == 50
    assert t.ui.max_load_s == 5
    assert t.ui.max_sync_lag_ms == 500
    assert t.ui.output_divergence_count == 0


@pytest.mark.unit
def test_secret_scanner_detects_planted_fake_key(tmp_path):
    """Verify that a planted fake key in a test fixture is caught by the secret scanner."""
    from scripts.scan_secrets import scan_file, Finding

    # Plant a fake AWS secret key, GitHub token, and private key in temporary fixture file
    fake_fixture = tmp_path / "planted_secrets_fixture.py"
    fake_token = "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyzAB"
    fake_aws = "AKIA" + "1111111111EXAMPLE"
    fake_key = "-----BEGIN " + "RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
    fake_fixture.write_text(
        f'# Test fixture with planted credentials\nAWS_KEY = "{fake_aws}"\nTOKEN = "{fake_token}"\nKEY = "{fake_key}"\n',
        encoding="utf-8"
    )

    findings = scan_file(fake_fixture)
    assert len(findings) > 0, "Secret scanner must detect planted fake secrets"
    rule_names = [f.rule_name for f in findings]
    assert any("AWS" in r or "GitHub" in r or "Private Key" in r for r in rule_names)


@pytest.mark.integration
def test_smoke_backend_fastapi_starts():
    """Smoke test proving existing FastAPI backend endpoints are live and healthy."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "agents" in data


@pytest.mark.unit
def test_smoke_frontend_exists_and_runnable():
    """Smoke test verifying frontend project configuration and entry points."""
    frontend_dir = REPO_ROOT / "frontend"
    assert (frontend_dir / "package.json").exists(), "frontend/package.json must exist"
    assert (frontend_dir / "src" / "App.tsx").exists(), "frontend/src/App.tsx must exist"
    assert (frontend_dir / "vite.config.ts").exists(), "frontend/vite.config.ts must exist"


@pytest.mark.unit
def test_vh_package_submodules_mapped():
    """Verify ADR-0001 subpackage layout mappings exist and are importable."""
    import vh
    import vh.common
    import vh.cases
    import vh.rag
    import vh.generation
    import vh.verification
    import vh.agents
    import vh.feedback
    import vh.training
    import vh.events

    assert hasattr(vh, "__version__")
    assert vh.common is not None
    assert vh.cases is not None
    assert vh.rag is not None
    assert vh.generation is not None
    assert vh.verification is not None
    assert vh.agents is not None
    assert vh.feedback is not None
    assert vh.training is not None
    assert vh.events is not None


@pytest.mark.unit
def test_pydantic_settings_loader():
    """Verify configuration settings loader via pydantic-settings."""
    from vh.common.config import Settings, get_settings

    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "APP_ENV")
    assert hasattr(settings, "PORT")
    assert settings.PORT == 8000
