"""
Acceptance tests for Phase 0 | STEP 05 (P0.5: Golden-set authoring tools and draft seed cases).
Written before implementation to verify red-to-green TDD cycle.
"""

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


@pytest.mark.unit
def test_validator_rejects_missing_fields_and_invalid_enums():
    """Verify the validator rejects missing required fields and invalid enum values."""
    from vh.golden.validator import validate_case_dict, ValidationError

    # Missing ground_truth field
    incomplete_case = {
        "case_id": "TEST-001",
        "specialty": "Cardiology",
        "patient_ref": "PAT-001",
        "visible_presentation": {"chief_complaint": "Chest pain"}
        # missing ground_truth, status, etc.
    }
    with pytest.raises((ValidationError, Exception)):
        validate_case_dict(incomplete_case)

    # Invalid status enum
    invalid_status_case = {
        "case_id": "TEST-002",
        "specialty": "Cardiology",
        "patient_ref": "PAT-002",
        "visible_presentation": {"chief_complaint": "Chest pain"},
        "ground_truth": {
            "primary_dx": "STEMI",
            "acceptable_differential": [],
            "expected_workup": [],
            "red_flags": []
        },
        "status": "APPROVED_WITHOUT_SIGN_OFF",  # Invalid enum value (must be draft or verified)
        "version": "1.0.0"
    }
    with pytest.raises((ValidationError, Exception)):
        validate_case_dict(invalid_status_case)


@pytest.mark.unit
def test_setting_verified_status_without_signoff_is_rejected():
    """Verify that setting status: verified directly without a matching sign-off entry is rejected."""
    from vh.golden.validator import validate_case_dict, UnauthorizedVerificationError

    unauthorized_case = {
        "case_id": "TEST-003",
        "specialty": "Cardiology",
        "patient_ref": "PAT-003",
        "visible_presentation": {"chief_complaint": "Chest pain"},
        "ground_truth": {
            "primary_dx": "STEMI",
            "acceptable_differential": [],
            "expected_workup": [],
            "red_flags": []
        },
        "status": "verified",  # Attempting to declare verified directly
        "version": "1.0.0"
    }

    # Strict check: direct validation without approved sign-off registry raises error
    with pytest.raises(UnauthorizedVerificationError):
        validate_case_dict(unauthorized_case, allow_verified=False)


@pytest.mark.unit
def test_release_contains_only_verified_cases_and_manifest_hashes_correct(tmp_path):
    """Verify that a release contains only verified cases and manifest hashes match exact content."""
    from vh.golden.releaser import build_release
    from eval.harness.manifest import validate_manifest

    drafts_dir = tmp_path / "drafts"
    drafts_dir.mkdir()
    release_dir = tmp_path / "v1"

    # Create 2 verified cases and 1 draft case in source directory
    case_verified_1 = {
        "case_id": "GOLDEN-V-001",
        "specialty": "Cardiology",
        "patient_ref": "P1",
        "visible_presentation": {"chief_complaint": "Pain"},
        "ground_truth": {"primary_dx": "STEMI", "acceptable_differential": [], "expected_workup": [], "red_flags": []},
        "status": "verified",
        "reviewer": "Dr. Marcus Vance",
        "reviewed_at": "2026-09-28T00:00:00Z",
        "version": "1.0.0"
    }
    case_verified_2 = {
        "case_id": "GOLDEN-V-002",
        "specialty": "Pulmonology",
        "patient_ref": "P2",
        "visible_presentation": {"chief_complaint": "Cough"},
        "ground_truth": {"primary_dx": "Pneumonia", "acceptable_differential": [], "expected_workup": [], "red_flags": []},
        "status": "verified",
        "reviewer": "Dr. Marcus Vance",
        "reviewed_at": "2026-09-28T00:00:00Z",
        "version": "1.0.0"
    }
    case_draft_3 = {
        "case_id": "GOLDEN-D-003",
        "specialty": "Endocrinology",
        "patient_ref": "P3",
        "visible_presentation": {"chief_complaint": "Nausea"},
        "ground_truth": {"primary_dx": "DKA", "acceptable_differential": [], "expected_workup": [], "red_flags": []},
        "status": "draft",
        "version": "1.0.0"
    }

    (drafts_dir / "case_01.json").write_text(json.dumps(case_verified_1), encoding="utf-8")
    (drafts_dir / "case_02.json").write_text(json.dumps(case_verified_2), encoding="utf-8")
    (drafts_dir / "case_03.json").write_text(json.dumps(case_draft_3), encoding="utf-8")

    release_info = build_release(source_dir=drafts_dir, target_dir=release_dir, version_tag="v1")
    assert release_info["cases_released"] == 2

    # Verify directory contents
    released_files = [p.name for p in release_dir.glob("*.json") if p.name != "manifest.json"]
    assert len(released_files) == 2
    assert "case_03.json" not in released_files, "Draft cases must never be included in a release"

    # Verify manifest integrity
    validate_manifest(release_dir)


@pytest.mark.unit
def test_draft_references_are_real_or_explicitly_empty_flagged():
    """Verify that all drafted references in eval/golden/drafts are real or explicitly flagged empty."""
    from vh.golden.validator import validate_reference_authenticity

    drafts_dir = REPO_ROOT / "eval" / "golden" / "drafts"
    if not drafts_dir.exists() or not list(drafts_dir.glob("*.json")):
        pytest.skip("Draft cases directory not yet populated")

    draft_files = list(drafts_dir.glob("*.json"))
    assert len(draft_files) == 60, f"Must have exactly 60 draft seed cases, found {len(draft_files)}"

    for case_file in draft_files:
        data = json.loads(case_file.read_text(encoding="utf-8"))
        for ref in data.get("supporting_references", []):
            is_valid, reason = validate_reference_authenticity(ref)
            assert is_valid, f"Invalid or invented citation in {case_file.name}: {ref} ({reason})"
