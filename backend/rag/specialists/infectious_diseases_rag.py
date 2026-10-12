"""
Infectious Diseases Specialist RAG Agent & Knowledge Base
Provides deep domain-specific knowledge ingestion, query expansion, and evidence retrieval
from Harrison's Infectious Diseases (Anthony S. Fauci, Dennis L. Kasper).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..vector_index import MedicalKnowledgeIndex
from .internal_medicine_rag import EvidenceBrief

logger = logging.getLogger("InfectiousDiseasesRAG")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ID_COLLECTION_PATH = REPO_ROOT / "data" / "knowledge" / "infectious_diseases_collection.json"
ID_EMBEDDINGS_PATH = REPO_ROOT / "data" / "knowledge" / "infectious_diseases_embeddings.npy"

INFECTIOUS_DISEASES_SYNONYM_MAP: Dict[str, List[str]] = {
    "sepsis": ["septic shock", "bacteremia", "qsofa", "lactate clearance", "blood cultures", "broad-spectrum antibiotics"],
    "bacteremia": ["bloodstream infection", "staphylococcus aureus bacteremia", "gram-negative bacteremia", "endovascular infection"],
    "fever of unknown origin": ["classical fuo", "prolonged febrile illness", "pel-ebstein", "inflammatory markers", "pet-ct imaging"],
    "fuo": ["fever of unknown origin", "occult infection", "prolonged pyrexia", "blood cultures", "biopsy"],
    "endocarditis": ["infective endocarditis", "duke criteria", "valvular vegetation", "transesophageal echocardiogram", "viridans streptococci", "enterococcus"],
    "meningitis": ["acute bacterial meningitis", "cerebrospinal fluid pleocytosis", "lumbar puncture", "streptococcus pneumoniae", "neisseria meningitidis", "dexamethasone"],
    "pneumonia": ["community-acquired pneumonia", "hospital-acquired pneumonia", "ventilator-associated pneumonia", "curb-65", "pseudomonas", "mrsa"],
    "antimicrobial resistance": ["methicillin-resistant staphylococcus aureus", "mrsa", "vancomycin-resistant enterococcus", "vre", "esbl", "carbapenemase", "cre"],
    "mrsa": ["methicillin-resistant staphylococcus aureus", "vancomycin", "daptomycin", "linezolid", "ceftaroline"],
    "c difficile": ["clostridioides difficile colitis", "pseudomembranous colitis", "toxic megacolon", "fidaxomicin", "oral vancomycin"],
    "osteomyelitis": ["septic arthritis", "diabetic foot infection", "bone biopsy", "mri spine", "parenteral antibiotics"],
    "tuberculosis": ["mycobacterium tuberculosis", "acid-fast bacilli", "quantiferon gold", "rifampin isoniazid pyrazinamide ethambutol", "ripe therapy"],
    "fungal": ["invasive candidiasis", "aspergillosis", "cryptococcal meningitis", "echinocandin", "voriconazole", "liposomal amphotericin b"],
    "hiv": ["human immunodeficiency virus", "cd4 count", "opportunistic infection", "pneumocystis jirovecii", "antiretroviral therapy"],
}


class InfectiousDiseasesRAGAgent:
    """
    Dedicated Infectious Diseases knowledge retrieval agent indexing Harrison's Infectious Diseases (Fauci & Kasper).
    """

    def __init__(self, collection_path: Optional[Path] = None, embeddings_path: Optional[Path] = None):
        self.collection_path = collection_path or ID_COLLECTION_PATH
        self.embeddings_path = embeddings_path or ID_EMBEDDINGS_PATH
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(
            f"Infectious Diseases RAG Agent initialized with {len(self.chunks)} chunks "
            f"(Dense vectors: {emb_p is not None})."
        )

    def _load_collection(self) -> List[Dict[str, Any]]:
        if self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"Loaded {len(data)} Infectious Diseases chunks from {self.collection_path.name}")
                        return data
            except Exception as e:
                logger.warning(f"Could not load collection from {self.collection_path}: {e}")
        return []

    def reload(self):
        """Reloads collection and vector index from disk after background ingestion finishes."""
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(
            f"Infectious Diseases RAG Agent reloaded with {len(self.chunks)} chunks "
            f"(Dense vectors: {emb_p is not None})."
        )

    def expand_query(self, query: str) -> str:
        """Enriches clinical query with microbiological terminology and antimicrobial synonym mapping."""
        q_lower = query.lower()
        expanded_terms = [query]
        for trigger, synonyms in INFECTIOUS_DISEASES_SYNONYM_MAP.items():
            if trigger in q_lower:
                expanded_terms.extend(synonyms[:2])
        return " ".join(expanded_terms)

    def retrieve_evidence(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages from Harrison's Infectious Diseases."""
        if not self.chunks:
            return []
        expanded = self.expand_query(query)
        results = self.index.search(expanded, top_k=top_k)
        formatted = []
        for r in results:
            text = r.get("text") or r.get("content") or ""
            formatted.append({
                "book": "Harrison's Infectious Diseases",
                "specialty": "Infectious Diseases",
                "chapter": r.get("chapter", "Infectious Diseases"),
                "topic": r.get("topic", "Microbiology & Antimicrobial Therapy"),
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
        """Synthesizes structured infectious disease evidence brief for clinical decision support."""
        search_query = f"{chief_complaint} {hpi[:150]}"
        if abnormal_labs:
            search_query += f" {' '.join(abnormal_labs)}"

        citations = self.retrieve_evidence(search_query, top_k=3)

        c_lower = chief_complaint.lower()
        if "endocarditis" in c_lower or "vegetation" in c_lower or "murmur" in c_lower:
            domain = "Infective Endocarditis & Endovascular Infections"
            rationale = "Obtain 3 sets of blood cultures from separate venipunctures prior to antibiotic initiation; perform urgent echocardiography (TTE/TEE) to evaluate for vegetations or perivalvular abscess."
            workup = [
                "Three sets of blood cultures drawn ≥ 30 minutes apart before antimicrobial therapy",
                "Transthoracic echocardiogram (TTE) followed by transesophageal echocardiogram (TEE)",
                "Complete blood count with differential, ESR, and high-sensitivity C-reactive protein",
                "Baseline electrocardiogram (ECG) to monitor for PR prolongation (aortic root abscess)",
            ]
            treatment = [
                "Empiric vancomycin 15-20 mg/kg IV q8-12h (targeting trough 15-20 mcg/mL or AUC/MIC ≥ 400)",
                "Add cefepime 2 g IV q8h or ceftriaxone 2 g IV q24h pending microbiological identification",
                "De-escalate to targeted beta-lactam or aminoglycoside synergy once susceptibilities return",
                "Cardiothoracic surgery consultation if heart failure, persistent bacteremia > 72h, or large vegetation > 10 mm",
            ]
            contraindications = [
                "Do NOT start empiric antibiotics before obtaining adequate blood culture volume unless in septic shock",
                "Do NOT use oral antibiotics for definitive therapy of native or prosthetic valve endocarditis",
            ]
        elif "fuo" in c_lower or "fever of unknown" in c_lower:
            domain = "Fever of Unknown Origin (FUO)"
            rationale = "Structured diagnostic evaluation distinguishing infectious, rheumatologic, and occult neoplastic etiologies before committing to empiric therapy."
            workup = [
                "Three sets of peripheral blood cultures without prior antibiotics",
                "Chest/abdomen/pelvis contrast CT scan",
                "Inflammatory markers (ESR, CRP, ferritin, procalcitonin)",
                "Serologies (HIV, EBV, CMV, ANA, RF) and peripheral blood smear",
                "Biopsy of any clinically abnormal tissue or guided FDG-PET/CT",
            ]
            treatment = [
                "Hold empiric antibiotics in hemodynamically stable patients to avoid obscuring microbiological yield",
                "Daily temperature curve and symptom charting with directed re-examinations",
                "Targeted antimicrobial or immunosuppressive therapy once definitive diagnosis established",
            ]
            contraindications = [
                "Do NOT administer empiric corticosteroids or broad-spectrum antibiotics without diagnostic yield in stable FUO",
                "Do NOT discontinue diagnostic workup after single negative blood culture set",
            ]
        elif "meningitis" in c_lower or "stiff neck" in c_lower:
            domain = "Acute Meningitis & CNS Infections"
            rationale = "Immediate diagnostic lumbar puncture and prompt administration of bactericidal CNS-penetrating antimicrobials and dexamethasone."
            workup = [
                "Immediate blood cultures (2 sets)",
                "Diagnostic lumbar puncture for opening pressure, CSF cell count, differential, protein, glucose, Gram stain, culture, and multiplex PCR",
                "Head CT prior to LP only if focal deficit, altered sensorium, papilledema, or immunocompromise present",
            ]
            treatment = [
                "Dexamethasone 10 mg IV administered with or immediately before first dose of antibiotics",
                "Ceftriaxone 2 g IV q12h + Vancomycin 15-20 mg/kg IV q8-12h",
                "Add Ampicillin 2 g IV q4h if age > 50 or immunocompromised (covering Listeria monocytogenes)",
                "Acyclovir 10 mg/kg IV q8h if viral encephalitis suspected",
            ]
            contraindications = [
                "Do NOT delay antibiotic administration for neuroimaging; give antibiotics immediately if LP is delayed",
                "Do NOT give dexamethasone after antibiotics have already been running for hours without benefit",
            ]
        else:
            domain = "Infectious Diseases & Antimicrobial Stewardship"
            rationale = "Prompt source identification, appropriate microbiological sampling before therapy, rational empiric antimicrobial selection, and timely de-escalation based on susceptibility data."
            workup = [
                "Targeted blood, urine, sputum, and wound cultures prior to antimicrobial therapy",
                "Complete blood count with differential, serum lactate, and procalcitonin",
                "Focused diagnostic imaging directed by clinical examination findings",
                "Assess renal function (eGFR/CrCl) for accurate antimicrobial dosing",
            ]
            treatment = [
                "Initiate guideline-directed empiric antimicrobial therapy tailored to suspected infection source",
                "Targeted source control (abscess drainage, line removal, debridement)",
                "Re-evaluate clinical response and microbiology at 48-72 hours for antimicrobial de-escalation",
                "Implement therapeutic drug monitoring (TDM) for vancomycin, aminoglycosides, and azoles",
            ]
            contraindications = [
                "Do NOT continue broad-spectrum empiric coverage beyond 72 hours when definitive susceptibilities are available",
                "Do NOT treat asymptomatic bacteriuria in non-pregnant patients without planned urological instrumentation",
            ]

        summary = (
            f"Harrison's Infectious Diseases: Expert infectious disease assessment for '{chief_complaint}'. "
            f"Retrieved {len(citations)} citations addressing evidence-based antimicrobial regimens and diagnostic criteria: {rationale}"
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
