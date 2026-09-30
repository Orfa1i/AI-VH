"""
Tests for the plan-update import commands (updated plan/CLAUDE.md rule:
status changes only through import commands applying exactly what the
sign-off lists):
- `vh golden chunkmap-import` (updated STEP-18 prompt).
- `vh safety import-signoff` (updated STEP-25 prompt).
- `training.min_preference_pairs` threshold model support (updated STEP-02/53).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def _chunkmap_fixture() -> dict:
    return {
        "golden_version": "v1",
        "status": "draft_for_h2_review",
        "case_mappings": {
            "CASE-001": {
                "specialty": "Cardiology",
                "supporting_references": [
                    {
                        "source": "ACC Guideline",
                        "locator": "PMID: 111",
                        "status": "mapped",
                        "matched_doc_id": "GUIDELINE-OLD",
                    },
                    {
                        "source": "Textbook",
                        "locator": "Chapter 1",
                        "status": "unmappable",
                        "reason": "copyright",
                    },
                ],
            },
            "CASE-002": {
                "specialty": "Pulmonology",
                "supporting_references": [
                    {
                        "source": "ATS Guideline",
                        "locator": "Chest Guideline 2019",
                        "status": "unmappable",
                        "reason": "pending review",
                    }
                ],
            },
        },
    }


def _signoff_with_correction() -> str:
    return """# Sign-off: H2 | Confirm Golden-Set Chunk Mapping

- **Reviewer:** Test Owner
- **Date:** 2026-09-30
- **Result:** PASS

## Approved items
- All mappings look correct.

## Rejected or corrected items
- CHUNGMAP-CORRECTION: CASE-002 | Chest Guideline 2019 | status = mapped
- CHUNGMAP-CORRECTION: CASE-002 | Chest Guideline 2019 | matched_doc_id = GUIDELINE-CAP-2019
"""


def _signoff_no_corrections() -> str:
    return """# Sign-off: H2 | Confirm Golden-Set Chunk Mapping

- **Reviewer:** Test Owner
- **Date:** 2026-09-30
- **Result:** PASS

## Approved items
- All mappings look correct.

## Rejected or corrected items
- None
"""


def test_chunkmap_import_changes_only_listed_entries(tmp_path: Path):
    """Updated STEP-18: corrections apply exactly; everything else untouched."""
    from vh.golden.chunkmap import apply_chunkmap_corrections

    chunkmap_path = tmp_path / "chunkmap.json"
    before = _chunkmap_fixture()
    chunkmap_path.write_text(json.dumps(before, indent=2, sort_keys=True), encoding="utf-8")
    signoff_path = tmp_path / "H2.md"
    signoff_path.write_text(_signoff_with_correction(), encoding="utf-8")

    result = apply_chunkmap_corrections(str(signoff_path), str(chunkmap_path))
    assert result["corrections_applied"] == 2

    after = json.loads(chunkmap_path.read_text(encoding="utf-8"))
    ref = after["case_mappings"]["CASE-002"]["supporting_references"][0]
    assert ref["status"] == "mapped"
    assert ref["matched_doc_id"] == "GUIDELINE-CAP-2019"

    # Everything else byte-identical: restore the two fields and compare.
    ref["status"] = "unmappable"
    del ref["matched_doc_id"]
    ref["reason"] = "pending review"
    assert after == before


def test_chunkmap_import_no_corrections_is_noop(tmp_path: Path):
    """A sign-off listing None leaves the chunk map byte-identical."""
    from vh.golden.chunkmap import apply_chunkmap_corrections

    chunkmap_path = tmp_path / "chunkmap.json"
    chunkmap_path.write_text(
        json.dumps(_chunkmap_fixture(), indent=2, sort_keys=True), encoding="utf-8"
    )
    digest_before = chunkmap_path.read_bytes()
    signoff_path = tmp_path / "H2.md"
    signoff_path.write_text(_signoff_no_corrections(), encoding="utf-8")

    result = apply_chunkmap_corrections(str(signoff_path), str(chunkmap_path))
    assert result["corrections_applied"] == 0
    assert chunkmap_path.read_bytes() == digest_before


def test_chunkmap_import_unknown_target_fails_closed(tmp_path: Path):
    """Corrections matching nothing abort without writing."""
    from vh.golden.chunkmap import apply_chunkmap_corrections

    chunkmap_path = tmp_path / "chunkmap.json"
    chunkmap_path.write_text(
        json.dumps(_chunkmap_fixture(), indent=2, sort_keys=True), encoding="utf-8"
    )
    digest_before = chunkmap_path.read_bytes()
    signoff_path = tmp_path / "H2.md"
    signoff_path.write_text(
        _signoff_with_correction().replace("CASE-002", "CASE-NOPE"), encoding="utf-8"
    )

    with pytest.raises(KeyError):
        apply_chunkmap_corrections(str(signoff_path), str(chunkmap_path))
    assert chunkmap_path.read_bytes() == digest_before


def _safety_table(table_id: str, rows: list) -> dict:
    return {
        "metadata": {"table_id": table_id, "version": "1.0.0", "status": "draft"},
        "criteria": rows,
    }


def _safety_signoff() -> str:
    return """# Sign-off: H4 | Safety Tables

