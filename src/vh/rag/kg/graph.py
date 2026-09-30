"""
Knowledge graph core for AI-VH (STEP 52 / P9.2).

Typed nodes, provenance-carrying edges, and resolution checks. The graph is
built exclusively from existing normalised sources (RxNorm formulary, safety
tables, guideline chunk maps); it never invents clinical relations.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

NODE_TYPES = {"drug", "ingredient", "drug_class", "condition", "guideline", "chunk", "safety_row"}

RELATIONS = {
    "HAS_INGREDIENT",
    "IN_CLASS",
    "INTERACTS_WITH",
    "CONTRAINDICATED_IN",
    "GUIDELINE_FOR",
    "CONTAINS",
}


class KGNode:
    """Graph node with a stable id, a type, and a human label."""

    def __init__(self, node_id: str, node_type: str, label: str) -> None:
        if node_type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {node_type!r}")
        self.id = node_id
        self.type = node_type
        self.label = label

    def __repr__(self) -> str:
        return f"KGNode({self.id!r}, {self.type!r})"


class KGEdge:
    """Directed edge with mandatory provenance (source system + locator)."""

    def __init__(self, src: str, relation: str, dst: str, provenance: Dict[str, Any]) -> None:
        if relation not in RELATIONS:
            raise ValueError(f"Unknown relation: {relation!r}")
        if not provenance.get("source"):
            raise ValueError("Every edge requires provenance with a 'source'.")
        self.src = src
        self.relation = relation
        self.dst = dst
        self.provenance = dict(provenance)

    def key(self) -> Tuple[str, str, str]:
        return (self.src, self.relation, self.dst)


class KnowledgeGraph:
    """Small deterministic in-memory clinical knowledge graph."""

    def __init__(self) -> None:
        self.nodes: Dict[str, KGNode] = {}
        self.edges: Dict[Tuple[str, str, str], KGEdge] = {}
        self._outgoing: Dict[str, List[KGEdge]] = {}

    def add_node(self, node_id: str, node_type: str, label: str) -> KGNode:
        node = KGNode(node_id, node_type, label)
        self.nodes[node_id] = node
        return node

    def add_edge(
        self, src: str, relation: str, dst: str, provenance: Dict[str, Any]
    ) -> KGEdge:
        if src not in self.nodes:
            raise KeyError(f"Edge source missing from graph: {src!r}")
        if dst not in self.nodes:
            raise KeyError(f"Edge destination missing from graph: {dst!r}")
        edge = KGEdge(src, relation, dst, provenance)
        self.edges[edge.key()] = edge
        self._outgoing.setdefault(src, []).append(edge)
        return edge

    def neighbors(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[Tuple[KGEdge, KGNode]]:
        """Outgoing neighbors, optionally filtered by relation, in insertion order."""
        result = []
        for edge in self._outgoing.get(node_id, []):
            if relation is not None and edge.relation != relation:
                continue
            target = self.nodes.get(edge.dst)
            if target is not None:
                result.append((edge, target))
        return result

    def n_nodes(self) -> int:
        return len(self.nodes)

    def n_edges(self) -> int:
        return len(self.edges)

    def node_types(self) -> Set[str]:
        return {node.type for node in self.nodes.values()}

    def relation_types(self) -> Set[str]:
        return {edge.relation for edge in self.edges.values()}

    def unresolved_edges(self) -> List[str]:
        """Edge keys whose endpoints are missing (should always be empty)."""
        bad = []
        for key, edge in self.edges.items():
            if edge.src not in self.nodes or edge.dst not in self.nodes:
                bad.append(f"{key} provenance={edge.provenance}")
        return bad
