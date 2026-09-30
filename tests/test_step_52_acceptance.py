"""
Acceptance tests for STEP 52 (P9.2): knowledge graph experiment.

Criteria (from plan/prompts/phase-9-advanced/STEP-52_P9.2_knowledge-graph.md):
1. Every edge resolves to its source.
2. Adopt only if primary metrics improve with no safety regression; otherwise
   the flag stays off.
3. Full regression suite passes.
Plus: augmentation determinism, resolvable-only additions, flag plumbing.
"""

from pathlib import Path

import pytest

from vh.rag.kg.build import build_graph
from vh.rag.kg.evaluate import decide_adoption, run_ab_comparison
from vh.rag.kg.graph import KnowledgeGraph

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def graph() -> KnowledgeGraph:
    return build_graph(REPO_ROOT)


def test_graph_edges_resolve_to_sources(graph: KnowledgeGraph):
    """Criterion 1: every edge carries provenance that resolves."""
    assert graph.n_edges() > 0
    assert graph.n_nodes() > 0
    unresolved = graph.unresolved_edges()
    assert unresolved == [], f"Unresolved edges: {unresolved[:5]}"


def test_graph_covers_required_sources(graph: KnowledgeGraph):
    """Nodes/edges span drugs, classes, interactions, contraindications, guidelines."""
    types = graph.node_types()
    for required in ("drug", "ingredient", "drug_class", "condition", "guideline", "chunk"):
        assert required in types, f"Missing node type: {required}"
    relations = graph.relation_types()
    for required in (
        "HAS_INGREDIENT",
        "IN_CLASS",
        "INTERACTS_WITH",
        "CONTRAINDICATED_IN",
        "GUIDELINE_FOR",
        "CONTAINS",
    ):
        assert required in relations, f"Missing relation: {required}"


def test_kg_augmentation_deterministic(graph: KnowledgeGraph):
    """Same query twice yields identical augmented rankings."""
    from vh.rag.kg.retrieval import augment_for_query

    first = augment_for_query(
        "acute chest pain with troponin rise", base_chunk_ids=["c1", "c2"], graph=graph, k=10
    )
    second = augment_for_query(
        "acute chest pain with troponin rise", base_chunk_ids=["c1", "c2"], graph=graph, k=10
    )
    assert first == second


def test_augmentation_only_adds_resolvable_chunks(graph: KnowledgeGraph):
    """KG-added chunk ids exist in the corpus records with valid locators."""
    from vh.rag.kg.retrieval import reachable_chunk_ids

    chunk_ids = reachable_chunk_ids("cough with sputum and infiltrate", graph=graph)
    assert len(chunk_ids) > 0
    records = _index_records()
    for cid in chunk_ids:
        assert cid in records, f"KG chunk not in corpus: {cid}"
        locator = records[cid]["chunk"].locator
        assert locator and "#" in locator


def _index_records():
    from eval.harness.scorers.retrieval import RetrievalEvaluationHarness

    harness = RetrievalEvaluationHarness(repo_root=REPO_ROOT)
    index = harness._get_or_build_index("biomedical")
    return index.records


def test_ab_reproducible():
    """The A/B comparison is deterministic across repeated runs."""
    first = run_ab_comparison(repo_root=REPO_ROOT, max_cases=10)
    second = run_ab_comparison(repo_root=REPO_ROOT, max_cases=10)
    for arm in ("rag_only", "kg"):
        for key, value in first[arm].items():
            if key == "p95_latency_s":
                assert value < 1.5 and second[arm][key] < 1.5
            else:
                assert value == second[arm][key], f"{arm}.{key} not reproducible"
    assert first["decision"] == second["decision"]


def test_adoption_rule_unit():
    """Adopt only on strict improvement with no safety regression."""
    improved = {
        "recall_at_10": (0.90, 0.95),
        "mrr": (0.80, 0.85),
        "stale_count": (0, 0),
        "traceability": (1.0, 1.0),
    }
    assert decide_adoption(improved) == "adopt"
    tie = {
        "recall_at_10": (0.90, 0.90),
        "mrr": (0.80, 0.80),
        "stale_count": (0, 0),
        "traceability": (1.0, 1.0),
    }
    assert decide_adoption(tie) == "reject"
    regressed = {
        "recall_at_10": (0.90, 0.95),
        "mrr": (0.80, 0.85),
        "stale_count": (0, 1),
        "traceability": (1.0, 1.0),
    }
    assert decide_adoption(regressed) == "reject"
    unsafe = {
        "recall_at_10": (0.90, 0.95),
        "mrr": (0.80, 0.85),
        "stale_count": (0, 0),
        "traceability": (1.0, 0.9),
    }
    assert decide_adoption(unsafe) == "reject"


def test_flag_matches_measured_decision():
    """Committed flag equals the measured full-golden-set decision; off means off."""
    import yaml

    result = run_ab_comparison(repo_root=REPO_ROOT, max_cases=None)
    assert result["n_cases"] == 60
    assert result["decision"] in ("adopt", "reject")
    config = yaml.safe_load((REPO_ROOT / "configs" / "rag.yaml").read_text(encoding="utf-8"))
    expected_flag = result["decision"] == "adopt"
    assert config.get("kgraph", {}).get("enabled", False) is expected_flag
    # The helper reads the same committed value.
    from vh.rag.kg.retrieval import is_kg_enabled

    assert is_kg_enabled(REPO_ROOT) is expected_flag
    # Flag-off plumbing: with the flag off the service behaves exactly as base
    # RAG (deterministic), and no item carries KG provenance markers.
    from vh.rag.kg.retrieval import retrieve_with_kg

    first = retrieve_with_kg("acute chest pain", repo_root=REPO_ROOT, k=10, kg_enabled=False)
    second = retrieve_with_kg("acute chest pain", repo_root=REPO_ROOT, k=10, kg_enabled=False)
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]
    assert all("kg_expansion" not in item.metadata for item in first)
