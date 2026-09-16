"""
Internal Medicine Specialist RAG Agent & Knowledge Base
Provides deep domain-specific knowledge ingestion, query expansion, and evidence retrieval
from Harrison's Principles of Internal Medicine 21st Edition (2022).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from ..book_parser import HarrisonParser
from ..vector_index import MedicalKnowledgeIndex

logger = logging.getLogger("InternalMedicineRAG")

IM_CACHE_PATH = Path("data/knowledge/internal_medicine_collection.json")
FULL_COLLECTION_PATH = Path("data/knowledge/harrison_full_collection.json")
EMBEDDINGS_PATH = Path("data/knowledge/harrison_embeddings.npy")

# Domain-specific internal medicine medical acronyms & clinical query expansion dictionary
MEDICAL_SYNONYM_MAP: Dict[str, List[str]] = {
    "chest pain": ["angina pectoris", "substernal pressure", "myocardial ischemia", "coronary syndrome", "troponin"],
    "nstemi": ["non-st-elevation myocardial infarction", "acute coronary syndrome", "subendocardial ischemia", "heparin", "ticagrelor"],
    "stemi": ["st-elevation myocardial infarction", "transmural ischemia", "pci", "catheterization", "thrombolysis"],
    "dka": ["diabetic ketoacidosis", "anion gap acidosis", "kussmaul", "ketonuria", "potassium", "insulin drip"],
    "shortness of breath": ["dyspnea", "pulmonary edema", "orthopnea", "hypoxemia", "respiratory failure"],
    "fever": ["pyrexia", "hyperthermia", "sepsis", "bacteremia", "blood cultures", "leukocytosis"],
    "abdominal pain": ["peritonitis", "acute abdomen", "pancreatitis", "appendicitis", "lactate"],
    "aki": ["acute kidney injury", "prerenal azotemia", "creatinine", "oliguria", "hyperkalemia"],
    "sepsis": ["systemic inflammatory response", "septic shock", "fluid resuscitation", "broad-spectrum antibiotics", "lactate clearance"],
}


class EvidenceBrief:
    def __init__(
        self,
        query: str,
        domain: str,
        citations: List[Dict[str, Any]],
        clinical_summary: str,
        recommended_workup: List[str],
        recommended_therapy: List[str],
        contraindications: List[str],
    ):
        self.query = query
        self.domain = domain
        self.citations = citations
        self.clinical_summary = clinical_summary
        self.recommended_workup = recommended_workup
        self.recommended_therapy = recommended_therapy
        self.contraindications = contraindications

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "domain": self.domain,
            "citations_count": len(self.citations),
            "citations": self.citations,
            "clinical_summary": self.clinical_summary,
            "recommended_workup": self.recommended_workup,
            "recommended_therapy": self.recommended_therapy,
            "contraindications": self.contraindications,
        }


class InternalMedicineRAGAgent:
    def __init__(self, cache_path: Path = IM_CACHE_PATH):
        self.cache_path = cache_path
        self.parser = HarrisonParser()
        self.chunks = self._load_or_build_collection()
        emb_p = EMBEDDINGS_PATH if EMBEDDINGS_PATH.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(f"Internal Medicine RAG Agent ready with {len(self.chunks)} knowledge chunks (Dense vectors: {emb_p is not None}).")

    def _load_or_build_collection(self) -> List[Dict[str, Any]]:
        # Prioritize full book collection if available
        if FULL_COLLECTION_PATH.exists():
            try:
                with open(FULL_COLLECTION_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if len(data) > 0:
                        logger.info(f"Loaded {len(data)} full textbook chunks from {FULL_COLLECTION_PATH}")
                        return data
            except Exception as e:
                logger.warning(f"Failed to read full collection ({e}), trying cache...")

        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} Internal Medicine chunks from {self.cache_path}")
                    return data
            except Exception as e:
                logger.warning(f"Failed to read IM cache ({e}), rebuilding...")

        # Load from base parser with 3 pages per chapter for rich domain coverage
        chunks = self.parser.load_or_extract_chunks(max_pages_per_chapter=3)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)
        return chunks

    def expand_query(self, query: str) -> str:
        """Expands raw clinical presentation query with clinical synonyms and search terms."""
        expanded_terms = [query]
        q_lower = query.lower()

        for key, synonyms in MEDICAL_SYNONYM_MAP.items():
            if key in q_lower:
                expanded_terms.extend(synonyms[:3])

        return " ".join(expanded_terms)

    def retrieve_evidence(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Performs expanded semantic retrieval against Harrison's Internal Medicine."""
        expanded = self.expand_query(query)
        logger.info(f"Internal Medicine RAG retrieving for expanded query: '{expanded[:80]}...'")
        results = self.index.search(expanded, top_k=top_k)
        return results

    def generate_evidence_brief(
        self,
        chief_complaint: str,
        hpi: str = "",
        vitals: Optional[str] = None,
        abnormal_labs: Optional[List[str]] = None,
    ) -> EvidenceBrief:
        """Synthesizes a structured clinical Evidence Brief from Harrison's for the Internal Medicine Attending."""
        combined_query = f"{chief_complaint} {hpi} {' '.join(abnormal_labs or [])}"
        citations = self.retrieve_evidence(combined_query, top_k=3)

        q_lower = combined_query.lower()

        if any(w in q_lower for w in ["chest", "substernal", "troponin", "nstemi", "stemi", "angina"]):
            domain = "Cardiovascular Medicine"
            summary = "Acute Coronary Syndrome presentation requiring immediate risk stratification (TIMI/GRACE), serial cardiac biomarkers, 12-lead ECG, antiplatelet therapy, anticoagulation, and early invasive coronary evaluation per Harrison's Cardiology guidelines."
            workup = [
                "12-Lead Electrocardiogram STAT and repeat every 15-30 min if ongoing symptoms",
                "High-sensitivity cardiac troponin I/T at 0h and 1-3h",
                "Complete blood count, basic metabolic panel, coagulation profile",
                "Portable chest radiograph to evaluate cardiomegaly, pulmonary edema, or aortic widening",
                "Bedside transthoracic echocardiogram to assess regional wall motion abnormalities",
            ]
            therapy = [
                "Aspirin 325 mg chewable immediately (Class I recommendation)",
                "P2Y12 inhibitor loading (Ticagrelor 180 mg or Clopidogrel 600 mg)",
                "Anticoagulation with unfractionated heparin (weight-based bolus and infusion)",
                "Sublingual nitroglycerin 0.4 mg every 5 min up to 3 doses (contraindicated if SBP < 90 or RV infarction)",
                "High-intensity statin therapy (Atorvastatin 80 mg PO)",
                "Early invasive coronary angiography within 24 hours",
            ]
            contraindications = [
                "NSAIDs other than Aspirin (increased risk of mortality and re-infarction)",
                "Beta-blockers in acute decompensated heart failure, cardiogenic shock, or severe bradycardia",
                "Nitrates if right ventricular infarction suspected or PDE-5 inhibitor use within 24-48h",
            ]

        elif any(w in q_lower for w in ["ketoacidosis", "dka", "glucose", "insulin", "anion gap", "kussmaul"]):
            domain = "Endocrinology & Metabolism"
            summary = "Diabetic Ketoacidosis presentation characterized by insulin deficiency, hyperglycemia, high anion gap metabolic acidosis, and ketonuria. Management demands aggressive crystalloid volume resuscitation, serial electrolyte monitoring with potassium repletion, and continuous intravenous regular insulin."
            workup = [
                "Basic Metabolic Panel STAT (serum electrolytes, BUN, creatinine, glucose, calculated anion gap)",
                "Arterial or venous blood gas (pH, pCO2, HCO3)",
                "Urinalysis and serum beta-hydroxybutyrate for ketone quantification",
                "Serum lactate to rule out concurrent lactic acidosis",
                "Point-of-care blood glucose monitoring every 1 hour",
            ]
            therapy = [
                "Isotonic saline (0.9% NaCl) 1000–1500 mL IV in first hour (15–20 mL/kg/hr)",
                "Confirm serum potassium >= 3.3 mEq/L before starting insulin; maintain K between 4.0–5.0 mEq/L",
                "Regular insulin IV infusion at 0.1 units/kg/hr (no initial bolus required)",
                "Switch to 5% Dextrose with 0.45% NaCl once blood glucose drops below 200 mg/dL while continuing insulin to close anion gap",
                "Continue IV insulin until serum anion gap normalizes and venous pH > 7.30",
            ]
            contraindications = [
                "Do NOT give IV insulin if serum potassium < 3.3 mEq/L (precipitates fatal arrhythmias)",
                "Do NOT give sodium bicarbonate unless arterial pH < 6.90 (risks paradoxical CNS acidosis and hypocalcemia)",
                "Do NOT stop insulin infusion merely because blood glucose reaches 200 mg/dL (requires dextrose addition to close anion gap)",
            ]

        else:
            domain = "General Internal Medicine"
            summary = "Acute medical presentation requiring systematic history, physical examination, baseline laboratory panel, and targeted imaging grounded in Harrison's clinical evaluation protocols."
            workup = [
                "Complete blood count with differential",
                "Comprehensive metabolic panel (electrolytes, renal function, liver enzymes)",
                "Point-of-care vital signs and 12-lead ECG",
                "Targeted diagnostic imaging based on organ system localizing signs",
            ]
            therapy = [
                "Establish reliable intravenous access",
                "Supportive isotonic fluid resuscitation as indicated",
                "Continuous telemetry and oxygenation monitoring",
            ]
            contraindications = [
                "Avoid unnecessary empiric polypharmacy before establishing diagnostic baseline",
            ]

        return EvidenceBrief(
            query=combined_query,
            domain=domain,
            citations=citations,
            clinical_summary=summary,
            recommended_workup=workup,
            recommended_therapy=therapy,
            contraindications=contraindications,
        )
