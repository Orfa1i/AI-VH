"""
KG-augmented retrieval for AI-VH (STEP 52 / P9.2).

Mechanism: match query terms to graph nodes (RxNorm synonyms, condition term
lists), collect reachable guideline chunk ids, boost base-ranked items that
are KG-reachable, and append missing reachable chunks (built from the same
index records, capped). Everything added is resolvable in the corpus.
Behind the `kg_enabled` flag (default off); flag off returns base rankings.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from vh.rag.sources.rxnorm import RxNormService

from .build import CONDITION_TERMS, REPO_ROOT, build_graph
from .graph import KnowledgeGraph

KG_BOOST = 0.5
MAX_APPENDED_CHUNKS = 2


def is_kg_enabled(repo_root: Optional[Path] = None) -> bool:
    """Read the committed kgraph flag from configs/rag.yaml."""
    import yaml

    root = Path(repo_root) if repo_root else REPO_ROOT
    config_path = root / "configs" / "rag.yaml"
    if not config_path.exists():
        return False
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return bool(config.get("kgraph", {}).get("enabled", False))


def match_drug_nodes(query: str, graph: KnowledgeGraph) -> List[str]:
    """Drug node ids whose synonym appears in the query (longest-first)."""
    service = RxNormService()
    lowered = f" {query.lower()} "
    hits: List[Tuple[int, str]] = []
    seen_cuis: Set[str] = set()
    for rxcui, concept in sorted(service.concepts.items()):
        for synonym in concept.get("synonyms", []) or []:
            term = str(synonym).lower().strip()
            if len(term) >= 4 and f" {term} " in lowered:
                if str(rxcui) not in seen_cuis:
                    seen_cuis.add(str(rxcui))
                    hits.append((len(term), f"rxnorm:{rxcui}"))
                break
    hits.sort(key=lambda item: -item[0])
    return [node_id for _, node_id in hits if node_id in graph.nodes]


def match_condition_nodes(query: str, graph: KnowledgeGraph) -> List[str]:
    """Condition node ids whose heuristic terms appear in the query."""
    lowered = f" {query.lower()} "
    matched: List[str] = []
    for cond_id, terms in CONDITION_TERMS.items():
        if cond_id not in graph.nodes:
            continue
        if any(term in lowered for term in terms):
            matched.append(cond_id)
    return matched


def reachable_chunk_ids(query: str, graph: KnowledgeGraph) -> List[str]:
    """Guideline chunk ids reachable from query-matched nodes, sorted."""
    chunk_ids: Set[str] = set()
    for node_id in match_drug_nodes(query, graph) + match_condition_nodes(query, graph):
        for _, target in graph.neighbors(node_id):
            if target.type == "guideline":
                for _, chunk in graph.neighbors(target.id, relation="CONTAINS"):
                    if chunk.type == "chunk":
                        chunk_ids.add(chunk.id)
    return sorted(chunk_ids)


def augment_for_query(
    query: str, base_chunk_ids: List[str], graph: KnowledgeGraph, k: int = 10
) -> List[str]:
    """Deterministic merge used by unit tests (ids only)."""
    reachable = reachable_chunk_ids(query, graph)
    reachable_set = set(reachable)
    boosted = [cid for cid in base_chunk_ids if cid in reachable_set]
    rest = [cid for cid in base_chunk_ids if cid not in reachable_set]
    missing = [cid for cid in reachable if cid not in set(base_chunk_ids)]
    merged = boosted + rest + missing[: max(0, MAX_APPENDED_CHUNKS)]
    return merged[:k]


def retrieve_with_kg(
    query: str,
    repo_root: Optional[Path] = None,
    k: int = 10,
    kg_enabled: bool = False,
    embedding_model: str = "biomedical",
) -> List[Any]:
    """Base hybrid retrieval, optionally KG-augmented. Same call shape both ways."""
    from eval.harness.scorers.retrieval import RetrievalEvaluationHarness

    root = Path(repo_root) if repo_root else REPO_ROOT
    harness = RetrievalEvaluationHarness(repo_root=root)
    index = harness._get_or_build_index(embedding_model)
    from vh.rag.retrieval import UnifiedRetrievalService

    service = UnifiedRetrievalService(index=index)
    base_items = service.retrieve(query=query, k=k)
    if not kg_enabled:
        return base_items

    graph = build_graph(root)
    reachable = reachable_chunk_ids(query, graph)
    reachable_set = set(reachable)
    for item in base_items:
        if item.chunk_id in reachable_set:
            item.scores["kg_boost"] = KG_BOOST
            item.metadata["kg_expansion"] = True
    ordered = sorted(
        base_items, key=lambda item: (item.scores.get("rrf", 0.0) + item.scores.get("kg_boost", 0.0), item.chunk_id or ""), reverse=True
    )
    present = {item.chunk_id for item in ordered}
    records = index.records
    idx_ver = index.manifest.index_version if index.manifest else "v1.0"
    appended = 0
    for chunk_id in reachable:
        if chunk_id in present or appended >= MAX_APPENDED_CHUNKS:
            continue
        rec = records.get(chunk_id)
        if rec is None:
            continue
        chunk = rec["chunk"]
        from vh.rag.retrieval import EvidenceItem

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
