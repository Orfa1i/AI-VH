"""
Acceptance criteria tests for STEP 34 (P5.4):
Encounter scoring and deterministic replay.

Criteria (from plan/prompts/phase-5-agents/STEP-34_P5.4_encounter-scoring-replay.md):
1. Scorer unit tests on hand-built encounters.
2. Replaying 10 runs gives identical event logs (hash comparison).
3. A full golden-set run completes and metrics are reported.
Plus: encounter pipeline added to the harness; replay CLI reproduces logs.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from vh.cases.schema import GoldenCase
from vh.cases.spec import CaseSpec, GroundTruth, HiddenResult, VisiblePresentation
from vh.agents.orchestrator import EncounterBudget, EncounterState, EncounterStatus, EncounterStep
from vh.agents.scoring import EncounterScorer, aggregate_encounter_scores
from vh.agents.replay import (
    REPLAY_DIR,
    hash_event_log,
    load_bundle,
    record_encounter,
    replay_encounter,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_V1_DIR = REPO_ROOT / "eval" / "golden" / "v1"


def _make_case() -> CaseSpec:
    visible = VisiblePresentation(
        presentation="62-year-old male with acute substernal pressure and diaphoresis.",
        demographics={"age": 62, "gender": "male"},
        history="Hypertension, hyperlipidemia.",
        current_medications=["Aspirin"],
        allergies=["Penicillin"],
        initial_vitals={"bp": "136/84", "hr": 88, "rr": 18, "spo2": 96, "temp": 37.0},
        exam="Diaphoretic, chest discomfort.",
    )
    hidden = [
        HiddenResult(
            order_code="DX-ECG",
            order_name="12-Lead ECG",
            result="ST elevation in anterior leads.",
            turnaround_time_minutes=10,
            category="imaging",
        ),
        HiddenResult(
            order_code="LAB-TROP",
            order_name="Troponin I",
            result="Elevated high-sensitivity troponin.",
            turnaround_time_minutes=20,
            category="laboratory",
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Acute Anterior STEMI",
        acceptable_differential=["NSTEMI", "Pericarditis"],
        expected_workup=["12-Lead ECG", "Troponin I"],
        red_flags=["Cardiogenic shock"],
    )
    return CaseSpec(
        case_id="CASE-SCORE-001",
        specialty="Cardiology",
        patient_ref="PAT-SCORE-001",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
        status="verified",
        version="1.0.0",
    )


def _make_completed_state(case_id: str = "CASE-SCORE-001") -> EncounterState:
    """Hand-built completed encounter with correct diagnosis and full workup."""
    report = {
        "patient_summary": "62yo male with acute substernal pressure.",
        "findings": ["ST elevation in anterior leads", "Elevated troponin"],
        "differential": [
            {"dx": "Acute Anterior STEMI", "likelihood": "high"},
            {"dx": "NSTEMI", "likelihood": "moderate"},
            {"dx": "Pericarditis", "likelihood": "low"},
        ],
        "recommendations": [
            {"text": "Monitor for cardiogenic shock and arrange emergent angiography."}
        ],
        "claims": [],
    }
    history = [
        EncounterStep(
            step_number=1,
            actor="doctor",
            action="order_workup",
            payload={"ordered_tests": ["DX-ECG", "LAB-TROP"]},
            sim_time_minutes=0,
        ),
        EncounterStep(
            step_number=2,
            actor="diagnostics",
            action="report_findings",
            payload={"findings": {"DX-ECG": "ST elevation", "LAB-TROP": "Elevated"}},
            sim_time_minutes=30,
        ),
        EncounterStep(
            step_number=3,
            actor="doctor",
            action="submit_report",
            payload={"report": report},
            sim_time_minutes=45,
            result_summary="Clinical report submitted and verified",
        ),
    ]
    return EncounterState(
        encounter_id="enc_test_perfect",
        case_id=case_id,
        status=EncounterStatus.COMPLETED,
        termination_reason="report_submitted_and_verified",
        step_count=3,
        token_count=500,
        cost=0.05,
        sim_time_minutes=45,
        report=report,
        verification={"status": "verified", "passed": True, "critical_count": 0},
        history=history,
    )


def test_scorer_perfect_encounter_high_score():
    """Criterion 1: hand-built perfect encounter scores near 1.0 on all axes."""
    case = _make_case()
    state = _make_completed_state()
    scorer = EncounterScorer()
    score = scorer.score(state, case)

    assert score.dx_top1 == 1.0
    assert score.dx_top3 == 1.0
    assert score.workup_recall == pytest.approx(1.0)
    assert score.workup_precision == pytest.approx(1.0)
    assert score.red_flags_addressed == pytest.approx(1.0)
    assert score.verification_passed is True
    assert score.time_to_diagnosis_minutes == 45
    assert 0.0 <= score.time_efficiency <= 1.0
    assert 0.0 <= score.budget_efficiency <= 1.0
    assert score.encounter_score >= 0.85


def test_scorer_missed_diagnosis_low_score():
    """Criterion 1: wrong primary diagnosis yields dx_top1 == 0 and low composite."""
    case = _make_case()
    state = _make_completed_state()
    bad_report = dict(state.report or {})
    bad_report["differential"] = [
        {"dx": "Gastroesophageal Reflux", "likelihood": "high"},
        {"dx": "Costochondritis", "likelihood": "moderate"},
        {"dx": "Anxiety", "likelihood": "low"},
    ]
    state.report = bad_report
    scorer = EncounterScorer()
    score = scorer.score(state, case)

    assert score.dx_top1 == 0.0
    assert score.dx_top3 == 0.0
    assert score.encounter_score < 0.5


def test_scorer_workup_recall_precision():
    """Criterion 1: partial workup plus unnecessary tests penalize recall/precision."""
    case = _make_case()
    state = _make_completed_state()
    # Order only 1 of 2 expected tests plus one unnecessary test.
    state.history[0] = EncounterStep(
        step_number=1,
        actor="doctor",
        action="order_workup",
        payload={"ordered_tests": ["DX-ECG", "LAB-UNKNOWN-XYZ"]},
        sim_time_minutes=0,
    )
    state.history[1] = EncounterStep(
        step_number=2,
        actor="diagnostics",
        action="report_findings",
        payload={"findings": {"DX-ECG": "ST elevation"}},
        sim_time_minutes=30,
    )
    scorer = EncounterScorer()
    score = scorer.score(state, case)

    assert score.workup_recall == pytest.approx(0.5)
    assert score.workup_precision == pytest.approx(0.5)


def test_scorer_red_flags_verification_time_budget():
    """Criterion 1: missed red flags, failed verification, and budget axes behave."""
    case = _make_case()
    state = _make_completed_state()
    # Remove red-flag mention from recommendations.
    bad_report = dict(state.report or {})
    bad_report["recommendations"] = [{"text": "Discharge home with reassurance."}]
    state.report = bad_report
    state.verification = {"status": "flagged", "passed": False, "critical_count": 2}
    state.sim_time_minutes = 300
    state.step_count = 24
    state.token_count = 16000
    state.cost = 0.99
    scorer = EncounterScorer()
    score = scorer.score(state, case)

    assert score.red_flags_addressed == pytest.approx(0.0)
    assert score.verification_passed is False
    assert score.verification_score == pytest.approx(0.0)
    assert 0.0 <= score.time_efficiency < 0.5
    assert 0.0 <= score.budget_efficiency <= 1.0


def test_scorer_workup_alias_panel_matching():
    """Workup synonyms bridge panel names to components (Cardiac Enzymes ~ Troponin)."""
    case = _make_case()
    state = _make_completed_state()
    state.history[0] = EncounterStep(
        step_number=1,
        actor="doctor",
        action="order_workup",
        payload={"ordered_tests": ["Cardiac Enzymes", "ECG"]},
        sim_time_minutes=0,
    )
    state.history[1] = EncounterStep(
        step_number=2,
        actor="diagnostics",
        action="report_findings",
        payload={"findings": {"Cardiac Enzymes": "Elevated", "ECG": "ST elevation"}},
        sim_time_minutes=30,
    )
    scorer = EncounterScorer()
    score = scorer.score(state, case)

    assert score.workup_recall == pytest.approx(1.0)
    assert score.workup_precision == pytest.approx(1.0)


def test_replay_10_runs_identical_hashes():
    """Criterion 2: replaying 10 runs reproduces identical canonical event logs."""
    golden_files = sorted(GOLDEN_V1_DIR.glob("*.json"))
    golden_cases = [
        GoldenCase.model_validate(json.loads(f.read_text(encoding="utf-8")))
        for f in golden_files
        if f.name != "manifest.json"
    ][:10]
    assert len(golden_cases) == 10

    for golden in golden_cases:
        case_spec = CaseSpec.from_golden_case(golden)
        bundle = record_encounter(case_spec=case_spec, seed=42)
        original_hash = bundle.event_log_hash
        assert original_hash == hash_event_log(bundle.event_log)

        replayed_state, replayed_hash = replay_encounter(bundle, case_spec=case_spec)
        assert replayed_hash == original_hash
        assert replayed_state.case_id == case_spec.case_id


def test_full_golden_set_run_reports_metrics():
    """Criterion 3: full golden-set run completes and reports score distribution."""
    golden_files = sorted(GOLDEN_V1_DIR.glob("*.json"))
    golden_cases = [
        GoldenCase.model_validate(json.loads(f.read_text(encoding="utf-8")))
        for f in golden_files
        if f.name != "manifest.json" and GoldenCase.model_validate(
            json.loads(f.read_text(encoding="utf-8"))
        ).status == "verified"
    ]
    assert len(golden_cases) > 0

    scorer = EncounterScorer()
    scores = []
    for golden in golden_cases:
        case_spec = CaseSpec.from_golden_case(golden)
        bundle = record_encounter(case_spec=case_spec, seed=42)
        replayed_state, _ = replay_encounter(bundle, case_spec=case_spec)
        scores.append(scorer.score(replayed_state, case_spec))

    dist = aggregate_encounter_scores(scores)
    assert dist["n_cases"] == len(golden_cases)
    for key in (
        "encounter_score_mean",
        "encounter_score_min",
        "encounter_score_max",
        "dx_top1_rate",
        "dx_top3_rate",
        "workup_recall_mean",
        "workup_precision_mean",
        "red_flags_addressed_mean",
        "verification_pass_rate",
    ):
        assert key in dist
        assert 0.0 <= dist[key] <= 1.0


def test_encounter_pipeline_in_harness():
    """Encounter pipeline is registered in the harness and scores via harness API."""
    from eval.harness.encounter import EncounterHarnessScorer, EncounterPipeline

    golden_files = sorted(GOLDEN_V1_DIR.glob("*.json"))
    golden_cases = [
        GoldenCase.model_validate(json.loads(f.read_text(encoding="utf-8")))
        for f in golden_files
        if f.name != "manifest.json"
    ][:3]
    pipeline = EncounterPipeline()
    scorer = EncounterHarnessScorer()
    results = []
    for golden in golden_cases:
        case_view = golden.to_case_view()
        out = pipeline.run(case_view)
        assert out.case_id == golden.case_id
        assert out.diagnosis
        results.append((case_view, out))
    metrics = scorer.score(results, golden_cases)
    assert "encounter_score_mean" in metrics
    assert 0.0 <= metrics["encounter_score_mean"] <= 1.0


def test_replay_cli_reproduces_log(tmp_path):
    """Replay CLI `vh replay <run_id>` re-executes and reports MATCH."""
    golden_files = sorted(GOLDEN_V1_DIR.glob("*.json"))
    golden = GoldenCase.model_validate(json.loads(golden_files[0].read_text(encoding="utf-8")))
    case_spec = CaseSpec.from_golden_case(golden)
    bundle = record_encounter(case_spec=case_spec, seed=42)
    saved = REPLAY_DIR / f"{bundle.run_id}.json"
    assert saved.exists()

    proc = subprocess.run(
        [sys.executable, "-m", "vh.cli", "replay", bundle.run_id],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stdout}\n{proc.stderr}"
    assert "MATCH" in proc.stdout
