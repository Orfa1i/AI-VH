"""
Phase 3 acceptance tests: automated validation layer V1-V12, failure handling
(regenerate with feedback, max 2 retries, FAILED list), and the ungrounded
fail-safe (tagging + permanent RL exclusion).

Owner: QA Engineer. Clinical content spec: Medical Expert.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from vh.cases.retrieval_log import RetrievalLog, RetrievalLogChunk, RetrievalQueryRecord
from vh.generation.medgemma import MedGemmaAdapter
from vh.generation.pipeline import GroundedGenerationPipeline
from vh.generation.v2_report import AssessmentReport
from vh.rag.sources.base import SourceSearchHit
from vh.verification import phase3
from vh.verification.phase3 import (
    CheckResult,
    validate_assessment_report,
)

CHUNK_1 = "lobar consolidation with air bronchograms suggests bacterial pneumonia and warrants empiric therapy"
CHUNK_2 = "curb sixty five score guides admission decisions for community acquired pneumonia patients"

BROWN_STRUCTURED = {
    "age": 68, "sex": "male",
    "presenting_symptoms": ["fever for 3 days", "productive cough with yellow sputum"],
    "symptom_duration": "3 days",
    "chief_complaint": "fever for 3 days; productive cough with yellow sputum for 3 days",
    "vitals": {"temp": 38.9, "hr": 112, "rr": 28, "bp": "128/78", "spo2": 89},
    "examination_findings": "Tachypnoeic, right basal crackles with bronchial breathing.",
    "comorbidities": ["hypertension"], "current_medications": ["amlodipine 5mg daily"],
    "allergies": ["no known drug allergies"],
    "labs": {"WBC": "16.2 x10^3/uL"}, "imaging": {"CXR": "right lower lobe consolidation"},
    "missing_data": [],
}


def _ev(chunk_id: str = "H-1", quote: str = "lobar consolidation with air bronchograms") -> dict:
    return {"source": "harrison", "chunk_id": chunk_id, "supporting_quote": quote, "note": None}


def _valid_dict(report_id: str = "REP-V3") -> dict:
    return {
        "report_id": report_id,
        "case_summary": "68-year-old man with fever and productive cough for 3 days.",
        "chief_complaint": "fever and productive cough for 3 days",
        "differential_diagnosis": [
            {"diagnosis": "Community-acquired pneumonia", "icd10": "J18.9", "probability": 0.55,
             "supporting_findings": ["fever", "productive cough", "consolidation"],
             "against_findings": [], "evidence": [_ev()]},
            {"diagnosis": "Acute bronchitis", "icd10": "J20.9", "probability": 0.2,
             "supporting_findings": ["cough"], "against_findings": ["consolidation on CXR"], "evidence": [_ev("H-2", "curb sixty five score guides admission")]},
            {"diagnosis": "Aspiration pneumonia", "icd10": "J69.0", "probability": 0.1,
             "supporting_findings": ["cough"], "against_findings": ["no aspiration event"], "evidence": [_ev()]},
        ],
        "final_diagnosis": {"diagnosis": "Community-acquired pneumonia", "icd10": "J18.9",
                            "certainty": "probable", "confidence": 0.7, "evidence": [_ev()]},
        "severity_assessment": [{"score_name": "CURB-65",
                                 "components": {"age_65": "68 (+1)", "respiratory_rate": "28 (0)"},
                                 "value": "1", "interpretation": "CURB-65 = 1; ward care.",
                                 "evidence": [_ev("H-2", "curb sixty five score guides admission")]}],
        "clinical_reasoning": "A 68-year-old man with hypertension has fever with productive cough over three days [H:H-1]. Right basal crackles with consolidation favour community-acquired pneumonia over bronchitis [H:H-1]. A CURB-65 of one supports ward admission with oxygen and empiric antibiotics [H:H-2].",
        "workup": [{"test": "Chest radiography", "priority": "urgent",
                   "rationale": "Confirm consolidation extent.", "evidence": [_ev()]}],
        "treatment": [{"item": "Empiric amoxicillin-clavulanate", "dose_route_frequency_duration": "1g PO q12h for 5 days with oxygen target 94-98%",
                       "rationale": "Covers likely CAP pathogens with oxygen support.", "evidence": [_ev()]}],
        "disposition": {"setting": "ward", "rationale": "CURB-65 = 1 with hypoxaemia risk.", "evidence": [_ev()]},
        "red_flags": ["Worsening dyspnoea"],
        "follow_up": "Reassess within 24 hours.",
        "missing_data": ["blood urea"],
        "conflicts_noted": [],
        "prompt_version": "internal_medicine_assessment@1.0.0",
    }


def _log() -> RetrievalLog:
    return RetrievalLog(
        case_id="C-V3",
        queries=[RetrievalQueryRecord(query="fever cough", top_k=6,
                                      returned_chunk_ids=["H-1", "H-2"],
                                      scores={"H-1": 0.5, "H-2": 0.4})],
        chunks={"H-1": RetrievalLogChunk(chunk_id="H-1", metadata={}, text=CHUNK_1, score=0.5),
                "H-2": RetrievalLogChunk(chunk_id="H-2", metadata={}, text=CHUNK_2, score=0.4)},
    )


def _check(report_dict: dict, check_id: str, structured: dict = BROWN_STRUCTURED) -> CheckResult:
    from vh.verification.phase3 import _Ctx

    report = AssessmentReport.model_validate(report_dict)
    ctx = _Ctx(_log(), dict(structured))
    checks = {"V1": phase3.check_v1, "V2": phase3.check_v2, "V3": phase3.check_v3,
              "V4": phase3.check_v4, "V5": phase3.check_v5, "V6": phase3.check_v6,
              "V7": phase3.check_v7, "V8": phase3.check_v8, "V9": phase3.check_v9,
              "V10": phase3.check_v10, "V11": phase3.check_v11, "V12": phase3.check_v12}
    return checks[check_id](report, ctx)


# --- Per-check tests (V1-V12) --------------------------------------------------

@pytest.mark.unit
def test_v1_valid_and_v5_v9_v11_consistent() -> None:
    assert _check(_valid_dict(), "V1").passed is True
    assert _check(_valid_dict(), "V5").passed is True
    assert _check(_valid_dict(), "V9").passed is True
    assert _check(_valid_dict(), "V11").passed is True


@pytest.mark.unit
def test_v2_rejects_box2d_and_raw_json() -> None:
    bad = _valid_dict()
    bad["clinical_reasoning"] += ' box_2d: [10, 20, 30, 40]'
    assert _check(bad, "V2").passed is False
    bad2 = _valid_dict()
    bad2["follow_up"] = '{"key": "value"}'
    assert _check(bad2, "V2").passed is False
    assert _check(_valid_dict(), "V2").passed is True


@pytest.mark.unit
def test_v3_rejects_repeated_output() -> None:
    bad = _valid_dict()
    bad["clinical_reasoning"] = ("The patient has fever. " * 3) + "Additional assessment notes here."
    assert _check(bad, "V3").passed is False
    assert _check(_valid_dict(), "V3").passed is True


@pytest.mark.unit
def test_v4_rejects_diagnosis_in_chief_complaint() -> None:
    bad = _valid_dict()
    bad["chief_complaint"] = "Pneumonia for 3 days"
    result = _check(bad, "V4")
    assert result.passed is False and "pneumonia" in result.message
    assert _check(_valid_dict(), "V4").passed is True


@pytest.mark.unit
def test_v5_rejects_vague_final_without_provisional() -> None:
    bad = _valid_dict()
    bad["final_diagnosis"] = {"diagnosis": "Undifferentiated Acute Medical Illness", "icd10": "",
                              "certainty": "probable", "confidence": 0.7, "evidence": [_ev()]}
    assert _check(bad, "V5").passed is False
    ok = _valid_dict()
    ok["final_diagnosis"] = {"diagnosis": "Undifferentiated Acute Medical Illness", "icd10": "",
                             "certainty": "provisional", "confidence": 0.4, "evidence": [_ev()]}
    assert _check(ok, "V5").passed is True


@pytest.mark.unit
def test_v6_rejects_hallucinated_chunk_id() -> None:
    bad = _valid_dict()
    bad["final_diagnosis"]["evidence"] = [_ev("H-FAKE-999", "lobar consolidation with air bronchograms")]
    assert _check(bad, "V6").passed is False
    assert _check(_valid_dict(), "V6").passed is True


@pytest.mark.unit
def test_v7_rejects_fake_and_null_quotes() -> None:
    bad = _valid_dict()
    bad["final_diagnosis"]["evidence"] = [_ev("H-1", "unicorns dancing on the moon tonight")]
    assert _check(bad, "V7").passed is False
    bad2 = _valid_dict()
    bad2["final_diagnosis"]["evidence"] = [{"source": "harrison", "chunk_id": "H-1",
                                            "supporting_quote": None, "note": None}]
    assert _check(bad2, "V7").passed is False
    assert _check(_valid_dict(), "V7").passed is True


@pytest.mark.unit
def test_v8_grounding_minimums_and_fraction() -> None:
    assert _check(_valid_dict(), "V8").passed is True
    bad = _valid_dict()
    bad["final_diagnosis"]["evidence"] = [{"source": "model_knowledge", "chunk_id": None,
                                           "supporting_quote": None, "note": None}]
    assert _check(bad, "V8").passed is False
    thin = _valid_dict()
    mg = {"source": "model_knowledge", "chunk_id": None, "supporting_quote": None, "note": None}
    for section in thin["differential_diagnosis"]:
        section["evidence"] = [mg]
    for section in thin["workup"] + thin["treatment"]:
        section["evidence"] = [mg]
    thin["severity_assessment"][0]["evidence"] = [mg]
    thin["disposition"]["evidence"] = [mg]
    assert _check(thin, "V8").passed is False


@pytest.mark.unit
def test_v9_rejects_unexplained_non_top_final() -> None:
    bad = _valid_dict()
    bad["final_diagnosis"] = {"diagnosis": "Legionella pneumonia", "icd10": "J15.7",
                              "certainty": "probable", "confidence": 0.6, "evidence": [_ev()]}
    assert _check(bad, "V9").passed is False


@pytest.mark.unit
def test_v10_cap_completeness_enforced_and_drafts_audit() -> None:
    assert _check(_valid_dict(), "V10").passed is True
    bad = _valid_dict()
    bad["treatment"] = [{"item": "Bed rest", "dose_route_frequency_duration": "as tolerated",
                         "rationale": "Supportive care.", "evidence": [_ev()]}]
    result = _check(bad, "V10")
    assert result.passed is False and "community_acquired_pneumonia" in result.message
    # Draft rule (ACS) incomplete -> audit-only pass with note.
    acs = _valid_dict()
    acs["final_diagnosis"] = {"diagnosis": "Acute coronary syndrome", "icd10": "I24.9",
                              "certainty": "probable", "confidence": 0.6, "evidence": [_ev()]}
    acs["differential_diagnosis"][0]["diagnosis"] = "Acute coronary syndrome"
    audit = _check(acs, "V10")
    assert audit.passed is True and "audit" in audit.message


@pytest.mark.unit
def test_v12_rejects_copied_paragraph_and_missing_findings() -> None:
    bad = _valid_dict()
    bad["clinical_reasoning"] = ("Preface words here. " + CHUNK_1 + " Trailing clinical note.")
    assert _check(bad, "V12").passed is False
    sparse = {"presenting_symptoms": ["cough"], "vitals": {}, "examination_findings": "",
              "labs": {}, "imaging": {}}
    thin = _valid_dict()
    thin["clinical_reasoning"] = "The presentation is concerning and warrants admission for observation."
    assert _check(thin, "V12", sparse).passed is False
    assert _check(_valid_dict(), "V12").passed is True


# --- Full validation + failure handling ----------------------------------------

@pytest.mark.unit
def test_full_validation_passes_brown_like_report() -> None:
    report = AssessmentReport.model_validate(_valid_dict())
    validation = validate_assessment_report(report, _log(), BROWN_STRUCTURED)
    assert validation.passed is True
    assert len(validation.checks) == 12
    assert validation.harrison_fraction >= 0.6


def _stub_runner_factory(script: List[str]) -> Any:
    calls = {"n": 0}

    def runner(prompt: str, **kwargs: Any) -> str:
        idx = min(calls["n"], len(script) - 1)
        calls["n"] += 1
        return script[idx]

    return runner


def _hit(cid: str, text: str, score: float = 0.5) -> SourceSearchHit:
    return SourceSearchHit(source_name="harrison", chunk_id=cid, metadata={}, text=text, score=score)


@pytest.mark.unit
def test_pipeline_regenerates_with_feedback_then_valid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Failing V4 triggers regeneration with the error list; retry then VALID."""
    monkeypatch.setattr(phase3, "FAILED_LOG_PATH", tmp_path / "failed.jsonl")
    bad = _valid_dict("REP-RETRY")
    bad["chief_complaint"] = "Pneumonia for 3 days"
    good = _valid_dict("REP-RETRY")
    adapter = MedGemmaAdapter(runner=_stub_runner_factory([json.dumps(bad), json.dumps(good)]))
    pipeline = GroundedGenerationPipeline(adapter=adapter)
    result = pipeline.run_grounded_assessment(
        case_id="C-RETRY", specialty="Pulmonology", structured_case=dict(BROWN_STRUCTURED),
        candidate_differentials=["Community-acquired pneumonia"], report_id="REP-RETRY",
        search_fn=lambda q, top_k=6: [_hit("H-1", CHUNK_1), _hit("H-2", CHUNK_2)],
    )
    assert result.metadata["generation_status"] == "VALID"
    assert len(result.metadata["raw_model_output"]) == 2
    assert result.metadata["validation"]["passed"] is True


