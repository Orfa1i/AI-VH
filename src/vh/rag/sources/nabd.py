"""
NABD clinical drug search and safety intelligence service.
Combines RxNorm terminology, DailyMed/openFDA product labels, and PubMed evidence.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from vh.rag.sources.base import SourceDocument
from vh.rag.sources.rxnorm import RxNormService


class DrugProfile(BaseModel):
    """
    Unified clinical drug profile produced by NABD search.
    """
    drug_name: str = Field(..., description="Query drug name")
    rxcui: Optional[str] = Field(None, description="Resolved RxNorm Concept Unique Identifier")
    generic_name: str = Field("", description="Canonical generic drug name")
    brand_names: List[str] = Field(default_factory=list, description="Common commercial brand names")
    active_ingredients: List[str] = Field(default_factory=list, description="Active pharmaceutical ingredients")
    drug_classes: List[str] = Field(default_factory=list, description="Pharmacological and therapeutic classes")
    indications: List[str] = Field(default_factory=list, description="FDA-approved clinical indications")
    contraindications: List[str] = Field(default_factory=list, description="Documented clinical contraindications")
    boxed_warnings: List[str] = Field(default_factory=list, description="FDA black box warnings")
    adverse_reactions: List[str] = Field(default_factory=list, description="Documented adverse reactions")
    citations: List[SourceDocument] = Field(default_factory=list, description="Literature and guideline citations")
    safety_alerts: List[str] = Field(default_factory=list, description="Critical clinical safety notifications")


class NABDService:
    """
    NABD multi-source drug search and safety profile engine.
    """
    def __init__(self, rxnorm_service: Optional[RxNormService] = None):
        self.rxnorm = rxnorm_service or RxNormService()
        self.indexed_docs: List[SourceDocument] = []

    def index_documents(self, documents: List[SourceDocument]) -> None:
        """Add SourceDocuments to the in-memory search index."""
        self.indexed_docs.extend(documents)

    def search_drug(self, drug_name: str) -> DrugProfile:
        """
        Execute comprehensive drug search across terminology, labels, and literature.
        """
        rxcui = self.rxnorm.lookup_rxcui(drug_name)
        concept = self.rxnorm.get_concept(rxcui) if rxcui else None

        generic_name = concept.get("name", drug_name) if concept else drug_name
        brand_names = concept.get("synonyms", []) if concept else []
        ingredients = concept.get("ingredients", [drug_name]) if concept else [drug_name]
        drug_classes = concept.get("drug_classes", []) if concept else []

        search_tokens = {drug_name.lower(), generic_name.lower()}
        for ing in ingredients:
            search_tokens.add(ing.lower())
        for bn in brand_names:
            search_tokens.add(bn.lower())

        indications: List[str] = []
        contraindications: List[str] = []
        boxed_warnings: List[str] = []
        adverse_reactions: List[str] = []
        citations: List[SourceDocument] = []
        safety_alerts: List[str] = []

        for doc in self.indexed_docs:
            text_lower = doc.text.lower()
            title_lower = doc.title.lower()

            matches = any(t in text_lower or t in title_lower for t in search_tokens)
            if not matches:
                continue

            sec_path_str = " > ".join(doc.section_path).lower()

            if doc.source_id in {"dailymed", "openfda"}:
                if "boxed warning" in sec_path_str:
                    boxed_warnings.append(doc.text)
                    safety_alerts.append(f"Black Box Warning: {doc.text[:200]}...")
                elif "contraindication" in sec_path_str:
                    contraindications.append(doc.text)
                elif "indication" in sec_path_str:
                    indications.append(doc.text)
                elif "adverse" in sec_path_str:
                    adverse_reactions.append(doc.text)
                elif "interaction" in sec_path_str:
                    safety_alerts.append(f"Interaction Caution: {doc.text[:200]}...")

            elif doc.source_id in {"pubmed", "pmc", "guidelines"}:
                citations.append(doc)

        return DrugProfile(
            drug_name=drug_name,
            rxcui=rxcui,
            generic_name=generic_name,
            brand_names=brand_names,
            active_ingredients=ingredients,
            drug_classes=drug_classes,
            indications=indications,
            contraindications=contraindications,
            boxed_warnings=boxed_warnings,
            adverse_reactions=adverse_reactions,
            citations=citations,
            safety_alerts=safety_alerts,
        )


def nabd_drug_search(drug_name: str, nabd_service: Optional[NABDService] = None) -> DrugProfile:
    """Convenience functional helper for NABD drug search."""
    service = nabd_service or NABDService()
    return service.search_drug(drug_name)
