"""
Cardiology Specialist RAG Agent & Knowledge Base
Provides deep domain-specific knowledge ingestion, query expansion, and evidence retrieval
from Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine (12th Edition).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..vector_index import MedicalKnowledgeIndex
from .internal_medicine_rag import EvidenceBrief

logger = logging.getLogger("CardiologyRAG")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BRAUNWALD_COLLECTION_PATH = REPO_ROOT / "data" / "knowledge" / "braunwald_collection.json"
BRAUNWALD_EMBEDDINGS_PATH = REPO_ROOT / "data" / "knowledge" / "braunwald_embeddings.npy"

CARDIOLOGY_SYNONYM_MAP: Dict[str, List[str]] = {
    "chest pain": ["angina pectoris", "substernal pressure", "myocardial ischemia", "acute coronary syndrome", "troponin elevation"],
    "nstemi": ["non-st-elevation myocardial infarction", "subendocardial infarction", "unstable angina", "dual antiplatelet therapy", "heparin"],
    "stemi": ["st-elevation myocardial infarction", "transmural myocardial infarction", "percutaneous coronary intervention", "primary pci", "cardiogenic shock"],
    "heart failure": ["congestive heart failure", "reduced ejection fraction", "preserved ejection fraction", "b-type natriuretic peptide", "furosemide"],
    "atrial fibrillation": ["supraventricular arrhythmia", "rate control", "rhythm control", "anticoagulation", "chadsvasc"],
    "pericarditis": ["pericardial friction rub", "pr-segment depression", "diffuse st elevation", "colchicine", "nsaids"],
    "aortic stenosis": ["systolic ejection murmur", "valvular heart disease", "tavr", "syncope", "angina"],
}


class CardiologyRAGAgent:
    """
    Dedicated Cardiology knowledge retrieval agent indexing Braunwald's Heart Disease.
    """

    def __init__(self, collection_path: Optional[Path] = None, embeddings_path: Optional[Path] = None):
        self.collection_path = collection_path or BRAUNWALD_COLLECTION_PATH
        self.embeddings_path = embeddings_path or BRAUNWALD_EMBEDDINGS_PATH
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(f"Cardiology RAG Agent initialized with {len(self.chunks)} Braunwald chunks (Dense vectors: {emb_p is not None}).")

    def _load_collection(self) -> List[Dict[str, Any]]:
        if self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"Loaded {len(data)} Cardiology chunks from {self.collection_path.name}")
                        return data
            except Exception as e:
                logger.warning(f"Could not load Braunwald collection from {self.collection_path}: {e}")
        return []

    def expand_query(self, query: str) -> str:
        """Enriches the clinical query with cardiovascular terminology and synonym mapping."""
        q_lower = query.lower()
        expanded_terms = [query]
        for trigger, synonyms in CARDIOLOGY_SYNONYM_MAP.items():
            if trigger in q_lower:
                expanded_terms.extend(synonyms[:2])
        return " ".join(expanded_terms)

    def retrieve_evidence(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages from Braunwald's Heart Disease."""
        if not self.chunks:
            return []
        expanded = self.expand_query(query)
        results = self.index.search(expanded, top_k=top_k)
        formatted = []
        for r in results:
            text = r.get("text") or r.get("content") or ""
            formatted.append({
                "book": "Braunwald's Heart Disease",
                "specialty": "Cardiology",
                "chapter": r.get("chapter", "Cardiovascular Medicine"),
                "topic": r.get("topic", "Clinical Cardiology"),
                "page": r.get("page", 1),
                "text": text[:500] if len(text) > 500 else text,
                "relevance_score": r.get("relevance_score", 0.0),
            })
        return formatted

    def generate_evidence_brief(
        self,
        chief_complaint: str,
        hpi: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> EvidenceBrief:
        """Synthesizes structured cardiovascular evidence brief for clinical decision support."""
        search_query = f"{chief_complaint} {hpi[:150]}"
        if abnormal_labs:
            search_query += f" {' '.join(abnormal_labs)}"

        citations = self.retrieve_evidence(search_query, top_k=3)

        # Default clinical guidance tailored to cardiovascular pathology
        workup = ["12-Lead ECG", "High-Sensitivity Troponin I", "Comprehensive Metabolic Panel", "Chest Radiograph", "Transthoracic Echocardiogram"]
        therapy = [
            "Aspirin 325 mg oral loading dose",
            "P2Y12 inhibitor (Ticagrelor 180 mg or Clopidogrel 300-600 mg)",
            "Anticoagulation (Unfractionated Heparin or Enoxaparin)",
            "High-intensity Statin (Atorvastatin 80 mg)",
        ]
        contraindications = ["Avoid NSAIDs (non-aspirin)", "Avoid nitrates in right ventricular infarction or severe aortic stenosis"]

        summary = (
            f"Evidence from Braunwald's Heart Disease regarding presentation of '{chief_complaint}'. "
            f"Retrieved {len(citations)} citations addressing guideline-directed medical therapy and diagnostics."
        )

        return EvidenceBrief(
            query=search_query,
            domain="Cardiovascular Medicine",
            citations=citations,
            clinical_summary=summary,
            recommended_workup=workup,
            recommended_therapy=therapy,
            contraindications=contraindications,
        )
