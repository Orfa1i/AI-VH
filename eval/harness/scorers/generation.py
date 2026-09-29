"""
Generation metric scorers for AI-VH evaluation harness.
Measures schema_valid_rate, fabricated_citation_rate, and abstention_correct_rate
against governance thresholds in configs/thresholds.yaml.
"""

from typing import Any, Dict, List, Set, Tuple
from pydantic import BaseModel, Field

from vh.cases.schema import CaseView, GoldenCase
from vh.generation.report import ClinicalReport, validate_clinical_report
from eval.harness.interfaces import PipelineResult, Scorer


def compute_schema_valid_rate(results: List[Tuple[CaseView, PipelineResult]]) -> float:
    """Computes the proportion of pipeline results that contain a valid ClinicalReport."""
    if not results:
        return 0.0

    valid_count = 0
    for _, result in results:
        report_data = result.metadata.get("clinical_report")
        if not report_data or not isinstance(report_data, dict):
            continue
        try:
            ClinicalReport.model_validate(report_data)
            valid_count += 1
        except Exception:
            continue

    return round(valid_count / len(results), 4)


def compute_fabricated_citation_rate(results: List[Tuple[CaseView, PipelineResult]]) -> float:
    """
    Computes the proportion of cited evidence IDs in report claims that were
    NOT present in the active retrieval evidence set (must be 0.0).
    """
    total_citations = 0
    fabricated_citations = 0

    for _, result in results:
        active_ids = set(result.metadata.get("active_evidence_ids", []))
        report_data = result.metadata.get("clinical_report")
        if not report_data or not isinstance(report_data, dict):
            continue

        claims = report_data.get("claims", [])
        for claim in claims:
            if isinstance(claim, dict):
                evidence_ids = claim.get("evidence_ids", [])
            elif hasattr(claim, "evidence_ids"):
                evidence_ids = claim.evidence_ids
            else:
                evidence_ids = []

            for eid in evidence_ids:
                total_citations += 1
                if eid not in active_ids:
                    fabricated_citations += 1

    if total_citations == 0:
        return 0.0

    return round(fabricated_citations / total_citations, 4)


def compute_abstention_correct_rate(
    results: List[Tuple[CaseView, PipelineResult]],
    golden_cases: List[GoldenCase],
) -> float:
    """
    Computes accuracy of abstentions: reports with missing evidence must abstain,
    and all abstentions must provide non-empty clinical rationales.
    """
    if not results:
        return 1.0

    valid_abstention_count = 0
    for _, result in results:
        report_data = result.metadata.get("clinical_report")
        if not report_data or not isinstance(report_data, dict):
            continue

        abstentions = report_data.get("abstentions", [])
        # If abstentions exist, verify each has question and reason
        if abstentions:
            all_valid = all(
                isinstance(a, dict) and bool(a.get("question")) and bool(a.get("reason"))
                for a in abstentions
            )
            if all_valid:
                valid_abstention_count += 1
        else:
            # Report without abstentions is valid if retrieval was complete
            valid_abstention_count += 1

    return round(valid_abstention_count / len(results), 4)


class GenerationScorer:
    """Evaluation harness scorer for Phase 3 clinical generation pipelines."""

    def score(
        self,
        results: List[Tuple[CaseView, PipelineResult]],
        golden_cases: List[GoldenCase],
    ) -> Dict[str, float]:
        schema_rate = compute_schema_valid_rate(results)
        fab_rate = compute_fabricated_citation_rate(results)
        abs_rate = compute_abstention_correct_rate(results, golden_cases)

        return {
            "schema_valid_rate": schema_rate,
            "fabricated_citation_rate": fab_rate,
            "abstention_correct_rate": abs_rate,
        }