- **Reviewer:** Dr. Test, MD
- **Date:** 2026-09-30
- **Result:** PASS

## 1. `configs/safety/red_flags.yaml` (SAFETY-REDFLAG-001)
- RF-HYPOXEMIA approved per guidelines.
- Verdict: APPROVED. Promoted to `status: reviewed`.

## 2. `configs/safety/dose_ranges.yaml` (SAFETY-DOSE-001)
- Verdict: NEEDS CORRECTION before approval.
- SAFETY-CORRECTION: dose_ranges.yaml | drug=Aspirin | max_single_dose_mg = 325
"""


def test_safety_import_approves_only_listed_tables(tmp_path: Path):
    """Updated STEP-25: approved tables flip to reviewed; others stay draft."""
    from vh.verification.safety_import import apply_safety_signoff

    safety_dir = tmp_path / "safety"
    safety_dir.mkdir()
    red = _safety_table(
        "SAFETY-REDFLAG-001",
        [{"flag_id": "RF-X", "threshold": 90.0, "status": "draft"}],
    )
    dose = _safety_table(
        "SAFETY-DOSE-001",
        [
            {"drug": "Aspirin", "max_single_dose_mg": 300, "status": "draft"},
            {"drug": "Metformin", "max_single_dose_mg": 2550, "status": "draft"},
        ],
    )
    (safety_dir / "red_flags.yaml").write_text(yaml.safe_dump(red), encoding="utf-8")
    (safety_dir / "dose_ranges.yaml").write_text(yaml.safe_dump(dose), encoding="utf-8")
    signoff_path = tmp_path / "H4.md"
    signoff_path.write_text(_safety_signoff(), encoding="utf-8")

    result = apply_safety_signoff(str(signoff_path), str(safety_dir))
    assert result["tables_approved"] == ["red_flags.yaml"]
    assert result["rows_corrected"] == 1

    red_after = yaml.safe_load((safety_dir / "red_flags.yaml").read_text(encoding="utf-8"))
    assert red_after["metadata"]["status"] == "reviewed"
    assert red_after["metadata"]["reviewer"] == "Dr. Test, MD"
    assert red_after["metadata"]["reviewed_at"] == "2026-09-30"

    dose_after = yaml.safe_load((safety_dir / "dose_ranges.yaml").read_text(encoding="utf-8"))
    assert dose_after["metadata"]["status"] == "draft"
    aspirin = next(r for r in dose_after["criteria"] if r["drug"] == "Aspirin")
    assert aspirin["max_single_dose_mg"] == 325
    metformin = next(r for r in dose_after["criteria"] if r["drug"] == "Metformin")
    assert metformin == {"drug": "Metformin", "max_single_dose_mg": 2550, "status": "draft"}


def test_safety_import_preserves_real_file_comments(tmp_path: Path):
    """Surgical edits keep curated header comments in real table files."""
    from vh.verification.safety_import import apply_safety_signoff

    safety_dir = tmp_path / "safety"
    safety_dir.mkdir()
    real_text = (REPO_ROOT / "configs" / "safety" / "red_flags.yaml").read_text(encoding="utf-8")
    assert "# Curated Physiological" in real_text
    (safety_dir / "red_flags.yaml").write_text(real_text, encoding="utf-8")
    signoff_path = tmp_path / "H4.md"
    signoff_path.write_text(
        "# Sign-off: H4\n\n- **Reviewer:** Dr. Test, MD\n- **Date:** 2026-09-30\n\n"
        "## `configs/safety/red_flags.yaml`\n- Verdict: APPROVED.\n"
        "- SAFETY-CORRECTION: red_flags.yaml | flag_id=RF-HYPOXEMIA | threshold = 89.5\n",
        encoding="utf-8",
    )

    result = apply_safety_signoff(str(signoff_path), str(safety_dir))
    assert result["tables_approved"] == ["red_flags.yaml"]

    updated = (safety_dir / "red_flags.yaml").read_text(encoding="utf-8")
    assert "# Curated Physiological" in updated
    data = yaml.safe_load(updated)
    hypo = next(r for r in data["criteria"] if r["flag_id"] == "RF-HYPOXEMIA")
    assert hypo["threshold"] == 89.5
    assert len(data["criteria"]) == len(yaml.safe_load(real_text)["criteria"])


def test_safety_import_bold_verdict_format(tmp_path: Path):
    """Regression (real-H4 dry run): `**Verdict:** APPROVED` (bold markers)
    counts as approval; `NEEDS CORRECTION` does not."""
    from vh.verification.safety_import import apply_safety_signoff

    safety_dir = tmp_path / "safety"
    safety_dir.mkdir()
    (safety_dir / "red_flags.yaml").write_text(
        yaml.safe_dump(_safety_table("SAFETY-REDFLAG-001", [])), encoding="utf-8"
    )
    (safety_dir / "dose_ranges.yaml").write_text(
        yaml.safe_dump(_safety_table("SAFETY-DOSE-001", [])), encoding="utf-8"
    )
    signoff_path = tmp_path / "H4.md"
    signoff_path.write_text(
        "# Sign-off: H4\n\n- **Reviewer:** Dr. Test, MD\n- **Date:** 2026-09-30\n\n"
        "## Tables\n\n1. **`configs/safety/red_flags.yaml`**:\n"
        "- **Verdict:** APPROVED. Promoted to `status: reviewed`.\n\n"
        "2. **`configs/safety/dose_ranges.yaml`**:\n"
        "- **Verdict:** NEEDS CORRECTION before approval.\n",
        encoding="utf-8",
    )

    result = apply_safety_signoff(str(signoff_path), str(safety_dir))
    assert result["tables_approved"] == ["red_flags.yaml"]
    red_after = yaml.safe_load((safety_dir / "red_flags.yaml").read_text(encoding="utf-8"))
    assert red_after["metadata"]["status"] == "reviewed"


def test_golden_chunkmap_import_cli(tmp_path: Path):
    """`vh golden chunkmap-import` is wired and exits 0."""
    chunkmap_path = tmp_path / "chunkmap.json"
    chunkmap_path.write_text(
        json.dumps(_chunkmap_fixture(), indent=2, sort_keys=True), encoding="utf-8"
    )
    signoff_path = tmp_path / "H2.md"
    signoff_path.write_text(_signoff_with_correction(), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "vh.cli",
            "golden",
            "chunkmap-import",
            "--signoff",
            str(signoff_path),
            "--chunkmap",
            str(chunkmap_path),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stdout}\n{proc.stderr}"
    after = json.loads(chunkmap_path.read_text(encoding="utf-8"))
    assert after["case_mappings"]["CASE-002"]["supporting_references"][0]["status"] == "mapped"


def test_safety_import_cli(tmp_path: Path):
    """`vh safety import-signoff` is wired and exits 0."""
    safety_dir = tmp_path / "safety"
    safety_dir.mkdir()
    (safety_dir / "red_flags.yaml").write_text(
        yaml.safe_dump(_safety_table("SAFETY-REDFLAG-001", [])), encoding="utf-8"
    )
    (safety_dir / "dose_ranges.yaml").write_text(
        yaml.safe_dump(
            _safety_table(
                "SAFETY-DOSE-001",
                [{"drug": "Aspirin", "max_single_dose_mg": 300, "status": "draft"}],
            )
        ),
        encoding="utf-8",
    )
    signoff_path = tmp_path / "H4.md"
    signoff_path.write_text(_safety_signoff(), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "vh.cli",
            "safety",
            "import-signoff",
            "--signoff",
            str(signoff_path),
            "--safety-dir",
            str(safety_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stdout}\n{proc.stderr}"
    red_after = yaml.safe_load((safety_dir / "red_flags.yaml").read_text(encoding="utf-8"))
    assert red_after["metadata"]["status"] == "reviewed"


def test_training_min_preference_pairs_model_support():
    """Updated STEP-02/53: the loader model carries the new key (default null);
    the shipped yaml (owner adds the key later) still loads cleanly."""
    from vh.common.thresholds import load_thresholds

    loader = load_thresholds()
    assert loader.config.training.min_preference_pairs is None
    assert loader.is_set("training", "min_preference_pairs") is False

    customized = load_thresholds()
    customized.load_from_dict(
        {**customized._raw_data, "training": {**customized._raw_data["training"], "min_preference_pairs": 200}}
    )
    assert customized.config.training.min_preference_pairs == 200
    assert customized.evaluate_gate("training", "min_preference_pairs", candidate_value=250) is True
    assert customized.evaluate_gate("training", "min_preference_pairs", candidate_value=10) is False