@pytest.mark.unit
def test_pipeline_failed_after_exhaustion_logged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Persistent V4 failure -> FAILED with stored validation + failed-list entry."""
    monkeypatch.setattr(phase3, "FAILED_LOG_PATH", tmp_path / "failed.jsonl")
    bad = _valid_dict("REP-FAIL")
    bad["chief_complaint"] = "Pneumonia for 3 days"
    adapter = MedGemmaAdapter(runner=_stub_runner_factory([json.dumps(bad)]))
    pipeline = GroundedGenerationPipeline(adapter=adapter)
    result = pipeline.run_grounded_assessment(
        case_id="C-FAIL", specialty="Pulmonology", structured_case=dict(BROWN_STRUCTURED),
        candidate_differentials=["Community-acquired pneumonia"], report_id="REP-FAIL",
        search_fn=lambda q, top_k=6: [_hit("H-1", CHUNK_1)],
    )
    assert result.metadata["generation_status"] == "FAILED"
    assert result.metadata["validation"]["passed"] is False
    assert any(not c["passed"] and c["check_id"] == "V4" for c in result.metadata["validation"]["checks"])
    logged = (tmp_path / "failed.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(logged) == 1
    entry = json.loads(logged[0])
    assert entry["status"] == "FAILED" and entry["report_id"] == "REP-FAIL"
    assert entry["raw_attempts"], "raw outputs stored on the failed list"


@pytest.mark.unit
def test_timeout_attempts_counted_then_recovers() -> None:
    """Timeouts consume retry attempts truthfully instead of vanishing from stats."""
    from vh.generation.medgemma import GenerationTimeoutError

    script = [GenerationTimeoutError("slow"), GenerationTimeoutError("slow"), json.dumps(_valid_dict("REP-TO"))]
    calls = {"n": 0}

    def runner(prompt: str, **kwargs: Any) -> str:
        item = script[min(calls["n"], len(script) - 1)]
        calls["n"] += 1
        if isinstance(item, Exception):
            raise item
        return item

    adapter = MedGemmaAdapter(runner=runner)
    result = adapter.generate_assessment(
        structured_case={}, harrison_context="", retrieval_chunk_ids=["H-1"],
        report_id="REP-TO", case_id="C-TO", candidates=["X"],
    )
    assert result.report.report_id == "REP-TO"
    assert result.parse_stats.attempts == 3


# --- Fail-safe: ungrounded tagging + RL exclusion -------------------------------

@pytest.mark.unit
def test_grounded_failure_raises_not_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Grounded-mode failure raises; the caller tags the legacy fallback ungrounded."""
    monkeypatch.setenv("VH_PIPELINE", "grounded")
    import backend.simulation.grounded_shim as shim

    monkeypatch.setattr(shim, "_pipeline_class", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(shim.GroundedFailedError):
        shim.maybe_grounded_assessment({"chief_complaint": "x"}, {}, {}, [], "C-X")
    monkeypatch.delenv("VH_PIPELINE", raising=False)


@pytest.mark.unit
def test_rl_export_permanently_excludes_ungrounded() -> None:
    """Ungrounded reports never enter the training export."""
    from backend.clinical.models import ClinicalReport, PhysicianReview
    from backend.rl.dpo_generator import DPOPreferenceGenerator

    report = ClinicalReport.model_validate({
        "id": "REP-U1", "encounter_id": "ENC-U1", "patient_id": "P-U1", "patient_name": "Test",
        "patient_age": 50, "patient_sex": "male", "chief_complaint": "cough",
        "history_of_present_illness": "hpi", "vital_signs": {
            "heart_rate": 80, "systolic_bp": 120, "diastolic_bp": 80,
            "respiratory_rate": 16, "temperature_c": 37.0, "spo2_percent": 98},
        "differential_diagnosis": [], "primary_diagnosis": "X", "diagnostic_confidence": 0.5,
        "clinical_reasoning": "r", "treatment_plan": [], "ungrounded": True,
    })
    assert report.ungrounded is True
    review = PhysicianReview.model_validate({
        "id": "REV-U1", "report_id": "REP-U1", "encounter_id": "ENC-U1",
        "diagnosis_grade": "CORRECT", "reasoning_grade": "SOUND", "tests_grade": "APPROPRIATE",
        "treatment_grade": "SAFE_AND_OPTIMAL", "overall_score": 5, "approved": True,
        "physician_feedback_notes": "n",
    })
    pairs = DPOPreferenceGenerator.compile_dpo_corpus({"REP-U1": report}, {"REV-U1": review}, {}, include_calibrations=False)
    assert pairs == [], "ungrounded report must never export"
