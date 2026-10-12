"""
Phase 2 acceptance tests: MedGemma generation settings, v2 output schema,
verbatim system prompt, raw-output persistence, strict parse + retry,
VH_PIPELINE flag, legacy compat adapter and endpoint contracts.

Owner: QA Engineer. Fixture content spec: Medical Expert.
"""

import json
import os
from pathlib import Path

import pytest

from vh.common.prompts import load_prompt_template
from vh.generation import flag as pipeline_flag
from vh.generation.compat import assessment_to_legacy_report
from vh.generation.medgemma import (
    AssessmentResult,
    GenerationFailed,
    MedGemmaAdapter,
    Phase2GenerationConfig,
    contains_forbidden_grounding,
    guided_decoding_available,
    heuristic_assessment,
    heuristic_candidates,
)
from vh.generation.pipeline import GroundedGenerationPipeline
from vh.generation.v2_report import AssessmentReport, validate_assessment
from vh.rag.sources.base import SourceSearchHit

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "phase1" / "charles_brown_realistic.json"


def _ev(chunk_id: str = "HARRISON_P1060_C07") -> dict:
    return {"source": "harrison", "chunk_id": chunk_id, "supporting_quote": "lobar consolidation with air bronchograms", "note": None}


def _valid_v2_dict(report_id: str = "REP-TEST01") -> dict:
    return {
        "report_id": report_id,
        "case_summary": "68-year-old man with 3 days of fever and productive cough. Examination shows right basal crackles with consolidation on CXR.",
        "chief_complaint": "fever and productive cough for 3 days",
        "differential_diagnosis": [
            {"diagnosis": "Community-acquired pneumonia", "icd10": "J18.9", "probability": 0.55,
             "supporting_findings": ["fever", "productive cough", "consolidation"],
             "against_findings": [], "evidence": [_ev()]},
            {"diagnosis": "Acute bronchitis", "icd10": "J20.9", "probability": 0.2,
             "supporting_findings": ["cough"], "against_findings": ["consolidation on CXR"], "evidence": [_ev()]},
            {"diagnosis": "Aspiration pneumonia", "icd10": "J69.0", "probability": 0.1,
             "supporting_findings": ["cough"], "against_findings": ["no aspiration event"], "evidence": [_ev()]},
        ],
        "final_diagnosis": {"diagnosis": "Community-acquired pneumonia", "icd10": "J18.9",
                            "certainty": "probable", "confidence": 0.7, "evidence": [_ev()]},
        "severity_assessment": [{"score_name": "CURB-65",
                                 "components": {"confusion": "no (0)", "urea": "unknown (0)",
                                                "respiratory_rate": "28 (0)", "blood_pressure": "128/78 (0)",
                                                "age_65": "68 (+1)"},
                                 "value": "1", "interpretation": "CURB-65 = 1; ward care.",
                                 "evidence": [_ev()]}],
        "clinical_reasoning": "A 68-year-old man with hypertension presents with a 3-day syndrome of fever and productive cough [H:HARRISON_P1060_C07]. Right basal crackles with consolidation on CXR favour community-acquired pneumonia over bronchitis [H:HARRISON_P1060_C07]. CURB-65 of 1 supports ward admission with oxygen and empiric antibiotics [MG].",
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


def _hit(cid: str, score: float = 0.5, text: str = "lobar consolidation with air bronchograms") -> SourceSearchHit:
    return SourceSearchHit(
        source_name="harrison", chunk_id=cid,
        metadata={"chunk_id": cid, "chapter_title": "126 Pneumonia", "page": 1060},
        text=text, score=score,
    )


# --- Schema -----------------------------------------------------------------

@pytest.mark.unit
def test_v2_schema_accepts_valid_assessment() -> None:
    report = AssessmentReport.model_validate(_valid_v2_dict())
    assert validate_assessment(report) is True
    assert report.prompt_version == "internal_medicine_assessment@1.0.0"


@pytest.mark.unit
def test_v2_schema_rejects_probability_sum_above_one() -> None:
    bad = _valid_v2_dict()
    bad["differential_diagnosis"][0]["probability"] = 0.9
    bad["differential_diagnosis"][1]["probability"] = 0.9
    with pytest.raises(Exception):
        AssessmentReport.model_validate(bad)


@pytest.mark.unit
def test_v2_schema_rejects_confidence_certainty_mismatch() -> None:
    bad = _valid_v2_dict()
    bad["final_diagnosis"]["certainty"] = "provisional"
    bad["final_diagnosis"]["confidence"] = 0.9
    with pytest.raises(Exception):
        AssessmentReport.model_validate(bad)
    bad2 = _valid_v2_dict()
    bad2["final_diagnosis"]["certainty"] = "confirmed"
    bad2["final_diagnosis"]["confidence"] = 0.6
    with pytest.raises(Exception):
        AssessmentReport.model_validate(bad2)


@pytest.mark.unit
def test_heuristic_assessment_is_schema_valid() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    from vh.cases.structured_case import extract_structured_case, structured_case_to_agentview_dict

    structured = structured_case_to_agentview_dict(extract_structured_case(payload["raw_case"]))
    report = heuristic_assessment(
        structured, [_hit("HARRISON_P1060_C07")], "REP-BROWN1", "CASE-BROWN1",
        ["Community-acquired pneumonia", "Acute bronchitis", "Aspiration pneumonia"],
    )
    assert validate_assessment(report) is True
    assert "pneumonia" not in report.chief_complaint.lower() or "fever" in report.chief_complaint.lower()
    assert report.prompt_version == "internal_medicine_assessment@1.0.0"


# --- System prompt + settings ------------------------------------------------

@pytest.mark.unit
def test_system_prompt_verbatim_sections() -> None:
    text = load_prompt_template("internal_medicine_assessment@1.0.0")
    for section in ("SOURCE RULES", "CLINICAL RULES", "OUTPUT RULES", "WRITING STYLE",
                    "[H:chunk_id]", "[MG]", "conflicts_noted", "missing_data",
                    "box_2d", "CURB-65", "Internal Medicine diagnostic reasoning engine"):
        assert section in text, f"prompt missing required section/phrase: {section}"
    assert "box_2d" in text and "never output bounding boxes" in text


@pytest.mark.unit
def test_phase2_generation_settings() -> None:
    cfg = Phase2GenerationConfig()
    assert cfg.temperature == pytest.approx(0.2)
    assert cfg.repetition_penalty == pytest.approx(1.1)
    assert cfg.max_new_tokens >= 4096, "max_tokens must be large enough that output is never truncated"
    assert cfg.max_retries == 2
    assert cfg.differential_max_new_tokens <= 1024, "candidate micro-call must be bounded"
    assert cfg.timeout_s >= 900, "live attempts take minutes; timeout must cover them"
    assert cfg.prompt_version == "internal_medicine_assessment@1.0.0"


@pytest.mark.unit
def test_constrained_decoding_unsupported_uses_strict_parse() -> None:
    """Condition 4: serving stack has no constrained decoding; strict parse + retry applies."""
    assert guided_decoding_available() is False


@pytest.mark.unit
def test_text_only_forbidden_grounding_detected() -> None:
    assert contains_forbidden_grounding('{"box_2d": [1, 2]}') is True
    assert contains_forbidden_grounding('{"diagnosis": "CAP"}') is False
    assert contains_forbidden_grounding('```json\n{}\n```') is True


# --- Strict parse + retry + raw persistence ----------------------------------

def _stub_runner_factory(script: list) -> object:
    calls = {"n": 0}

    def runner(prompt: str, **kwargs: object) -> str:
        idx = min(calls["n"], len(script) - 1)
        calls["n"] += 1
        return script[idx]

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


@pytest.mark.unit
def test_retry_recovers_after_malformed_first_attempt() -> None:
    runner = _stub_runner_factory(["not json at all {{{", json.dumps(_valid_v2_dict("REP-R1"))])
    adapter = MedGemmaAdapter(runner=runner)  # type: ignore[arg-type]
    result = adapter.generate_assessment(
        structured_case={"presenting_symptoms": ["fever"]}, harrison_context="<harrison_chunk></harrison_chunk>",
        retrieval_chunk_ids=["HARRISON_P1060_C07"], report_id="REP-R1", case_id="C-R1",
        candidates=["Community-acquired pneumonia"],
    )
    assert isinstance(result, AssessmentResult)
    assert result.parse_stats.attempts == 2
    assert result.parse_stats.json_failures == 1
    assert len(result.raw_attempts) == 2, "raw outputs stored alongside the parsed report"


@pytest.mark.unit
def test_box2d_output_fails_attempt_and_retries() -> None:
    bad = json.dumps({"clinical_reasoning": "see box_2d [10, 20, 30, 40]"})
    runner = _stub_runner_factory([bad, bad, bad])
    adapter = MedGemmaAdapter(runner=runner)  # type: ignore[arg-type]
    with pytest.raises(GenerationFailed):
        adapter.generate_assessment(
            structured_case={}, harrison_context="", retrieval_chunk_ids=["H-1"],
            report_id="REP-B1", case_id="C-B1", candidates=["X"],
            config=Phase2GenerationConfig(max_retries=2),
        )


@pytest.mark.unit
def test_parse_failure_rate_reported() -> None:
    """Condition 4: measured parse-failure rate on scripted cases (reported, not tuned)."""
    clean = _stub_runner_factory([json.dumps(_valid_v2_dict("REP-C1"))])
    adapter = MedGemmaAdapter(runner=clean)  # type: ignore[arg-type]
    res = adapter.generate_assessment(structured_case={}, harrison_context="",
                                      retrieval_chunk_ids=["H-1"], report_id="REP-C1",
                                      case_id="C-C1", candidates=["X"])
    assert res.parse_stats.json_failures == 0 and res.parse_stats.schema_failures == 0

    doomed = _stub_runner_factory(["{{{{bad"] * 5)
    adapter2 = MedGemmaAdapter(runner=doomed)  # type: ignore[arg-type]
    try:
        adapter2.generate_assessment(structured_case={}, harrison_context="",
                                     retrieval_chunk_ids=["H-1"], report_id="REP-C2",
                                     case_id="C-C2", candidates=["X"])
        failed = False
    except GenerationFailed:
        failed = True
    assert failed is True
    print("\nparse-failure-rate: clean-runner 0/1 failed; adversarial-runner 1/1 failed after 3 attempts")


# --- Grounded pipeline path ---------------------------------------------------

@pytest.mark.unit
def test_grounded_path_stores_raw_and_log(tmp_path: Path) -> None:
    from vh.verification import phase3 as _phase3

    _phase3.FAILED_LOG_PATH, _saved_failed_log = tmp_path / "failed.jsonl", _phase3.FAILED_LOG_PATH
    try:
        runner = _stub_runner_factory([json.dumps(_valid_v2_dict("REP-G1"))])
        adapter = MedGemmaAdapter(runner=runner)  # type: ignore[arg-type]
        pipeline = GroundedGenerationPipeline(adapter=adapter)
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        from vh.cases.structured_case import extract_structured_case, structured_case_to_agentview_dict

        structured = structured_case_to_agentview_dict(extract_structured_case(payload["raw_case"]))
        chunk_text = ("lobar consolidation with air bronchograms suggests bacterial infection "
                      "and curb sixty five score guides admission decisions for ward care")
        result = pipeline.run_grounded_assessment(
            case_id="CASE-BROWN1", specialty="Pulmonology", structured_case=structured,
            candidate_differentials=["Community-acquired pneumonia"],
            report_id="REP-G1",
            search_fn=lambda q, top_k=6: [_hit("HARRISON_P1060_C07", 0.55, chunk_text),
                                          _hit("HARRISON_P1058_C08", 0.4, chunk_text)],
        )
    finally:
        _phase3.FAILED_LOG_PATH = _saved_failed_log
    assert result.metadata["generation_status"] == "VALID"
    assert result.metadata["prompt_version"] == "internal_medicine_assessment@1.0.0"
    assert isinstance(result.metadata["raw_model_output"], list) and result.metadata["raw_model_output"]
    assert all(isinstance(raw, str) for raw in result.metadata["raw_model_output"])
    assert result.metadata["retrieval_log"]["queries"], "retrieval ran before generation"
    assert result.metadata["assessment_report"]["report_id"] == "REP-G1"


@pytest.mark.unit
def test_grounded_path_insufficient_grounding() -> None:
    adapter = MedGemmaAdapter(runner=_stub_runner_factory([json.dumps(_valid_v2_dict())]))
    pipeline = GroundedGenerationPipeline(adapter=adapter)
    result = pipeline.run_grounded_assessment(
        case_id="CASE-X", specialty="Pulmonology",
        structured_case={"presenting_symptoms": ["fever"]},
        candidate_differentials=["Community-acquired pneumonia"],
        search_fn=lambda q, top_k=6: [],
    )
    assert result.metadata["generation_status"] == "insufficient_grounding"
    assert "assessment_report" not in result.metadata


# --- Flag + compat ------------------------------------------------------------

@pytest.mark.unit
def test_pipeline_flag_defaults_legacy_with_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Condition 1: default legacy; grounded opt-in; rollback is a flag change only."""
    monkeypatch.delenv("VH_PIPELINE", raising=False)
    assert pipeline_flag.get_pipeline_mode() == "legacy"
    assert pipeline_flag.is_grounded() is False
    monkeypatch.setenv("VH_PIPELINE", "grounded")
    assert pipeline_flag.is_grounded() is True
    monkeypatch.setenv("VH_PIPELINE", "legacy")
    assert pipeline_flag.is_grounded() is False, "rollback is a flag change only"


@pytest.mark.unit
def test_compat_adapter_covers_frontend_fields() -> None:
    assessment = AssessmentReport.model_validate(_valid_v2_dict("REP-COMPAT"))
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    from vh.cases.structured_case import extract_structured_case, structured_case_to_agentview_dict

    structured = structured_case_to_agentview_dict(extract_structured_case(payload["raw_case"]))
    patient = {"id": "CASE-BROWN1", "name": "Charles Brown", "age": 68, "sex": "male"}
    legacy = assessment_to_legacy_report(assessment, structured, patient, "ENC-1", retrieval_log=None)
    for field in ("id", "encounter_id", "patient_id", "patient_name", "patient_age", "patient_sex",
                  "chief_complaint", "history_of_present_illness", "past_medical_history", "medications",
                  "allergies", "vital_signs", "physical_exam_findings", "investigations_ordered",
                  "investigation_results", "differential_diagnosis", "primary_diagnosis",
                  "diagnostic_confidence", "clinical_reasoning", "treatment_plan",
                  "recommended_disposition", "medical_knowledge_citations"):
        assert field in legacy, f"legacy field missing: {field}"
    assert legacy["primary_diagnosis"] == "Community-acquired pneumonia"
    assert legacy["diagnostic_confidence"] == pytest.approx(0.7)
    assert all(0.0 <= d["likelihood"] <= 1.0 for d in legacy["differential_diagnosis"])
    assert all({"condition", "likelihood", "supporting_points", "opposing_points"} <= set(d)
               for d in legacy["differential_diagnosis"])
    # NOTE: investigations_ordered stays free-text until Phase 4 (backend enum
    # LabTestType cannot be coerced without inventing mappings); the unchanged
    # orchestrator write path still supplies enums, so stored reports validate.


@pytest.mark.unit
def test_live_settings_forwarded_and_schema_in_prompt() -> None:
    """Phase 2 settings reach live generate(); the prompt carries the JSON schema."""
    import numpy as np

    seen: dict = {}

    class FakeEncoding(dict):
        def to(self, *args: object, **kwargs: object) -> "FakeEncoding":
            return self

    class FakeProcessor:
        def apply_chat_template(self, *args: object, **kwargs: object) -> FakeEncoding:
            return FakeEncoding({"input_ids": np.zeros((1, 5), dtype=int)})

        def decode(self, tokens: object, skip_special_tokens: bool = True) -> str:
            return json.dumps(_valid_v2_dict("REP-LIVE-SETTINGS"))

    class FakeModel:
        def generate(self, **kwargs: object) -> list:
            seen.update(kwargs)
            return [np.array([1, 2, 3, 4, 5, 6, 7])]

    class FakeService:
        model = FakeModel()
        processor = FakeProcessor()

    adapter = MedGemmaAdapter(service=FakeService())  # type: ignore[arg-type]
    result = adapter.generate_assessment(
        structured_case={"presenting_symptoms": ["fever"]}, harrison_context="<harrison_chunk>x</harrison_chunk>",
        retrieval_chunk_ids=["H-1"], report_id="REP-LIVE-SETTINGS", case_id="C-LS",
        candidates=["Community-acquired pneumonia"],
    )
    assert result.report.report_id == "REP-LIVE-SETTINGS"
    assert seen["temperature"] == pytest.approx(0.2)
    assert seen["repetition_penalty"] == pytest.approx(1.1)
    assert seen["max_new_tokens"] >= 4096
    assert seen["do_sample"] is True


@pytest.mark.unit
def test_extract_json_prefers_last_balanced_object() -> None:
    """Live-model preamble (thinking + markdown) must not break extraction."""
    from vh.generation.medgemma import extract_json_from_text

    body = json.dumps(_valid_v2_dict("REP-EXT"))
    raw = "<unused94>thought\nSome thinking with { braces } inside.\nAnalysis text.\n" + body + "\nTrailing note."
    assert json.loads(extract_json_from_text(raw))["report_id"] == "REP-EXT"


@pytest.mark.unit
def test_heuristic_candidates_cover_cohorts() -> None:
    assert "Community-acquired pneumonia" in heuristic_candidates({"presenting_symptoms": ["cough"], "examination_findings": "", "labs": {}, "imaging": {}})
    assert "Acute coronary syndrome" in heuristic_candidates({"presenting_symptoms": ["chest pressure"], "examination_findings": "", "labs": {}, "imaging": {}})
    assert "Diabetic ketoacidosis" in heuristic_candidates({"presenting_symptoms": ["polyuria"], "examination_findings": "", "labs": {}, "imaging": {}})


@pytest.mark.unit
def test_heuristic_candidates_cardiac_first_on_mixed_case101() -> None:
    """Regression: CASE-101 (crushing chest pressure + mild dyspnoea) routes cardiac, not pneumonia."""
    candidates = heuristic_candidates(
        {"presenting_symptoms": ["Substernal crushing chest pressure radiating to left arm and jaw for 2 hours"],
         "examination_findings": "diaphoresis, nausea, and mild dyspnea", "labs": {}, "imaging": {}}
    )
    assert candidates[0] == "Acute coronary syndrome"


# --- Endpoint contracts (condition 2: frontend keeps working) ------------------

@pytest.mark.integration
def test_existing_endpoints_keep_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """All pre-existing endpoints respond; slow/generative routes asserted present."""
    monkeypatch.delenv("VH_ALLOW_RL_TRAIN", raising=False)
    monkeypatch.delenv("VH_PIPELINE", raising=False)
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    for url in ("/api/health", "/api/cases", "/api/simulation/events", "/api/reports",
                "/api/reports/pending", "/api/reports/reviewed", "/api/reports/history",
                "/api/reviews/history", "/api/database/status", "/api/patients",
                "/api/knowledge/search?q=fever&top_k=1", "/api/rl/dataset",
                "/api/rl/train/status", "/api/staff", "/api/inpatient/rooms"):
        resp = client.get(url)
        assert resp.status_code == 200, f"{url} -> {resp.status_code}: {resp.text[:200]}"
    resp = client.post("/api/rl/train", json={"epochs": 1, "dry_run": True})
    assert resp.status_code == 503 and "Phase 5" in resp.json().get("detail", "")

    def _all_paths(app: object) -> set:
        found: set = set()
        stack = list(getattr(app, "routes", []))
        while stack:
            route = stack.pop()
            path = getattr(route, "path", "")
            if path:
                found.add(path)
            for attr in ("router", "original_router"):
                nested = getattr(route, attr, None)
                if nested is not None:
                    stack.extend(getattr(nested, "routes", []))
        return found

    routes = _all_paths(app)
    for path in ("/api/simulation/run", "/api/rl/benchmark", "/api/patients/admit",
                 "/api/reviews", "/api/knowledge/seed", "/api/rl/dataset/export",
                 "/api/database/purge-mock-data"):
        assert path in routes, f"route removed: {path}"


@pytest.mark.integration
def test_grounded_shim_rollback_flag_stays_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rollback flag leaves production untouched (shim returns None)."""
    monkeypatch.setenv("VH_PIPELINE", "legacy")
    from backend.simulation.grounded_shim import maybe_grounded_assessment

    assert maybe_grounded_assessment({}, {}, {}, [], "CASE-X") is None


@pytest.mark.integration
def test_grounded_shim_grounded_path_uses_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Grounded flag + stubbed vh path yields a legacy-shaped decision (no network/GPU)."""
    monkeypatch.setenv("VH_PIPELINE", "grounded")
    import backend.simulation.grounded_shim as shim

    calls: dict = {}

    class FakeResult:
        metadata = {
            "generation_status": "VALID",
            "assessment_report": _valid_v2_dict("REP-SHIM"),
            "retrieval_log": {"chunks": {}},
        }

    class FakePipeline:
        def __init__(self, *args: object, **kwargs: object) -> None:
            calls["init"] = True

        def run_grounded_assessment(self, **kwargs: object) -> FakeResult:
            calls["kwargs"] = kwargs
            return FakeResult()

    monkeypatch.setattr(shim, "_pipeline_class", lambda: FakePipeline)
    out = shim.maybe_grounded_assessment(
        {"chief_complaint": "fever", "age": 68, "sex": "male"},
        {"heart_rate": 100}, {"General": "ok"}, [], "CASE-S",
    )
    assert out is not None
    decision, citations = out
    assert decision["primary_diagnosis"] == "Community-acquired pneumonia"
    assert 0.0 <= decision["confidence"] <= 1.0
    assert decision["differential"][0]["condition"] == "Community-acquired pneumonia"
    monkeypatch.delenv("VH_PIPELINE", raising=False)
