"""Knowledge-graph augmented retrieval package for AI-VH (STEP 52 / P9.2)."""

from .build import CONDITION_TERMS, build_graph, verify_graph
from .evaluate import decide_adoption, run_ab_comparison
from .graph import KGEdge, KGNode, KnowledgeGraph
from .retrieval import augment_for_query, reachable_chunk_ids, retrieve_with_kg

__all__ = [
    "CONDITION_TERMS",
    "KGEdge",
    "KGNode",
    "KnowledgeGraph",
    "augment_for_query",
    "build_graph",
    "decide_adoption",
    "reachable_chunk_ids",
    "retrieve_with_kg",
    "run_ab_comparison",
    "verify_graph",
]
