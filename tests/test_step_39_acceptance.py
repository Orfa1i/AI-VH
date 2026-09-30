"""
Acceptance criteria tests for STEP 39 (P6.4):
Reviewer agreement and feedback snapshots.

Criteria (from plan/prompts/phase-6-feedback/STEP-39_P6.4_agreement-and-snapshots.md):
1. Kappa is correct on a fixture with a known value.
2. Snapshots are reproducible and their lineage recorded.
Plus: per-taxonomy error rates, reviewer throughput, snapshot CLI.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

from vh.feedback.agreement import (
    agreement_report,
    claim_kappa,
    cohens_kappa,
    decision_kappa,
    per_taxonomy_error_rates,
    reviewer_throughput,
)
from vh.feedback.models import FeedbackStore
from vh.feedback.snapshot import build_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent


def _report() -> Dict[str, Any]:
    return {
        "patient_summary": "Summary.",
        "differential": [{"dx": "Acute Anterior STEMI", "likelihood": "high"}],
        "recommendations": [{"text": "Aspirin."}],
        "claims": [
            {"claim_id": "CLM-01", "text": "Claim one."},
            {"claim_id": "CLM-02", "text": "Claim two."},
            {"claim_id": "CLM-03", "text": "Claim three."},
            {"claim_id": "CLM-04", "text": "Claim four."},
        ],
    }


@pytest.fixture
def store(tmp_path: Path) -> FeedbackStore:
    db = FeedbackStore(db_path=str(tmp_path / "agree.db"))
    yield db
    db.close()


def _two_reviewer_overlap(
    store: FeedbackStore,
    ratings_a: List[str],
    ratings_b: List[str],
    decision_a: str = "approve",
    decision_b: str = "approve",
) -> str:
    """One overlap original reviewed independently by two reviewers."""
    rev_a, _ = store.register_reviewer("Agree A", "attending")
    rev_b, _ = store.register_reviewer("Agree B", "attending")
    original_id = store.store_original("CASE-AGR-001", _report(), "m", "p@1")
    asg_a = store.assign_review(original_id, rev_a)
    asg_b = store.assign_review(original_id, rev_b)
    ses_a = store.start_session(asg_a)
    ses_b = store.start_session(asg_b)
    for idx, rating in enumerate(ratings_a, start=1):
        store.rate_claim(ses_a, f"CLM-0{idx}", rating, "wrong_diagnosis")
    for idx, rating in enumerate(ratings_b, start=1):
        store.rate_claim(ses_b, f"CLM-0{idx}", rating, "wrong_diagnosis")
    if decision_a == "reject":
        store.record_decision(ses_a, "reject")
    else:
        store.finalize_report(ses_a, decision=decision_a)
    if decision_b == "reject":
        store.record_decision(ses_b, "reject")
    else:
        store.finalize_report(ses_b, decision=decision_b)
    return original_id


def test_kappa_known_value():
    """Criterion 1: kappa matches a hand-computed fixture (0.6) + edges."""
    pairs = [
        ("Y", "Y"),
        ("Y", "Y"),
        ("Y", "Y"),
        ("Y", "Y"),
        ("Y", "N"),
        ("N", "Y"),
        ("N", "N"),
        ("N", "N"),
        ("N", "N"),
        ("N", "N"),
    ]
    # po = 0.8, pe = 0.5*0.5 + 0.5*0.5 = 0.5 -> kappa = 0.6
    assert cohens_kappa(pairs) == pytest.approx(0.6)
    assert cohens_kappa([("a", "a"), ("b", "b"), ("c", "c")]) == pytest.approx(1.0)
    assert cohens_kappa([]) == pytest.approx(0.0)


def test_claim_and_decision_agreement(store: FeedbackStore):
    """Kappas computed over real overlap sessions in the store."""
    # Claims: A and B agree on 3 of 4 with balanced marginals -> kappa 0.5.
    # A: correct, correct, incorrect, incorrect
    # B: correct, incorrect, correct, incorrect
    # po = 0.5; P(correct) = 0.5 both -> pe = 0.5 -> kappa = 0.0. Use exact check.
    _two_reviewer_overlap(
        store,
        ["correct", "correct", "incorrect", "incorrect"],
        ["correct", "incorrect", "correct", "incorrect"],
    )
    assert claim_kappa(store) == pytest.approx(0.0)
    # Identical decisions -> decision kappa 1.0.
    assert decision_kappa(store) == pytest.approx(1.0)

    report = agreement_report(store)
    assert report["n_overlap_originals"] == 1
    assert report["claim_kappa"] == pytest.approx(0.0)
    assert report["decision_kappa"] == pytest.approx(1.0)


def test_taxonomy_rates_and_throughput(store: FeedbackStore):
    """Per-taxonomy error rates and reviewer throughput from fixtures."""
    _two_reviewer_overlap(
        store,
        ["correct", "incorrect", "incorrect", "incorrect"],
        ["correct", "correct", "incorrect", "incorrect"],
    )
    rates = per_taxonomy_error_rates(store)
    assert rates["wrong_diagnosis"]["n"] == 8
    assert rates["wrong_diagnosis"]["error_rate"] == pytest.approx(5 / 8)

    throughput = reviewer_throughput(store)
    assert len(throughput) == 2
    for row in throughput:
        assert row["decisions"] == 1
        assert row["mean_seconds_per_decision"] >= 0.0


def test_snapshot_reproducible_and_lineage(store: FeedbackStore, tmp_path: Path):
    """Criterion 2: two snapshots of one store are identical; lineage recorded."""
    _two_reviewer_overlap(
        store,
        ["correct", "correct", "incorrect", "incorrect"],
        ["correct", "incorrect", "correct", "incorrect"],
        decision_a="correct",
        decision_b="approve",
    )
    out_a = tmp_path / "snap-a"
    out_b = tmp_path / "snap-b"
    snap_a = build_snapshot(
        store, output_dir=str(out_a), version="vTest", registry_db=str(tmp_path / "art.db")
    )
    snap_b = build_snapshot(
        store, output_dir=str(out_b), version="vTest", registry_db=str(tmp_path / "art.db")
    )

    # Identical data payloads (manifest carries run timestamps, compared below).
    for name in ("originals.jsonl", "edits.jsonl", "finals.jsonl", "ratings.jsonl", "agreement.json"):
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes()
    assert snap_a["dataset_sha256"] == snap_b["dataset_sha256"]

    manifest = json.loads((out_a / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "vTest"
    assert manifest["dataset_sha256"] == snap_a["dataset_sha256"]
    assert manifest["counts"]["originals"] == 1
    assert manifest["counts"]["finals"] == 2
    assert "lineage" in manifest and manifest["lineage"]["golden_version"] == "v1"
    assert manifest["lineage"]["artifact_id"] == snap_a["artifact_id"]

    # Agreement flags travel with the snapshot.
    agreement = json.loads((out_a / "agreement.json").read_text(encoding="utf-8"))
    assert agreement["n_overlap_originals"] == 1


def test_snapshot_cli(tmp_path: Path):
    """`vh feedback snapshot` exits 0 and writes a versioned dataset."""
    store_path = tmp_path / "cli.db"
    store = FeedbackStore(db_path=str(store_path))
    store.store_original("CASE-CLI-001", _report(), "m", "p@1")
    store.close()

    out = tmp_path / "snap-cli"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "vh.cli",
            "feedback",
            "snapshot",
            "--db",
            str(store_path),
            "--output",
            str(out),
            "--version",
            "vCli",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stdout}\n{proc.stderr}"
    assert (out / "manifest.json").exists()
    assert (out / "originals.jsonl").exists()
