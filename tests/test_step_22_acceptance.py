"""
Acceptance tests for Step 22: P3.3 Grounded Generation Pipeline with Abstention.
Verifies the end-to-end grounded generation pipeline, golden-set schema validity,
zero fabricated citations, explicit pre/post-generation abstention, AgentView isolation,
and fail-closed error handling.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from vh.cases.schema import CaseView, GoldenCase
from vh.generation.pipeline import GroundedGenerationPipeline, QueryPlanner
from vh.generation.report import ClinicalReport, validate_clinical_report
from vh.generation.medgemma import GenerationFailed
from eval.harness.interfaces import Pipeline, PipelineResult

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_V1_DIR = REPO_ROOT / "eval" / "golden" / "v1"


@pytest.fixture
def sample_case_view() -> CaseView:
    """Provides a realistic sample CaseView without any hidden ground truth."""
    return CaseView(
        case_id="CASE-101",
        specialty="Cardiology",
        patient_ref="PAT-001",
        visible_presentation={
            "chief_complaint": "Severe retrosternal chest pressure and shortness of breath",
            "history_of_present_illness": (
                "62-year-old male with 3-hour history of acute chest pressure radiating to left arm. "
                "Associated with diaphoresis, dyspnea, and nausea."
            ),
            "vitals": {
                "blood_pressure": "154/92 mmHg",
                "heart_rate": "98 bpm",
                "respiratory_rate": "22 bpm",
                "oxygen_saturation": "96% on room air",
                "temperature": "37.1 C",
            },
            "physical_exam": {
                "general": "Diaphoretic male in moderate distress",
                "cardiovascular": "S4 gallop present, regular rhythm, no murmurs",
                "pulmonary": "Bilateral lung fields clear to auscultation",
            },
            "initial_labs": {
                "high_sensitivity_troponin_i": "480 ng/L (ref < 14)",
                "ecg": "2 mm ST-segment depression in leads II, III, and aVF",
            },
        },
    )


def test_pipeline_implements_protocol_and_schema_valid(sample_case_view):
    """Verifies that GroundedGenerationPipeline implements the Pipeline protocol and produces valid outputs."""
    pipeline = GroundedGenerationPipeline()
    assert isinstance(pipeline, Pipeline)

    result = pipeline.run(sample_case_view)
    assert isinstance(result, PipelineResult)
    assert result.case_id == "CASE-101"
    assert len(result.diagnosis) > 3
    assert len(result.differential) >= 1
    assert result.metadata.get("generation_status") == "success"

    report_dict = result.metadata.get("clinical_report")
    assert report_dict is not None

    report = ClinicalReport.model_validate(report_dict)
    active_evidence = result.metadata.get("active_evidence_ids", [])
    assert len(active_evidence) > 0

    # Strict referential integrity check
    validate_clinical_report(report, valid_evidence_ids=active_evidence)


def test_query_planner_subqueries(sample_case_view):
    """Verifies that the query planner generates sub-queries across clinical dimensions."""
    planner = QueryPlanner()
    plan = planner.plan_queries(sample_case_view)

    assert "presentation" in plan
    assert "differential" in plan
    assert "workup" in plan
    assert "management" in plan
    assert len(plan["differential"]) > 5
    assert len(plan["management"]) > 5


def test_abstention_on_filtered_evidence(sample_case_view):
    """
    Verifies that filtering out key supporting evidence for a clinical domain (management)
    triggers pre-generation or prompt abstention, producing an explicit abstention item
    and zero ungrounded recommendations on that specific topic.
    """
    # Create pipeline that explicitly drops management chunks from retrieval
    pipeline = GroundedGenerationPipeline(suppress_management_evidence=True)

    result = pipeline.run(sample_case_view)
    assert result.metadata.get("generation_status") in ("success", "abstained_partial")

    report = ClinicalReport.model_validate(result.metadata["clinical_report"])
    assert len(report.abstentions) >= 1

    # An abstention must document missing management evidence
    management_abstentions = [
        a for a in report.abstentions
        if "management" in a.question.lower() or "therapy" in a.question.lower() or "insufficient" in a.reason.lower()
    ]
    assert len(management_abstentions) >= 1

    # Recommendations must not contain ungrounded claims
    for rec in report.recommendations:
        for cid in rec.claim_ids:
            claim = next((c for c in report.claims if c.claim_id == cid), None)
            assert claim is not None
            for eid in claim.evidence_ids:
                assert eid in result.metadata["active_evidence_ids"]


def test_agentview_isolation_leakage(sample_case_view):
    """Verifies zero leakage of hidden ground truth into pipeline prompts, inputs, or results."""
    # Ensure sample CaseView has zero hidden keys
    assert not hasattr(sample_case_view, "ground_truth")
    assert not hasattr(sample_case_view, "hidden_records")

    pipeline = GroundedGenerationPipeline()
    result = pipeline.run(sample_case_view)

    serialized_result = json.dumps(result.model_dump()).lower()
    forbidden_leakage_terms = ["ground_truth", "hidden_findings", "secret_key", "agentview_leak"]
    for term in forbidden_leakage_terms:
        assert term not in serialized_result


def test_post_generation_failure_sets_status(sample_case_view):
    """Verifies that complete generation failure sets status to generation_failed without crashing or dropping silently."""
    def always_failing_runner(prompt: str, **kwargs: Any) -> str:
        return "malformed { unparseable"

    pipeline = GroundedGenerationPipeline(runner=always_failing_runner)
    result = pipeline.run(sample_case_view)

    assert result.metadata.get("generation_status") == "generation_failed"
    assert result.diagnosis == "Generation Failed"
    assert "error" in result.metadata


def test_golden_generation_metrics():
    """Verifies generation.schema_valid_rate and generation.fabricated_citation_rate on golden set."""
    from eval.harness.scorers.generation import GenerationScorer

    golden_cases: List[GoldenCase] = []
    for f in sorted(GOLDEN_V1_DIR.glob("*.json"))[:5]:
        if f.name == "manifest.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        golden_cases.append(GoldenCase.model_validate(data))

    assert len(golden_cases) >= 3

    pipeline = GroundedGenerationPipeline()
    results = []
    for gc in golden_cases:
        case_view = gc.to_case_view()
        out = pipeline.run(case_view)
        results.append((case_view, out))

    scorer = GenerationScorer()
    scores = scorer.score(results, golden_cases)

    # Assert against thresholds.yaml requirements
    assert scores["schema_valid_rate"] == 1.0
    assert scores["fabricated_citation_rate"] == 0.0
    assert scores["abstention_correct_rate"] >= 0.90

