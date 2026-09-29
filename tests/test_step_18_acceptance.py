"""
Acceptance criteria tests for STEP 18 (P2.5):
Retrieval evaluation against golden set supporting references,
comprehensive scorers unit testing, experiment reproducibility across embedding candidates
and reranking toggles, and verification against retrieval.* governance thresholds.
"""

from pathlib import Path
import json
import pytest
import numpy as np

from vh.cases.schema import CaseView, GoldenCase
from vh.rag.sources.base import SourceDocument
from vh.rag.retrieval import EvidenceItem

# Test scorers imported from eval harness
from eval.harness.scorers.retrieval import (
    compute_recall_at_k,
    compute_reciprocal_rank,
    compute_per_source_recall,
    compute_traceability_rate,
    compute_duplicate_rate,
    compute_stale_count,
    compute_p95_latency,
    build_retrieval_query_from_case_view,
    RetrievalMetrics,
    RetrievalEvaluationHarness,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_scorers_on_known_fixtures():
    """Verify that every retrieval scorer produces mathematically exact results on fixtures."""
    # 1. Recall@k
    targets = {"c1", "c2", "c3"}
    retrieved_1 = ["c1", "c4", "c5", "c6", "c7"]
    assert compute_recall_at_k(targets, retrieved_1, k=1) == pytest.approx(1 / 3)
    assert compute_recall_at_k(targets, retrieved_1, k=5) == pytest.approx(1 / 3)

    retrieved_all = ["c1", "c2", "c3", "c4", "c5"]
    assert compute_recall_at_k(targets, retrieved_all, k=3) == pytest.approx(1.0)
    assert compute_recall_at_k(set(), retrieved_all, k=5) == pytest.approx(1.0)

    # 2. MRR (Mean Reciprocal Rank)
    assert compute_reciprocal_rank(targets, ["c1", "c2"]) == pytest.approx(1.0)  # first item is match: 1/1
    assert compute_reciprocal_rank(targets, ["c9", "c1", "c2"]) == pytest.approx(0.5)  # second item: 1/2
    assert compute_reciprocal_rank(targets, ["c8", "c9", "c1"]) == pytest.approx(1 / 3)  # third item: 1/3
    assert compute_reciprocal_rank(targets, ["c8", "c9"]) == pytest.approx(0.0)  # no match

    # 3. Per-source recall
    source_targets = {
        "guidelines": {"g1", "g2"},
        "dailymed": {"d1"},
    }
    retrieved_items = [
        EvidenceItem(
            chunk_id="g1",
            text="Guideline text 1",
            source="guidelines",
            locator="g.md#1",
            dense_score=0.9,
            bm25_score=10.0,
            rrf_score=0.016,
            rank=1,
            index_version="v1",
        ),
        EvidenceItem(
            chunk_id="x1",
            text="Other text",
            source="pubmed",
            locator="pmid:1",
            dense_score=0.8,
            bm25_score=8.0,
            rrf_score=0.015,
            rank=2,
            index_version="v1",
        ),
    ]
    per_source = compute_per_source_recall(source_targets, retrieved_items)
    assert per_source["guidelines"] == pytest.approx(0.5)
    assert per_source["dailymed"] == pytest.approx(0.0)

    # 4. Traceability rate
    # One resolvable guideline locator, one unresolvable
    guideline_path = "data/sources/guidelines/aha_acc_acs_2023.md"
    tr_items = [
        EvidenceItem(
            chunk_id="t1",
            text="AHA text",
            source="guidelines",
            locator=f"{guideline_path}#1",
            dense_score=0.9,
            bm25_score=10.0,
            rrf_score=0.016,
            rank=1,
            index_version="v1",
        ),
        EvidenceItem(
            chunk_id="t2",
            text="Nonexistent",
            source="guidelines",
            locator="data/sources/nonexistent_file.md#1",
            dense_score=0.8,
            bm25_score=8.0,
            rrf_score=0.015,
            rank=2,
            index_version="v1",
        ),
    ]
    trace_rate = compute_traceability_rate(tr_items, repo_root=REPO_ROOT)
    assert trace_rate == pytest.approx(0.5)

    # 5. Duplicate rate
    dup_items = [
        EvidenceItem(
            chunk_id="c1",
            text="Same content",
            source="guidelines",
            locator="g.md#1",
            dense_score=0.9,
            bm25_score=10.0,
            rrf_score=0.016,
            rank=1,
            index_version="v1",
        ),
        EvidenceItem(
            chunk_id="c1",
            text="Same content",
            source="guidelines",
            locator="g.md#1",
            dense_score=0.9,
            bm25_score=10.0,
            rrf_score=0.016,
            rank=2,
            index_version="v1",
        ),
    ]
    assert compute_duplicate_rate(dup_items) == pytest.approx(0.5)

    # 6. Stale retrieval count
    stale_items = [
        EvidenceItem(
            chunk_id="s1",
            text="Fresh",
            source="guidelines",
            locator="g.md#1",
            dense_score=0.9,
            bm25_score=10.0,
            rrf_score=0.016,
            rank=1,
            index_version="v1",
            superseded_by=None,
        ),
        EvidenceItem(
            chunk_id="s2",
            text="Stale",
            source="guidelines",
            locator="g.md#2",
            dense_score=0.8,
            bm25_score=8.0,
            rrf_score=0.015,
            rank=2,
            index_version="v1",
            superseded_by="v2",
        ),
    ]
    assert compute_stale_count(stale_items) == 1

    # 7. p95 latency
    latencies = [0.01 * i for i in range(1, 101)]  # 0.01 to 1.00
    p95 = compute_p95_latency(latencies)
    assert p95 == pytest.approx(0.9505, abs=0.02)


def test_query_construction_strictly_uses_case_view():
    """Verify that retrieval queries are constructed strictly from CaseView data and not ground truth."""
    case_view = CaseView(
        case_id="TEST-CASE-001",
        specialty="Cardiology",
        patient_ref="PAT-001",
        visible_presentation={
            "chief_complaint": "Acute retrosternal crushing chest pain radiating to left arm",
            "history": "58-year-old male with hypertension and hyperlipidemia presenting with acute onset diaphoresis.",
            "vitals": {"bp": "140/90", "hr": 95},
        }
    )

    query = build_retrieval_query_from_case_view(case_view)
    assert "retrosternal crushing chest pain" in query
    assert "Cardiology" in query or "chest pain" in query
    # Ensure no leakage attributes are queried or required
    assert not hasattr(case_view, "ground_truth")


def test_chunkmap_draft_completeness_and_structure():
    """Verify that eval/golden/v1-chunkmap.json maps all 60 cases and records unmappable references."""
    chunkmap_path = REPO_ROOT / "eval" / "golden" / "v1-chunkmap.json"
    assert chunkmap_path.exists(), "v1-chunkmap.json must be generated"

    data = json.loads(chunkmap_path.read_text(encoding="utf-8"))
    assert data["golden_version"] == "v1"
    assert data["total_cases"] == 60
    assert len(data["case_mappings"]) == 60

    # Ensure unmappable references are documented (e.g. Harrison copyright restriction)
    assert len(data["unmappable_references"]) > 0
    for unmapped in data["unmappable_references"]:
        assert "source" in unmapped
        assert "locator" in unmapped
        assert "reason" in unmapped

    # Check sample case mapping
    sample_case = data["case_mappings"]["GOLDEN-DRAFT-ACS-001"]
    assert len(sample_case["relevant_chunk_ids"]) > 0
    assert any(ref["status"] == "mapped" for ref in sample_case["supporting_references"])


def test_retrieval_experiments_reproducibility():
    """Verify that evaluation experiments are bit-for-bit reproducible given the same run_id."""
    harness = RetrievalEvaluationHarness(repo_root=REPO_ROOT)

    res1 = harness.run_experiment(
        run_id="exp-reproducibility-test",
        embedding_model="biomedical",
        reranker_enabled=False,
        max_cases=10,
    )
    res2 = harness.run_experiment(
        run_id="exp-reproducibility-test",
        embedding_model="biomedical",
        reranker_enabled=False,
        max_cases=10,
    )

    assert res1.metrics.recall_at_10 == pytest.approx(res2.metrics.recall_at_10)
    assert res1.metrics.mrr == pytest.approx(res2.metrics.mrr)
    assert res1.metrics.traceability_rate == pytest.approx(res2.metrics.traceability_rate)
    assert res1.metrics.stale_retrieval_count == res2.metrics.stale_retrieval_count


def test_chosen_configuration_meets_governance_thresholds():
    """Verify that the chosen configuration in ADR-0003 meets all retrieval.* thresholds."""
    harness = RetrievalEvaluationHarness(repo_root=REPO_ROOT)

    # Evaluate chosen configuration across the full golden set
    report = harness.run_evaluation_against_thresholds(
        run_id="eval-retrieval-v1-chosen",
        golden_version="v1",
    )

    metrics = report["metrics"]
    # Check against configs/thresholds.yaml retrieval thresholds
    assert metrics["recall_at_10"]["status"] == "PASS"
    assert metrics["mrr_min"]["status"] == "PASS"
    assert metrics["traceability_rate"]["status"] == "PASS"
    assert metrics["stale_retrieval_count"]["status"] == "PASS"
    assert metrics["p95_latency_s"]["status"] == "PASS"
    assert report["overall_status"] == "PASS"
