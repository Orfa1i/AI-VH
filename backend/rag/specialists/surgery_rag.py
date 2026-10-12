"""
Surgery Specialist RAG Agent & Knowledge Base
Provides domain-specific knowledge ingestion, surgical query expansion, and evidence retrieval
from Schwartz's Principles of Surgery (10th Edition).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..vector_index import MedicalKnowledgeIndex
from .internal_medicine_rag import EvidenceBrief

logger = logging.getLogger("SurgeryRAG")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCHWARTZ_COLLECTION_PATH = REPO_ROOT / "data" / "knowledge" / "schwartz_collection.json"
SCHWARTZ_EMBEDDINGS_PATH = REPO_ROOT / "data" / "knowledge" / "schwartz_embeddings.npy"

SURGERY_SYNONYM_MAP: Dict[str, List[str]] = {
    "acute abdomen": [
        "peritonitis", "rebound tenderness", "guarding", "involuntary rigidity",
        "abdominal pain", "surgical exploration", "exploratory laparotomy"
    ],
    "appendicitis": [
        "acute appendicitis", "right lower quadrant pain", "mcburney point",
        "appendectomy", "periappendiceal abscess", "rovsing sign", "psoas sign", "obturator sign"
    ],
    "cholecystitis": [
        "acute cholecystitis", "gallbladder", "murphy sign", "cholecystectomy",
        "biliary colic", "choledocholithiasis", "biliary pancreatitis", "ultrasound gallbladder"
    ],
    "bowel obstruction": [
        "small bowel obstruction", "sbo", "large bowel obstruction", "air fluid levels",
        "adhesions", "obstipation", "nasogastric decompression", "bowel strangulation", "ischemia"
    ],
    "hernia": [
        "incarcerated hernia", "strangulated hernia", "inguinal hernia", "femoral hernia",
        "ventral hernia", "umbilical hernia", "herniorrhaphy", "mesh repair"
    ],
    "pancreatitis": [
        "acute pancreatitis", "gallstone pancreatitis", "ranson criteria", "lipase",
        "peripancreatic necrosis", "necrosectomy", "ct abdomen with contrast"
    ],
    "diverticulitis": [
        "acute diverticulitis", "left lower quadrant pain", "colonic perforation",
        "hinchey classification", "hartmann procedure", "peridiverticular abscess"
    ],
    "trauma": [
        "blunt abdominal trauma", "penetrating trauma", "fast exam", "splenic laceration",
        "hepatic trauma", "damage control surgery", "laparotomy", "hemoperitoneum"
    ],
    "peritonitis": [
        "generalized peritonitis", "hollow viscus perforation", "free air under diaphragm",
        "pneumoperitoneum", "emergent laparotomy", "source control", "septic peritonitis"
    ],
    "mesenteric ischemia": [
        "acute mesenteric ischemia", "pain out of proportion to exam", "superior mesenteric artery",
        "bowel infarction", "lactate elevation", "embolectomy", "revascularization"
    ],
    "operative risk": [
        "preoperative evaluation", "asa physical status", "cardiac risk index",
        "surgical clearance", "bleeding risk", "dvt prophylaxis", "informed consent"
    ],
    "postoperative fever": [
        "surgical site infection", "atelectasis", "anastomotic leak", "wound dehiscence",
        "deep vein thrombosis", "pulmonary embolism", "intra-abdominal abscess"
    ],
}


class SurgeryRAGAgent:
    """
    Dedicated Surgery knowledge retrieval agent indexing Schwartz's Principles of Surgery (10th Edition).
    """

    def __init__(self, collection_path: Optional[Path] = None, embeddings_path: Optional[Path] = None):
        self.collection_path = collection_path or SCHWARTZ_COLLECTION_PATH
        self.embeddings_path = embeddings_path or SCHWARTZ_EMBEDDINGS_PATH
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(
            f"Surgery RAG Agent initialized with {len(self.chunks)} Schwartz chunks "
            f"(Dense vectors: {emb_p is not None})."
        )

    def _load_collection(self) -> List[Dict[str, Any]]:
        if self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"Loaded {len(data)} Surgery chunks from {self.collection_path.name}")
                        return data
            except Exception as e:
                logger.warning(f"Could not load Schwartz collection from {self.collection_path}: {e}")
        return []

    def reload(self):
        """Reloads collection and vector index from disk after background ingestion finishes."""
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(
            f"Surgery RAG Agent reloaded with {len(self.chunks)} Schwartz chunks "
            f"(Dense vectors: {emb_p is not None})."
        )

    def expand_query(self, query: str) -> str:
        """Enriches the clinical query with surgical terminology and synonym mapping."""
        q_lower = query.lower()
        expanded_terms = [query]
        for trigger, synonyms in SURGERY_SYNONYM_MAP.items():
            if trigger in q_lower:
                expanded_terms.extend(synonyms[:2])
        return " ".join(expanded_terms)

    def retrieve_evidence(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages from Schwartz's Principles of Surgery."""
        if not self.chunks:
            return []
        expanded = self.expand_query(query)
        results = self.index.search(expanded, top_k=top_k)
        formatted = []
        for r in results:
            text = r.get("text") or r.get("content") or ""
            formatted.append({
                "book": "Schwartz's Principles of Surgery, 10th Edition",
                "specialty": "Surgery",
                "chapter": r.get("chapter", "Surgical Principles"),
                "topic": r.get("topic", "General Surgery"),
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
        """Synthesizes structured surgical evidence brief for clinical decision support."""
        search_query = f"{chief_complaint} {hpi[:150]}"
        if abnormal_labs:
            search_query += f" {' '.join(abnormal_labs)}"

        citations = self.retrieve_evidence(search_query, top_k=3)

        # Default clinical guidance tailored to surgical pathology
        summary = (
            "Schwartz's Principles of Surgery: Immediate surgical evaluation warranted for "
            "acute abdominal pathology, hemodynamic instability from hemorrhage, or strangulated viscus. "
            "Prioritize NPO status, dual large-bore IV access, fluid resuscitation, and surgical source control."
        )
        workup = [
            "Complete blood count (CBC) with differential for leukocytosis and left shift",
            "Serum lactate and comprehensive metabolic panel (electrolytes, BUN, creatinine)",
            "Coagulation panel (PT/INR, PTT) and Type & Crossmatch",
            "Urgent contrast-enhanced CT of abdomen/pelvis or bedside FAST ultrasound if unstable",
            "Upright chest/abdominal radiograph for free subdiaphragmatic air (pneumoperitoneum)",
        ]
        therapy = [
            "Strict NPO (nothing by mouth) and NG tube decompression if bowel obstruction",
            "Aggressive isotonic crystalloid fluid resuscitation (lactated Ringer's or normal saline)",
            "Broad-spectrum intravenous empiric antibiotics covering enteric gram-negatives and anaerobes",
            "Urgent surgical consultation for exploratory laparotomy or laparoscopic intervention",
            "Serial abdominal examinations by the same surgical team",
        ]
        contraindications = [
            "Do NOT administer oral analgesics, sedatives, or oral fluids prior to surgical evaluation",
            "Avoid barium contrast studies if bowel perforation or obstruction is suspected",
            "Avoid unmonitored delay in definitive surgical source control when peritonitis is present",
        ]

        return EvidenceBrief(
            query=search_query,
            domain="Surgery",
            citations=citations,
            clinical_summary=summary,
            recommended_workup=workup,
            recommended_therapy=therapy,
            contraindications=contraindications,
        )
