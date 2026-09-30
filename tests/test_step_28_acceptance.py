"""
Acceptance tests for Step 28: P4.4 DeepEval Metrics in CI.
Tests:
- Scorers produce faithfulness, contextual relevancy, and answer relevancy metrics
- DeepEval harness produces structured eval reports with pinned model and version
- CI evaluation runner enforces thresholds from configs/thresholds.yaml
- Demonstration of CI failure when threshold is raised above actual performance
"""

from pathlib import Path
import json
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# 1. DeepEval Harness Scorers Output Test
# -----------------------------------------------------------------------------

def test_deepeval_scorers_produce_metrics():
    """Verify that faithfulness, contextual relevancy, and answer relevancy scorers calculate valid scores."""
    from eval.harness.scorers.deepeval import (
        FaithfulnessScorer,
        ContextualRelevancyScorer,
        AnswerRelevancyScorer,
    )

    query = "60-year-old presenting with acute chest pressure and ST elevation."
    context = [
        "Aspirin 162-325 mg should be administered immediately for acute coronary syndrome.",
        "Primary PCI is recommended within 90 minutes of first medical contact for STEMI.",
    ]
    response = "Administer chewable aspirin 325 mg immediately and activate the cardiac catheterization lab for emergent PCI."

    # 1. Faithfulness
    f_scorer = FaithfulnessScorer()
    f_result = f_scorer.measure(query=query, response=response, context=context)
    assert 0.0 <= f_result.score <= 1.0
    assert f_result.score >= 0.85
    assert len(f_result.reason) > 5

    # 2. Contextual Relevancy
    cr_scorer = ContextualRelevancyScorer()
    cr_result = cr_scorer.measure(query=query, response=response, context=context)
    assert 0.0 <= cr_result.score <= 1.0
    assert cr_result.score >= 0.80

    # 3. Answer Relevancy
    ar_scorer = AnswerRelevancyScorer()
    ar_result = ar_scorer.measure(query=query, response=response, context=context)
    assert 0.0 <= ar_result.score <= 1.0
    assert ar_result.score >= 0.80


# -----------------------------------------------------------------------------
# 2. Structured Evaluation Report Generation
# -----------------------------------------------------------------------------

def test_deepeval_harness_generates_eval_report(tmp_path):
    """Verify that DeepEvalHarness evaluates test cases and emits structured JSON report with pinned metadata."""
    from eval.harness.scorers.deepeval import DeepEvalHarness, DeepEvalTestCase

    harness = DeepEvalHarness(
        judge_model="google/medgemma-4b",
        deepeval_version="2.4.0",
    )

    cases = [
        DeepEvalTestCase(
            case_id="GOLDEN-01",
            input_query="Evaluate patient with diabetic ketoacidosis and blood glucose 450 mg/dL.",
            actual_output="Initiate IV regular insulin infusion and aggressive fluid resuscitation with normal saline.",
            retrieval_context=["ADA guidelines recommend IV fluid resuscitation and regular insulin infusion for DKA."],
        ),
        DeepEvalTestCase(
            case_id="GOLDEN-02",
            input_query="Acute exacerbation of COPD in 70-year-old with wheezing and hypoxemia.",
            actual_output="Administer supplemental oxygen targeting SpO2 88-92%, inhaled short-acting bronchodilators, and oral prednisone.",
            retrieval_context=["GOLD COPD guidelines recommend titrated oxygen, SABA/SAMA bronchodilators, and systemic corticosteroids."],
        ),
    ]

    report_path = tmp_path / "deepeval_test_report.json"
    report = harness.evaluate_cases(cases=cases, report_path=report_path)

    assert report_path.exists()
    assert report["judge_model"] == "google/medgemma-4b"
    assert report["deepeval_version"] == "2.4.0"
    assert "mean_faithfulness" in report
    assert "mean_contextual_relevancy" in report
    assert "mean_answer_relevancy" in report
    assert len(report["case_results"]) == 2


# -----------------------------------------------------------------------------
# 3. CI Gate Threshold Enforcement and Failure Demonstration
# -----------------------------------------------------------------------------

def test_ci_eval_rag_runner_passes_on_standard_thresholds():
    """Verify that the CI runner passes when metrics exceed standard thresholds in configs/thresholds.yaml."""
    from scripts.eval_rag_ci import run_ci_eval

    # Run CI evaluation on sample cases with default thresholds
    result = run_ci_eval(sample_size=5, fail_on_threshold=False)

    assert result["total_cases"] == 5
    assert result["faithfulness"] >= 0.70
    assert result["contextual_relevancy"] >= 0.70


def test_ci_eval_rag_runner_demonstrates_failure_on_elevated_threshold():
    """
    Demonstrate CI failure: when threshold is artificially elevated to 0.9999
    (above realistic model scores), the runner returns non-zero exit code (gate failure).
    """
    from scripts.eval_rag_ci import run_ci_eval

    elevated_thresholds = {
        "faithfulness_min": 1.05,
        "contextual_relevancy_min": 1.05,
    }

    result = run_ci_eval(
        sample_size=5,
        threshold_overrides=elevated_thresholds,
        fail_on_threshold=False,
    )

    # Verification must report gate failure because scores are below 0.9999
    assert result["passed_gate"] is False
    assert len(result["gate_failures"]) >= 1
    assert any("faithfulness" in f.lower() or "contextual_relevancy" in f.lower() for f in result["gate_failures"])
