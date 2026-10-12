"""
Emergency Medicine Specialist RAG Agent & Knowledge Base
Provides deep domain-specific knowledge ingestion, query expansion, and evidence retrieval
from Tintinalli's Emergency Medicine Manual (McGraw-Hill / ACEP).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..vector_index import MedicalKnowledgeIndex
from .internal_medicine_rag import EvidenceBrief

logger = logging.getLogger("EmergencyMedicineRAG")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TINTINALLI_COLLECTION_PATH = REPO_ROOT / "data" / "knowledge" / "tintinalli_collection.json"
TINTINALLI_EMBEDDINGS_PATH = REPO_ROOT / "data" / "knowledge" / "tintinalli_embeddings.npy"

EMERGENCY_SYNONYM_MAP: Dict[str, List[str]] = {
    "resuscitation": ["cardiopulmonary arrest", "acls", "rosc", "defibrillation", "epinephrine 1mg iv", "amiodarone"],
    "airway": ["rapid sequence intubation", "rsi", "difficult airway", "etomidate", "succinylcholine", "rocuronium", "video laryngoscopy", "cricothyroidotomy"],
    "anaphylaxis": ["severe allergic reaction", "stridor", "angioedema", "intramuscular epinephrine", "h1/h2 antagonist", "methylprednisolone", "biphasic reaction"],
    "shock": ["septic shock", "hypovolemic shock", "cardiogenic shock", "distributive shock", "norepinephrine", "lactate clearance", "fluid resuscitation 30ml/kg"],
    "trauma": ["polytrauma", "advanced trauma life support", "atls", "massive transfusion protocol", "e-fast exam", "tranexamic acid", "txa", "pelvic binder"],
    "tension pneumothorax": ["needle decompression", "tube thoracostomy", "chest tube", "absent breath sounds", "tracheal deviation", "obstructive shock"],
    "toxicology": ["poisoning", "acute overdose", "toxidrome", "naloxone", "n-acetylcysteine", "activated charcoal", "anticholinergic toxidrome", "sympathomimetic"],
    "overdose": ["ingestion", "toxidrome", "naloxone", "flumazenil contraindications", "anion gap metabolic acidosis", "toxic alcohol"],
    "altered mental status": ["acute encephalopathy", "coma", "hypoglycemia", "gcs score", "narcan", "thiamine before glucose"],
    "status epilepticus": ["refractory seizure", "benzodiazepine", "lorazepam iv", "levetiracetam", "fosphenytoin", "propofol infusion"],
    "burns": ["thermal injury", "parkland formula", "inhalation injury", "rule of nines", "escharotomy"],
    "hypothermia": ["cold exposure", "active core rewarming", "osborn j waves", "ecmo rewarming"],
    "hyperthermia": ["heat stroke", "evaporative cooling", "ice water immersion", "end organ failure"],
    "sepsis": ["septic shock", "surviving sepsis campaign", "broad spectrum antibiotics within 1 hour", "norepinephrine", "iv fluids"],
}


class EmergencyMedicineRAGAgent:
    """
    Dedicated Emergency Medicine knowledge retrieval agent indexing Tintinalli's Emergency Medicine Manual.
    """

    def __init__(self, collection_path: Optional[Path] = None, embeddings_path: Optional[Path] = None):
        self.collection_path = collection_path or TINTINALLI_COLLECTION_PATH
        self.embeddings_path = embeddings_path or TINTINALLI_EMBEDDINGS_PATH
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(f"Emergency Medicine RAG Agent initialized with {len(self.chunks)} Tintinalli chunks (Dense vectors: {emb_p is not None}).")

    def _load_collection(self) -> List[Dict[str, Any]]:
        if self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"Loaded {len(data)} Emergency Medicine chunks from {self.collection_path.name}")
                        return data
            except Exception as e:
                logger.warning(f"Could not load Tintinalli collection from {self.collection_path}: {e}")
        return []

    def expand_query(self, query: str) -> str:
        """Enriches the emergency query with acute resuscitation terminology and synonym mapping."""
        q_lower = query.lower()
        expanded_terms = [query]
        for trigger, synonyms in EMERGENCY_SYNONYM_MAP.items():
            if trigger in q_lower:
                expanded_terms.extend(synonyms[:2])
        return " ".join(expanded_terms)

    def retrieve_evidence(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages from Tintinalli's Emergency Medicine Manual."""
        if not self.chunks:
            return []
        expanded = self.expand_query(query)
        results = self.index.search(expanded, top_k=top_k)
        formatted = []
        for r in results:
            text = r.get("text") or r.get("content") or ""
            formatted.append({
                "book": "Tintinalli's Emergency Medicine Manual",
                "specialty": "Emergency Medicine",
                "chapter": r.get("chapter", "Resuscitation & Critical Care"),
                "topic": r.get("topic", "Emergency Medicine"),
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
        """Synthesizes structured emergency medicine evidence brief for acute decision support."""
        search_query = f"{chief_complaint} {hpi[:150]}"
        if abnormal_labs:
            search_query += f" {' '.join(abnormal_labs)}"

        citations = self.retrieve_evidence(search_query, top_k=3)

        # Default clinical guidance tailored to emergency stabilization
        c_lower = chief_complaint.lower()
        if "anaphylaxis" in c_lower or "allergic" in c_lower or "stridor" in c_lower:
            domain = "Refractory Anaphylaxis & Airway Compromise"
            rationale = "Immediate intramuscular epinephrine (0.3-0.5 mg 1:1,000 in anterolateral thigh); secure definitive airway early if stridor or oropharyngeal swelling progresses."
            differential = ["Severe Anaphylactic Shock", "Angioedema (ACEi / Hereditary)", "Foreign Body Airway Obstruction", "Vocal Cord Dysfunction"]
            workup = ["Continuous cardiorespiratory & SpO2 monitoring", "Point-of-care ultrasound for airway & lung sliding", "Serum tryptase baseline & 2h post-event", "Serial vital signs q5min"]
            treatment = ["Epinephrine 0.3-0.5 mg IM (repeat q5-15 min prn)", "Rapid IV crystalloid bolus (1-2 L) for distributive hypotension", "Diphenhydramine 50 mg IV + Famotidine 20 mg IV", "Methylprednisolone 125 mg IV (biphasic prevention)"]
            contraindications = ["Do NOT delay intramuscular epinephrine for antihistamines or corticosteroids", "Do NOT administer subcutaneous epinephrine due to unpredictable absorption in shock"]
        elif "airway" in c_lower or "intubat" in c_lower or "rsi" in c_lower:
            domain = "Difficult Airway & Rapid Sequence Intubation"
            rationale = "Preoxygenate with high-flow FiO2 1.0; use video laryngoscopy with bougie on first attempt; avoid bag-mask ventilation if possible to minimize aspiration risk."
            differential = ["Acute Hypoxemic Respiratory Failure", "Impending Upper Airway Occlusion", "Severe Metabolic Acidosis with Respiratory Compensation Failure"]
            workup = ["LEMON assessment for difficult airway", "End-tidal CO2 detector STAT", "Continuous pulse oximetry and arterial line preparation"]
            treatment = ["Etomidate 0.3 mg/kg IV or Ketamine 1.5-2 mg/kg IV induction", "Rocuronium 1.2 mg/kg IV or Succinylcholine 1.5 mg/kg IV neuromuscular blockade", "Endotracheal tube placement with video laryngoscope + bougie", "Colorimetric / capnographic waveform confirmation"]
            contraindications = ["Do NOT administer Succinylcholine in known hyperkalemia, denervation injuries, or severe burns > 48h", "Do NOT persist with repeated direct laryngoscopy attempts after 2 failed passes; transition immediately to rescue supraglottic airway or surgical cricothyroidotomy"]
        elif "trauma" in c_lower or "bleed" in c_lower or "shock" in c_lower:
            domain = "Polytrauma, Hemorrhagic Shock & Resuscitation"
            rationale = "Damage control resuscitation with balanced blood components (1:1:1 PRBCs, FFP, Platelets); administer Tranexamic Acid (TXA) within 3 hours of injury."
            differential = ["Hemorrhagic Shock Class III/IV", "Tension Pneumothorax", "Cardiac Tamponade", "Neurogenic Shock"]
            workup = ["E-FAST ultrasound (cardiac, pleural, peritoneal spaces)", "Type and Crossmatch 4-6 units STAT", "Point-of-care venous lactate and arterial blood gas", "Pelvic and portable chest radiographs"]
            treatment = ["Activate Massive Transfusion Protocol (MTP)", "Tranexamic acid (TXA) 1 g IV over 10 min, then 1 g infusion over 8h", "Immediate pelvic binder application if open-book pelvic fracture suspected", "Permissive hypotension (target SBP 80-90 mmHg until surgical hemostasis)"]
            contraindications = ["Do NOT administer aggressive large-volume crystalloids (> 1 L) before blood products (worsens dilutional coagulopathy)", "Do NOT delay operative hemostasis for unnecessary full-body CT scanning in hemodynamically unstable patients"]
        else:
            domain = "Emergency Resuscitation & Time-Critical Triage"
            rationale = "Rapid assessment of ABCs, immediate continuous monitoring, establishment of two large-bore IV accesses, and targeted symptom-directed stabilization."
            differential = ["Acute Life-Threatening Cardiopulmonary Pathology", "Severe Sepsis / Septic Shock", "Toxic Metabolic Encephalopathy"]
            workup = ["12-lead ECG STAT", "Point-of-care glucose, blood gas, and lactate", "Continuous telemetry, pulse oximetry, and noninvasive BP cycling", "Focused bedside point-of-care ultrasonography (POCUS)"]
            treatment = ["Supplemental oxygen titrated to SpO2 >= 94%", "Establish 2 large-bore peripheral IV lines (16-18G) or intraosseous (IO) access", "Isotonic crystalloid challenge (30 mL/kg) if hypoperfusion or hypotension present", "Early specialist consultation and definitive department disposition"]
            contraindications = ["Do NOT leave unstable resuscitation patient unattended", "Do NOT administer medications without verifying renal, cardiac, and anaphylactic contraindications"]

        summary = (
            f"Tintinalli's Emergency Medicine Manual: Critical resuscitation guidance for '{chief_complaint}'. "
            f"Retrieved {len(citations)} citations addressing immediate stabilization protocols: {rationale}"
        )

        return EvidenceBrief(
            query=search_query,
            domain=domain,
            citations=citations,
            clinical_summary=summary,
            recommended_workup=workup,
            recommended_therapy=treatment,
            contraindications=contraindications,
        )
