"""
Evaluation scorers and benchmarking harness for clinical retrieval.
Evaluates Recall@5, Recall@10, MRR, per-source recall, traceability rate,
duplicate rate, stale retrieval count, and p95 latency against golden cases.
"""

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field

from vh.cases.schema import CaseView, GoldenCase
from vh.rag.sources.base import SourceDocument
from vh.rag.sources.guidelines import LocalGuidelinesAdapter
from vh.rag.chunking import ChunkerConfig, StructureAwareChunker, Chunk
from vh.rag.indexing import (
    VersionedHybridIndex,
    BiomedicalEmbeddingModel,
    GeneralEmbeddingModel,
    get_embedding_model,
)
from vh.rag.retrieval import (
    EvidenceItem,
    RetrievalFilters,
    RetrievalRequest,
    UnifiedRetrievalService,
    CrossEncoderReranker,
    resolve_locator,
)
from eval.harness.runner import evaluate_metrics_against_thresholds

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class RetrievalMetrics(BaseModel):
    """Structured metric outputs for clinical retrieval evaluation."""
    recall_at_5: float = Field(..., description="Proportion of relevant chunks retrieved in top 5")
    recall_at_10: float = Field(..., description="Proportion of relevant chunks retrieved in top 10")
    mrr: float = Field(..., description="Mean Reciprocal Rank across queries")
    per_source_recall: Dict[str, float] = Field(default_factory=dict, description="Recall breakdown by knowledge source")
    traceability_rate: float = Field(..., description="Proportion of retrieved items resolvable to valid source text")
    duplicate_rate: float = Field(..., description="Proportion of duplicate chunk IDs in retrieved results")
    stale_retrieval_count: int = Field(..., description="Count of retrieved items superseded by newer versions")
    p95_latency_s: float = Field(..., description="95th percentile query latency in seconds")
    total_queries: int = Field(..., description="Total number of evaluated queries")


class ExperimentResult(BaseModel):
    """Reproducible result container for a retrieval configuration experiment."""
    run_id: str
    embedding_model: str
    reranker_enabled: bool
    metrics: RetrievalMetrics
    timestamp: str
    cases_evaluated: int


def compute_recall_at_k(relevant_chunk_ids: Set[str], retrieved_chunk_ids: List[str], k: int) -> float:
    """
    Calculate Recall@k.
    If no relevant target chunks are defined, recall is 1.0.
    """
    if not relevant_chunk_ids:
        return 1.0
    top_k_set = set(retrieved_chunk_ids[:k])
    hits = len(relevant_chunk_ids.intersection(top_k_set))
    return float(hits / len(relevant_chunk_ids))


def compute_reciprocal_rank(relevant_chunk_ids: Set[str], retrieved_chunk_ids: List[str]) -> float:
    """
    Calculate reciprocal rank (1/rank) for the highest-ranked relevant chunk in retrieved items.
    If no relevant item is retrieved, returns 0.0.
    If no relevant target chunks exist, returns 1.0.
    """
    if not relevant_chunk_ids:
        return 1.0
    for rank, cid in enumerate(retrieved_chunk_ids, start=1):
        if cid in relevant_chunk_ids:
            return float(1.0 / rank)
    return 0.0


def compute_per_source_recall(
    relevant_by_source: Dict[str, Set[str]],
    retrieved_items: List[EvidenceItem]
) -> Dict[str, float]:
    """
    Calculate recall broken down by knowledge source repository.
    """
    results: Dict[str, float] = {}
    for src, target_cids in relevant_by_source.items():
        if not target_cids:
            results[src] = 1.0
            continue
        retrieved_ids = [item.chunk_id for item in retrieved_items if item.source == src]
        hits = len(target_cids.intersection(set(retrieved_ids)))
        results[src] = float(hits / len(target_cids))
    return results


def compute_traceability_rate(
    retrieved_items: List[EvidenceItem],
    repo_root: Optional[Path] = None
) -> float:
    """
    Calculate the proportion of retrieved evidence items whose locators
    successfully resolve to a physical source document on disk.
    """
    if not retrieved_items:
        return 1.0
    root = repo_root or REPO_ROOT
    valid_count = 0
    for item in retrieved_items:
        clean_path = item.locator.split("#")[0]
        p = Path(clean_path)
        if (root / clean_path).exists() or p.exists():
            valid_count += 1
    return float(valid_count / len(retrieved_items))


