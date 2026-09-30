"""
A/B evaluation: RAG-only vs KG-augmented retrieval (STEP 52 / P9.2).

Methodology mirrors the STEP-18 harness on the same golden set, corpus, and
scorers; only the retrieval arm differs. Adoption requires strict primary
improvement with no safety regression, otherwise the flag stays off.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from eval.harness.scorers.retrieval import (
    RetrievalEvaluationHarness,
    build_retrieval_query_from_case_view,
    compute_duplicate_rate,
    compute_reciprocal_rank,
    compute_p95_latency,
    compute_recall_at_k,
    compute_stale_count,
    compute_traceability_rate,
)
from vh.cases.schema import GoldenCase

from .build import REPO_ROOT, build_graph
from .retrieval import reachable_chunk_ids

MetricPair = Tuple[float, float]


def _score_arm(
    harness: RetrievalEvaluationHarness,
    use_kg: bool,
    golden_version: str,
    max_cases: Optional[int],
) -> Dict[str, Any]:
    from vh.rag.retrieval import UnifiedRetrievalService

    index = harness._get_or_build_index("biomedical")
    service = UnifiedRetrievalService(index=index)
    graph = build_graph(harness.repo_root) if use_kg else None

    chunkmap_path = harness.repo_root / "eval" / "golden" / f"{golden_version}-chunkmap.json"
    chunkmap = json.loads(chunkmap_path.read_text(encoding="utf-8"))
    case_mappings = chunkmap["case_mappings"]
    golden_dir = harness.repo_root / "eval" / "golden" / golden_version

    recall_10: List[float] = []
    mrr: List[float] = []
    latencies: List[float] = []
    all_items: List[Any] = []
    evaluated = 0
    for path in sorted(golden_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        if max_cases is not None and evaluated >= max_cases:
            break
        data = json.loads(path.read_text(encoding="utf-8"))
        gcase = GoldenCase(**data)
        query = build_retrieval_query_from_case_view(gcase.to_case_view())
        relevant = set(case_mappings.get(gcase.case_id, {}).get("relevant_chunk_ids", []))

        started = time.perf_counter()
        items = service.retrieve(query=query, k=10)
        if use_kg and graph is not None:
            items = _apply_kg_arm(items, query, graph, index, k=10)
        latencies.append(time.perf_counter() - started)
        evaluated += 1

        retrieved = [item.chunk_id for item in items]
        all_items.extend(items)
        recall_10.append(compute_recall_at_k(relevant, retrieved, k=10))
        mrr.append(compute_reciprocal_rank(relevant, retrieved))

    return {
        "n_cases": evaluated,
        "recall_at_10": float(sum(recall_10) / len(recall_10)) if recall_10 else 0.0,
        "mrr": float(sum(mrr) / len(mrr)) if mrr else 0.0,
        "traceability": compute_traceability_rate(all_items, repo_root=harness.repo_root),
        "duplicate_rate": compute_duplicate_rate(all_items),
        "stale_count": compute_stale_count(all_items),
        "p95_latency_s": compute_p95_latency(latencies),
    }


def _apply_kg_arm(items: List[Any], query: str, graph: Any, index: Any, k: int) -> List[Any]:
    """Same merge as retrieve_with_kg, factored for the harness loop."""
    from vh.rag.retrieval import EvidenceItem

    reachable = reachable_chunk_ids(query, graph)
    reachable_set = set(reachable)
    for item in items:
        if item.chunk_id in reachable_set:
            item.scores["kg_boost"] = 0.5
            item.metadata["kg_expansion"] = True
    ordered = sorted(
        items,
        key=lambda item: (item.scores.get("rrf", 0.0) + item.scores.get("kg_boost", 0.0), item.chunk_id or ""),
        reverse=True,
    )
    present = {item.chunk_id for item in ordered}
    idx_ver = index.manifest.index_version if index.manifest else "v1.0"
    appended = 0
    for chunk_id in reachable:
        if chunk_id in present or appended >= 2:
            continue
        rec = index.records.get(chunk_id)
        if rec is None:
            continue
        chunk = rec["chunk"]
        ordered.append(
            EvidenceItem(
                evidence_id=f"{idx_ver}:{chunk_id}",
                chunk_id=chunk_id,
                text=chunk.text,
                source=chunk.parent_metadata.get("source_id", "unknown"),
                locator=chunk.locator,
                scores={"kg": 1.0},
                metadata={**dict(chunk.parent_metadata), "kg_expansion": True},
            )
        )
        appended += 1
    for rank, item in enumerate(ordered[:k], start=1):
        item.rank = rank
    return ordered[:k]


def decide_adoption(pairs: Dict[str, MetricPair]) -> str:
    """Adopt only on strict primary improvement with zero safety regression."""
    recall_base, recall_kg = pairs["recall_at_10"]
    mrr_base, mrr_kg = pairs["mrr"]
    stale_base, stale_kg = pairs["stale_count"]
    trace_base, trace_kg = pairs["traceability"]
    improved = recall_kg > recall_base or mrr_kg > mrr_base
    no_regression = (
        recall_kg >= recall_base
        and mrr_kg >= mrr_base
        and stale_kg <= stale_base
        and trace_kg >= trace_base
    )
    return "adopt" if (improved and no_regression) else "reject"


def run_ab_comparison(
    repo_root: Optional[Path] = None, max_cases: Optional[int] = None
) -> Dict[str, Any]:
    """Run both arms over the golden set and decide. Fully deterministic."""
    root = Path(repo_root) if repo_root else REPO_ROOT
    harness = RetrievalEvaluationHarness(repo_root=root)
    rag_only = _score_arm(harness, use_kg=False, golden_version="v1", max_cases=max_cases)
    kg = _score_arm(harness, use_kg=True, golden_version="v1", max_cases=max_cases)
    pairs = {
        "recall_at_10": (rag_only["recall_at_10"], kg["recall_at_10"]),
        "mrr": (rag_only["mrr"], kg["mrr"]),
        "stale_count": (rag_only["stale_count"], kg["stale_count"]),
        "traceability": (rag_only["traceability"], kg["traceability"]),
    }
    return {
        "n_cases": rag_only["n_cases"],
        "rag_only": rag_only,
        "kg": kg,
        "pairs": {key: list(value) for key, value in pairs.items()},
        "decision": decide_adoption(pairs),
    }
