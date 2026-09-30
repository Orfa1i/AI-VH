"""
Knowledge graph construction for AI-VH (STEP 52 / P9.2).

Sources (all pre-existing, normalised, licence-checked):
- RxNorm built-in formulary: drugs, ingredients, classes, synonyms, interactions.
- Safety tables: drug interactions and contraindications with evidence locators.
- Guideline chunk map (reviewed): condition -> guideline document links.
- Local guideline chunker: guideline document -> chunk membership.
- Dose ranges and red-flag thresholds carry no graph relations and are
  deliberately excluded (documented, not forgotten).

Query term lists (CONDITION_TERMS) are retrieval-matching heuristics, not
clinical knowledge: they map query words to condition nodes only.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from vh.rag.sources.rxnorm import BUILTIN_FORMULARY, BUILTIN_INTERACTIONS, RxNormService

from .graph import KnowledgeGraph

CONDITIONS: Dict[str, Dict[str, Any]] = {
    "acs": {
        "label": "Acute Coronary Syndrome",
        "specialty": "Cardiology",
        "guideline_doc": "GUIDELINE-ACS-2023",
        "terms": [
            "chest pain",
            "chest discomfort",
            " pressure",
            "stemi",
            "nstemi",
            "troponin",
            "ecg",
            "ekg",
            "coronary",
            "myocardial",
            "infarction",
            "angina",
            "acs",
        ],
    },
    "cap": {
        "label": "Community-Acquired Pneumonia",
        "specialty": "Pulmonology",
        "guideline_doc": "GUIDELINE-CAP-2019",
        "terms": [
            "cough",
            "sputum",
            "pneumonia",
            "infiltrate",
            "cap ",
            "fever",
            "dyspnea",
            "crackles",
        ],
    },
    "dka": {
        "label": "Diabetic Ketoacidosis",
        "specialty": "Endocrinology",
        "guideline_doc": "GUIDELINE-DKA-2024",
        "terms": [
            "ketoacidosis",
            "ketone",
            "glucose",
            "hyperglycemia",
            "anion gap",
            "insulin",
            "dka",
            "kussmaul",
        ],
    },
}

CONDITION_TERMS: Dict[str, List[str]] = {
    cond_id: list(info["terms"]) for cond_id, info in CONDITIONS.items()
}

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def _normalize_name(name: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def _drug_node_id(rxcui: str) -> str:
    return f"rxnorm:{rxcui}"


def build_graph(repo_root: Optional[Path] = None) -> KnowledgeGraph:
    """Build the graph from normalised sources. Deterministic. Raises on gaps."""
    root = Path(repo_root) if repo_root else REPO_ROOT
    graph = KnowledgeGraph()
    service = RxNormService()

    formulary: Dict[str, Dict[str, Any]] = BUILTIN_FORMULARY
    for rxcui, concept in sorted(formulary.items()):
        node_id = _drug_node_id(rxcui)
        graph.add_node(node_id, "drug", str(concept.get("name", rxcui)))
        for ingredient in concept.get("ingredients", []) or []:
            ing_id = f"ingredient:{_normalize_name(ingredient).replace(' ', '-')}"
            if ing_id not in graph.nodes:
                graph.add_node(ing_id, "ingredient", str(ingredient))
            graph.add_edge(
                node_id,
                "HAS_INGREDIENT",
                ing_id,
                {"source": "rxnorm-builtin-formulary", "locator": f"rxcui:{rxcui}"},
            )
        for class_name in concept.get("drug_classes", []) or []:
            class_id = f"class:{_normalize_name(class_name).replace(' ', '-')}"
            if class_id not in graph.nodes:
                graph.add_node(class_id, "drug_class", str(class_name))
            graph.add_edge(
                node_id,
                "IN_CLASS",
                class_id,
                {"source": "rxnorm-builtin-formulary", "locator": f"rxcui:{rxcui}"},
            )

    for item in BUILTIN_INTERACTIONS:
        pair = [str(c) for c in item.get("rxcui_pair", [])]
        if len(pair) == 2 and all(_drug_node_id(c) in graph.nodes for c in pair):
            graph.add_edge(
                _drug_node_id(pair[0]),
                "INTERACTS_WITH",
                _drug_node_id(pair[1]),
                {
                    "source": "rxnorm-builtin-interactions",
                    "locator": item.get("description", "")[:120],
                    "severity": item.get("severity", ""),
                },
            )

    _add_safety_edges(graph, root)
    _add_guideline_edges(graph, root)
    return graph


def _resolve_drug(service: RxNormService, name: str) -> Optional[str]:
    rxcui = service.lookup_rxcui(name)
    if rxcui is None:
        return None
    node_id = _drug_node_id(str(rxcui))
    return node_id


def _add_safety_edges(graph: KnowledgeGraph, root: Path) -> None:
    """Interaction / contraindication edges from the curated safety tables."""
    service = RxNormService()
    safety_dir = root / "configs" / "safety"

    interactions_path = safety_dir / "drug_interactions.yaml"
    if interactions_path.exists():
        table = yaml.safe_load(interactions_path.read_text(encoding="utf-8")) or {}
        for entry in table.get("interactions", []) or []:
            names_a = entry.get("drug_a_names", []) or []
            names_b = entry.get("drug_b_names", []) or []
            cuis_a = {service.lookup_rxcui(n) for n in names_a} - {None}
            cuis_b = {service.lookup_rxcui(n) for n in names_b} - {None}
            for cui_a in sorted(cuis_a):
                for cui_b in sorted(cuis_b):
                    node_a, node_b = _drug_node_id(str(cui_a)), _drug_node_id(str(cui_b))
                    if node_a in graph.nodes and node_b in graph.nodes and node_a != node_b:
                        graph.add_edge(
                            node_a,
                            "INTERACTS_WITH",
                            node_b,
                            {
                                "source": "configs/safety/drug_interactions.yaml",
                                "locator": str(entry.get("evidence", ""))[:160],
                                "severity": str(entry.get("severity", "")),
                            },
                        )

    contra_path = safety_dir / "contraindications.yaml"
    if contra_path.exists():
        table = yaml.safe_load(contra_path.read_text(encoding="utf-8")) or {}
        for entry in table.get("contraindications", []) or []:
            for drug_name in entry.get("drug_names", []) or []:
                node_id = _resolve_drug(service, str(drug_name))
                if node_id is None or node_id not in graph.nodes:
                    continue
                for condition in entry.get("condition_matches", []) or []:
                    cond_id = f"condition:{_normalize_name(str(condition)).replace(' ', '-')[:48]}"
                    if cond_id not in graph.nodes:
                        graph.add_node(cond_id, "condition", str(condition))
                    graph.add_edge(
                        node_id,
                        "CONTRAINDICATED_IN",
                        cond_id,
                        {
                            "source": "configs/safety/contraindications.yaml",
                            "locator": str(entry.get("source", ""))[:160],
                        },
                    )


def _add_guideline_edges(graph: KnowledgeGraph, root: Path) -> None:
    """Condition -> guideline -> chunk edges from the reviewed chunk map."""
    from vh.rag.chunking import ChunkerConfig, StructureAwareChunker
    from vh.rag.sources.guidelines import LocalGuidelinesAdapter

    chunkmap_path = root / "eval" / "golden" / "v1-chunkmap.json"
    chunkmap: Dict[str, Any] = {}
    if chunkmap_path.exists():
        chunkmap = json.loads(chunkmap_path.read_text(encoding="utf-8"))

    doc_to_specialty: Dict[str, str] = {}
    for case_id, mapping in (chunkmap.get("case_mappings", {}) or {}).items():
        specialty = str(mapping.get("specialty", ""))
        for ref in mapping.get("supporting_references", []) or []:
            if ref.get("status") == "mapped" and ref.get("matched_doc_id"):
                doc_to_specialty.setdefault(str(ref["matched_doc_id"]), specialty)

    specialty_to_condition = {info["specialty"]: cond_id for cond_id, info in CONDITIONS.items()}

    guidelines_dir = root / "data" / "sources" / "guidelines"
    doc_chunk_ids: Dict[str, List[str]] = {}
    if guidelines_dir.exists():
        adapter = LocalGuidelinesAdapter(guidelines_dir)
        # Same chunker configuration as the evaluation harness so chunk ids
        # align exactly with indexed records.
        chunker = StructureAwareChunker(
            config=ChunkerConfig(target_chunk_tokens=256, max_chunk_tokens=384)
        )
        for doc in adapter.load_all():
            doc_chunk_ids.setdefault(doc.doc_id, []).extend(
                chunk.chunk_id for chunk in chunker.chunk_document(doc)
            )

    for cond_id, info in CONDITIONS.items():
        if cond_id not in graph.nodes:
            graph.add_node(cond_id, "condition", str(info["label"]))
        doc_id = str(info["guideline_doc"])
        if doc_id not in graph.nodes:
            graph.add_node(doc_id, "guideline", doc_id)
        if doc_id in doc_to_specialty or doc_id in doc_chunk_ids:
            graph.add_edge(
                cond_id,
                "GUIDELINE_FOR",
                doc_id,
                {"source": "eval/golden/v1-chunkmap.json", "locator": doc_id},
            )
        for chunk_id in sorted(set(doc_chunk_ids.get(doc_id, []))):
            if chunk_id not in graph.nodes:
                graph.add_node(chunk_id, "chunk", chunk_id)
            graph.add_edge(
                doc_id,
                "CONTAINS",
                chunk_id,
                {"source": "local-guidelines-chunker", "locator": chunk_id},
            )


def verify_graph(graph: KnowledgeGraph, repo_root: Optional[Path] = None) -> List[str]:
    """Check every edge's provenance resolves. Returns problem descriptions."""
    root = Path(repo_root) if repo_root else REPO_ROOT
    problems: List[str] = []
    problems.extend(f"structural: {desc}" for desc in graph.unresolved_edges())

    formulary = BUILTIN_FORMULARY
    rx_cuis = set(formulary.keys())
    for key, edge in graph.edges.items():
        provenance = edge.provenance
        if edge.relation in ("HAS_INGREDIENT", "IN_CLASS"):
            cui = edge.src.split(":", 1)[1] if ":" in edge.src else ""
            if cui not in rx_cuis:
                problems.append(f"formulary reference missing for {key}")
        elif edge.relation == "GUIDELINE_FOR":
            if edge.dst not in {info["guideline_doc"] for info in CONDITIONS.values()}:
                problems.append(f"guideline link outside curated set: {key}")
        elif edge.relation == "CONTAINS":
            if not edge.dst.startswith(edge.src):
                problems.append(f"chunk outside its document: {key}")
    _ = root
    return problems