def compute_duplicate_rate(retrieved_items: List[EvidenceItem]) -> float:
    """
    Calculate duplicate rate: proportion of redundant chunk IDs in retrieved results.
    """
    if not retrieved_items:
        return 0.0
    cids = [item.chunk_id for item in retrieved_items]
    unique_cids = set(cids)
    duplicates = len(cids) - len(unique_cids)
    return float(duplicates / len(cids))


def compute_stale_count(retrieved_items: List[EvidenceItem]) -> int:
    """
    Count total retrieved items that are superseded or inactive.
    """
    return sum(1 for item in retrieved_items if item.superseded_by is not None)


def compute_p95_latency(latencies: List[float]) -> float:
    """
    Calculate 95th percentile latency in seconds.
    """
    if not latencies:
        return 0.0
    return float(np.percentile(latencies, 95))


def build_retrieval_query_from_case_view(case_view: CaseView, template: str = "diagnostic_workup") -> str:
    """
    Constructs retrieval query strictly from CaseView visible presentation data.
    Never inspects ground-truth or hidden diagnostic findings.
    """
    pres = case_view.visible_presentation
    chief = pres.get("chief_complaint", "")
    history = pres.get("history", "")
    specialty = case_view.specialty

    if template == "diagnostic_workup":
        return f"{specialty}: {chief}. {history}".strip()
    elif template == "specialty_guideline":
        return f"clinical practice guidelines and evidence-based workup for {specialty}: {chief}".strip()
    else:
        return f"{specialty}: {chief}. {history}".strip()


