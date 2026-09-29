"""
Acceptance tests for Step 23: P3.4 Model Benchmark and No-RAG Baseline.
Verifies No-RAG baseline pipeline execution, RAG superiority over baseline with
bootstrap 95% confidence intervals excluding zero, stability across runs, and reproducibility.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest
import numpy as np

from vh.cases.schema import CaseView, GoldenCase
from vh.generation.pipeline import GroundedGenerationPipeline
from vh.generation.baseline import NoRagBaselinePipeline
from eval.harness.interfaces import Pipeline, PipelineResult

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_V1_DIR = REPO_ROOT / "eval" / "golden" / "v1"


@pytest.fixture
def golden_cases_sample() -> List[GoldenCase]:
    """Loads a representative cohort of verified golden cases."""
    cases: List[GoldenCase] = []
    for f in sorted(GOLDEN_V1_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        cases.append(GoldenCase.model_validate(data))
    return cases[:15]


def test_norag_baseline_pipeline_contract(golden_cases_sample):
    """Verifies that NoRagBaselinePipeline conforms to Pipeline protocol and runs without evidence."""
    pipeline = NoRagBaselinePipeline()
    assert isinstance(pipeline, Pipeline)

    case_view = golden_cases_sample[0].to_case_view()
    result = pipeline.run(case_view)

    assert isinstance(result, PipelineResult)
    assert result.case_id == case_view.case_id
    assert len(result.diagnosis) > 0
    assert result.metadata.get("generation_mode") == "no_rag"
    assert len(result.metadata.get("active_evidence_ids", [])) == 0


def test_grounded_rag_beats_norag_baseline_with_bootstrap_ci(golden_cases_sample):
    """
    Verifies that the Grounded RAG pipeline's top-3 diagnostic accuracy statistically
    beats the No-RAG baseline with a bootstrap 95% confidence interval that strictly excludes zero.
    """
    from eval.harness.scorers.diagnostic import (
        evaluate_diagnostic_accuracy,
        compute_bootstrap_ci_difference,
    )

    rag_pipeline = GroundedGenerationPipeline()
    norag_pipeline = NoRagBaselinePipeline()

    rag_results = []
    norag_results = []

    for gc in golden_cases_sample:
        cv = gc.to_case_view()
        rag_results.append((cv, rag_pipeline.run(cv)))
        norag_results.append((cv, norag_pipeline.run(cv)))

    rag_metrics = evaluate_diagnostic_accuracy(rag_results, golden_cases_sample)
    norag_metrics = evaluate_diagnostic_accuracy(norag_results, golden_cases_sample)

    assert rag_metrics["dx_top3"] > norag_metrics["dx_top3"]

    # Compute bootstrap confidence interval of accuracy difference (RAG - NoRAG)
    ci_low, ci_high = compute_bootstrap_ci_difference(
        rag_results, norag_results, golden_cases_sample, metric="dx_top3", n_bootstrap=500
    )

    # Acceptance criterion: 95% CI strictly excludes zero (lower bound > 0.0)
    assert ci_low > 0.0
    assert ci_high >= ci_low


def test_stability_reproducibility_across_runs(golden_cases_sample):
    """Verifies that grounded generation produces stable top-3 diagnoses across repeated runs."""
    from eval.harness.scorers.diagnostic import compute_differential_agreement

    pipeline = GroundedGenerationPipeline()
    test_cases = golden_cases_sample[:5]

    run1 = [pipeline.run(gc.to_case_view()) for gc in test_cases]
    run2 = [pipeline.run(gc.to_case_view()) for gc in test_cases]
    run3 = [pipeline.run(gc.to_case_view()) for gc in test_cases]

    agreement_1_2 = compute_differential_agreement(run1, run2)
    agreement_2_3 = compute_differential_agreement(run2, run3)

    assert agreement_1_2 >= 0.90
    assert agreement_2_3 >= 0.90