def generate_v1_chunkmap(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate the official draft chunk mapping between golden set v1 supporting references
    and current indexed chunks, recording unmappable references for H2 review.
    """
    root = repo_root or REPO_ROOT
    golden_dir = root / "eval" / "golden" / "v1"

    # Ingest guidelines to identify canonical chunk IDs
    guidelines_dir = root / "data" / "sources" / "guidelines"
    adapter = LocalGuidelinesAdapter(guidelines_dir)
    guideline_docs = adapter.load_all()
    chunker = StructureAwareChunker()

    doc_to_chunks: Dict[str, List[str]] = {}
    for d in guideline_docs:
        chunks = chunker.chunk_document(d)
        doc_to_chunks.setdefault(d.doc_id, []).extend([c.chunk_id for c in chunks])

    # Map references to document IDs
    ref_to_doc_id = {
        "PMID: 34709979": "GUIDELINE-ACS-2023",
        "ACC/AHA Guideline for Chest Pain": "GUIDELINE-ACS-2023",
        "PMID: 31573350": "GUIDELINE-CAP-2019",
        "ATS/IDSA Community-Acquired Pneumonia Guidelines": "GUIDELINE-CAP-2019",
        "PMID: 38078642": "GUIDELINE-DKA-2024",
        "ADA Standards of Care in Diabetes": "GUIDELINE-DKA-2024",
    }

    unmappable_list = [
        {
            "source": "Harrison's Principles of Internal Medicine",
            "locator": "Chapter 269: ST-Segment Elevation Myocardial Infarction",
            "reason": "Textbook copyright restriction (McGraw-Hill) noted in H0.1 signoff; full text excluded from open-access ingestion",
        },
        {
            "source": "Harrison's Principles of Internal Medicine",
            "locator": "Chapter 121: Pneumonia",
            "reason": "Textbook copyright restriction (McGraw-Hill) noted in H0.1 signoff; full text excluded from open-access ingestion",
        },
        {
            "source": "Harrison's Principles of Internal Medicine",
            "locator": "Chapter 396: Diabetes Mellitus: Complications",
            "reason": "Textbook copyright restriction (McGraw-Hill) noted in H0.1 signoff; full text excluded from open-access ingestion",
        },
    ]

    case_mappings: Dict[str, Any] = {}
    for case_file in sorted(golden_dir.glob("*.json")):
        if case_file.name == "manifest.json":
            continue
        data = json.loads(case_file.read_text(encoding="utf-8"))
        case_id = data["case_id"]
        specialty = data.get("specialty", "")
        refs = data.get("supporting_references", [])

        mapped_refs = []
        relevant_chunks: Set[str] = set()

        for r in refs:
            src = r.get("source", "")
            loc = r.get("locator", "")

            # Check if mappable to guideline document
            doc_id = None
            if loc in ref_to_doc_id:
                doc_id = ref_to_doc_id[loc]
            elif src in ref_to_doc_id:
                doc_id = ref_to_doc_id[src]

            if doc_id and doc_id in doc_to_chunks:
                matched_cids = doc_to_chunks[doc_id]
                relevant_chunks.update(matched_cids)
                mapped_refs.append({
                    "source": src,
                    "locator": loc,
                    "status": "mapped",
                    "matched_doc_id": doc_id,
                    "matched_chunk_ids": matched_cids,
                })
            else:
                mapped_refs.append({
                    "source": src,
                    "locator": loc,
                    "status": "unmappable",
                    "reason": "Textbook copyright restriction (McGraw-Hill) noted in H0.1 signoff",
                })

        case_mappings[case_id] = {
            "specialty": specialty,
            "supporting_references": mapped_refs,
            "relevant_chunk_ids": sorted(list(relevant_chunks)),
        }

    chunkmap_data = {
        "golden_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "draft_for_h2_review",
        "total_cases": len(case_mappings),
        "mapped_cases": len(case_mappings),
        "case_mappings": case_mappings,
        "unmappable_references": unmappable_list,
    }

    out_file = root / "eval" / "golden" / "v1-chunkmap.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(chunkmap_data, indent=2), encoding="utf-8")
    return chunkmap_data


class RetrievalEvaluationHarness:
    """
    Harness for evaluating retrieval configurations across golden sets,
    running reproducible experiments, and asserting metric compliance against thresholds.
    """
    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root or REPO_ROOT)
        self.guidelines_dir = self.repo_root / "data" / "sources" / "guidelines"
        self._ensure_chunkmap()

        # Ingest and cache chunks
        adapter = LocalGuidelinesAdapter(self.guidelines_dir)
        docs = adapter.load_all()
        chunker = StructureAwareChunker(config=ChunkerConfig(target_chunk_tokens=256, max_chunk_tokens=384))
        self.chunks: List[Chunk] = []
        for d in docs:
            self.chunks.extend(chunker.chunk_document(d))

        self._cached_indexes: Dict[str, VersionedHybridIndex] = {}

    def _ensure_chunkmap(self) -> None:
        chunkmap_path = self.repo_root / "eval" / "golden" / "v1-chunkmap.json"
        if not chunkmap_path.exists():
            generate_v1_chunkmap(self.repo_root)

    def _get_or_build_index(self, embedding_model_name: str) -> VersionedHybridIndex:
        if embedding_model_name in self._cached_indexes:
            return self._cached_indexes[embedding_model_name]

        model = get_embedding_model(embedding_model_name)
        index = VersionedHybridIndex(
            index_id=f"eval_index_{embedding_model_name}",
            storage_dir=self.repo_root / "data" / "cache" / f"index_{embedding_model_name}",
        )
        index.build(chunks=self.chunks, embedding_model=model, index_version="v1.0")
        self._cached_indexes[embedding_model_name] = index
        return index

    def run_experiment(
        self,
        run_id: str,
        embedding_model: str = "biomedical",
        reranker_enabled: bool = False,
        golden_version: str = "v1",
        max_cases: Optional[int] = None,
    ) -> ExperimentResult:
        """
        Execute a deterministic retrieval experiment across golden cases and compute all scorers.
        """
        index = self._get_or_build_index(embedding_model)
        reranker = CrossEncoderReranker(enabled=reranker_enabled)
        service = UnifiedRetrievalService(index=index, reranker=reranker)

        # Load chunkmap
        chunkmap_path = self.repo_root / "eval" / "golden" / f"{golden_version}-chunkmap.json"
        chunkmap = json.loads(chunkmap_path.read_text(encoding="utf-8"))
        case_mappings = chunkmap["case_mappings"]

        # Load golden cases
        golden_dir = self.repo_root / "eval" / "golden" / golden_version
        golden_files = sorted(golden_dir.glob("*.json"))

        evaluated_cases = 0
        recall_5_list: List[float] = []
        recall_10_list: List[float] = []
        mrr_list: List[float] = []
        latencies: List[float] = []
        all_retrieved_items: List[EvidenceItem] = []
        source_targets_agg: Dict[str, Set[str]] = {}

        for f in golden_files:
            if f.name == "manifest.json":
                continue
            if max_cases is not None and evaluated_cases >= max_cases:
                break

            data = json.loads(f.read_text(encoding="utf-8"))
            gcase = GoldenCase(**data)
            case_view = gcase.to_case_view()
            query = build_retrieval_query_from_case_view(case_view)

            mapping = case_mappings.get(gcase.case_id, {})
            relevant_chunk_ids = set(mapping.get("relevant_chunk_ids", []))

            # Measure latency
            t0 = time.perf_counter()
            items = service.retrieve(
                query=query,
                k=10,
                rerank=reranker_enabled,
                include_superseded=False,
            )
            lat = time.perf_counter() - t0
            latencies.append(lat)
            evaluated_cases += 1

            retrieved_cids = [item.chunk_id for item in items]
            all_retrieved_items.extend(items)

            r5 = compute_recall_at_k(relevant_chunk_ids, retrieved_cids, k=5)
            r10 = compute_recall_at_k(relevant_chunk_ids, retrieved_cids, k=10)
            recip_rank = compute_reciprocal_rank(relevant_chunk_ids, retrieved_cids)

            recall_5_list.append(r5)
            recall_10_list.append(r10)
            mrr_list.append(recip_rank)

            for ref in mapping.get("supporting_references", []):
                src = ref.get("source", "")
                if ref.get("status") == "mapped":
                    source_targets_agg.setdefault(src, set()).update(ref.get("matched_chunk_ids", []))

        avg_r5 = float(np.mean(recall_5_list)) if recall_5_list else 1.0
        avg_r10 = float(np.mean(recall_10_list)) if recall_10_list else 1.0
        avg_mrr = float(np.mean(mrr_list)) if mrr_list else 1.0
        per_source = compute_per_source_recall(source_targets_agg, all_retrieved_items)
        trace_rate = compute_traceability_rate(all_retrieved_items, repo_root=self.repo_root)
        dup_rate = compute_duplicate_rate(all_retrieved_items)
        stale_count = compute_stale_count(all_retrieved_items)
        p95_lat = compute_p95_latency(latencies)

        metrics = RetrievalMetrics(
            recall_at_5=round(avg_r5, 4),
            recall_at_10=round(avg_r10, 4),
            mrr=round(avg_mrr, 4),
            per_source_recall={k: round(v, 4) for k, v in per_source.items()},
            traceability_rate=round(trace_rate, 4),
            duplicate_rate=round(dup_rate, 4),
            stale_retrieval_count=stale_count,
            p95_latency_s=round(p95_lat, 4),
            total_queries=evaluated_cases,
        )

        return ExperimentResult(
            run_id=run_id,
            embedding_model=embedding_model,
            reranker_enabled=reranker_enabled,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc).isoformat(),
            cases_evaluated=evaluated_cases,
        )

    def run_evaluation_against_thresholds(
        self,
        run_id: str = "eval-retrieval-v1-chosen",
        golden_version: str = "v1",
        embedding_model: str = "biomedical",
        reranker_enabled: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate full golden set against configs/thresholds.yaml retrieval thresholds.
        """
        exp = self.run_experiment(
            run_id=run_id,
            embedding_model=embedding_model,
            reranker_enabled=reranker_enabled,
            golden_version=golden_version,
            max_cases=None,
        )

        computed = {
            "recall_at_10": exp.metrics.recall_at_10,
            "mrr_min": exp.metrics.mrr,
            "traceability_rate": exp.metrics.traceability_rate,
            "stale_retrieval_count": float(exp.metrics.stale_retrieval_count),
            "p95_latency_s": exp.metrics.p95_latency_s,
        }

        metric_results = evaluate_metrics_against_thresholds(
            computed_metrics=computed,
            thresholds_path=self.repo_root / "configs" / "thresholds.yaml",
        )

        all_passed = all(m["status"] == "PASS" for m in metric_results.values())
        return {
            "run_id": run_id,
            "overall_status": "PASS" if all_passed else "FAIL",
            "metrics": metric_results,
            "experiment": exp.model_dump(),
        }
