"""
Medical Specialty Router for AI Virtual Hospital (AI-VH).
Determines the appropriate medical specialty for an incoming patient encounter.
Architecture Rule:
- The Router only determines the appropriate medical specialty.
- The Router is NOT the model being trained.
- All routing decisions are deterministic and clinically grounded.
"""

import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("SpecialtyRouter")


class RoutingDecision(BaseModel):
    specialty: str
    confidence: float
    primary_rationale: str
    matched_keywords: List[str]
    suggested_specialist_name: str
    target_medical_book: str


class MedicalSpecialtyRouter:
    """
    Deterministic clinical router triaging cases to the appropriate specialist agent.
    Never exposes ground truth to the doctor agent and remains strictly separated
    from model fine-tuning and weight optimization.
    """

    CARDIOLOGY_KEYWORDS = [
        "chest pain", "angina", "infarction", "stemi", "nstemi", "coronary",
        "substernal", "crushing chest", "troponin", "arrhythmia", "palpitation",
        "syncope", "heart failure", "orthopnea", "chf", "pericarditis",
        "myocarditis", "cardiogenic", "atrial fibrillation", "tachycardia",
        "aortic dissection", "cardiac arrest", "cardiovascular"
    ]

    INTERNAL_MEDICINE_KEYWORDS = [
        "fever", "cough", "sputum", "pneumonia", "shortness of breath", "dyspnea",
        "ketoacidosis", "dka", "hyperglycemia", "diabetes", "kidney", "creatinine",
        "aki", "oliguria", "sepsis", "bacteremia", "nausea",
        "vomiting", "diarrhea", "jaundice", "rash", "malaise",
        "fatigue", "weight loss", "anemia", "hyponatremia", "hyperkalemia"
    ]

    SURGERY_KEYWORDS = [
        "acute abdomen", "appendicitis", "peritonitis", "rebound tenderness", "guarding",
        "cholecystitis", "gallbladder", "bowel obstruction", "obstipation", "hernia",
        "incarcerated", "strangulated", "laparotomy", "appendectomy", "cholecystectomy",
        "trauma", "splenic laceration", "hemoperitoneum", "mesenteric ischemia",
        "perforation", "pneumoperitoneum", "surgical exploration", "surgical consult",
        "operative", "right lower quadrant pain", "mcburney", "murphy sign",
        "diverticulitis", "wound dehiscence", "anastomotic leak"
    ]

    EMERGENCY_KEYWORDS = [
        "anaphylaxis", "allergic reaction", "stridor", "angioedema", "airway", "intubation",
        "rapid sequence intubation", "rsi", "choking", "foreign body", "aspiration",
        "resuscitation", "cardiac arrest", "code blue", "pea", "asystole", "defibrillation",
        "tension pneumothorax", "needle decompression", "polytrauma", "massive transfusion",
        "toxicology", "overdose", "poisoning", "ingestion", "naloxone",
        "status epilepticus", "burn", "inhalation injury", "hypothermia", "hyperthermia",
        "heat stroke", "emergency stabilization", "unresponsive"
    ]

    INFECTIOUS_DISEASES_KEYWORDS = [
        "fever of unknown origin", "fuo", "bacteremia", "endocarditis", "vegetation",
        "septic shock", "sepsis", "meningitis", "osteomyelitis", "tuberculosis",
        "mrsa", "vre", "esbl", "carbapenemase", "cre", "c difficile", "pseudomembranous",
        "antimicrobial resistance", "opportunistic infection", "hiv", "cd4",
        "aspergillosis", "candidemia", "cryptococcus", "antimicrobial stewardship",
        "prolonged fever", "gram-negative bacteremia", "staphylococcus aureus bacteremia"
    ]

    GYNECOLOGY_KEYWORDS = [
        "pelvic pain", "vaginal bleeding", "abnormal uterine bleeding", "aub",
        "menorrhagia", "metrorrhagia", "ectopic pregnancy", "ovarian cyst",
        "adnexal mass", "ovarian torsion", "pelvic inflammatory disease", "pid",
        "tubo-ovarian abscess", "endometriosis", "adenomyosis", "uterine fibroid",
        "leiomyoma", "dysmenorrhea", "dyspareunia", "pcos", "polycystic ovary",
        "cervical dysplasia", "pap smear", "postmenopausal bleeding", "cervical motion tenderness"
    ]

    @classmethod
    def route_case(cls, case_data: Any) -> RoutingDecision:
        """
        Analyzes clinical presentation and routes patient to the appropriate specialty.
        Accepts PatientGroundTruth or dictionary.
        """
        if hasattr(case_data, "chief_complaint"):
            complaint = str(case_data.chief_complaint or "")
            hpi = str(getattr(case_data, "history_of_present_illness", "") or "")
            pmh = list(getattr(case_data, "past_medical_history", []) or [])
        elif isinstance(case_data, dict):
            complaint = str(case_data.get("chief_complaint") or "")
            hpi = str(case_data.get("history_of_present_illness") or case_data.get("hpi") or "")
            pmh = list(case_data.get("past_medical_history") or [])
        else:
            complaint = str(case_data)
            hpi = ""
            pmh = []

        combined_text = f"{complaint.lower()} {hpi.lower()} {' '.join(str(p).lower() for p in pmh)}"

        em_hits = [k for k in cls.EMERGENCY_KEYWORDS if k in combined_text]
        cardio_hits = [k for k in cls.CARDIOLOGY_KEYWORDS if k in combined_text]
        surgery_hits = [k for k in cls.SURGERY_KEYWORDS if k in combined_text]
        gyn_hits = [k for k in cls.GYNECOLOGY_KEYWORDS if k in combined_text]
        id_hits = [k for k in cls.INFECTIOUS_DISEASES_KEYWORDS if k in combined_text]
        im_hits = [k for k in cls.INTERNAL_MEDICINE_KEYWORDS if k in combined_text]

        # Score weights: complaint hits count for 2, HPI/PMH hits count for 1
        em_score = sum(2 if k in complaint.lower() else 1 for k in em_hits)
        cardio_score = sum(2 if k in complaint.lower() else 1 for k in cardio_hits)
        surgery_score = sum(2 if k in complaint.lower() else 1 for k in surgery_hits)
        gyn_score = sum(2 if k in complaint.lower() else 1 for k in gyn_hits)
        id_score = sum(2 if k in complaint.lower() else 1 for k in id_hits)
        im_score = sum(2 if k in complaint.lower() else 1 for k in im_hits)

        # High-acuity resuscitation triggers take precedence
        is_immediate_resuscitation = any(
            k in complaint.lower() for k in [
                "anaphylaxis", "stridor", "angioedema", "cardiac arrest", "code blue",
                "tension pneumothorax", "polytrauma", "overdose", "poisoning", "status epilepticus",
                "unresponsive", "resuscitation", "aspiration", "rapid sequence intubation"
            ]
        )
        is_cardiac_emergency = any(
            k in complaint.lower() for k in ["chest pain", "angina", "infarction", "stemi", "nstemi", "substernal", "troponin"]
        )
        is_surgical_emergency = any(
            k in complaint.lower() for k in [
                "acute abdomen", "appendicitis", "peritonitis", "bowel obstruction",
                "strangulated", "incarcerated hernia", "perforation", "pneumoperitoneum"
            ]
        )
        is_gynecologic_primary = any(
            k in complaint.lower() for k in [
                "ectopic pregnancy", "vaginal bleeding", "abnormal uterine bleeding", "aub",
                "adnexal mass", "ovarian cyst", "ovarian torsion", "pelvic inflammatory disease",
                "pid", "tubo-ovarian abscess", "endometriosis", "uterine fibroid", "postmenopausal bleeding"
            ]
        )
        is_infectious_primary = any(
            k in complaint.lower() for k in [
                "fever of unknown origin", "fuo", "endocarditis", "bacteremia",
                "bloodstream infection", "osteomyelitis", "tuberculosis",
                "opportunistic infection", "c difficile", "c. diff", "mrsa bacteremia"
            ]
        )

        if is_immediate_resuscitation or (em_score > cardio_score and em_score > surgery_score and em_score > gyn_score and em_score > id_score and em_score > im_score):
            specialty = "EMERGENCY"
            specialist_name = "Dr. David Kim, MD, FACEP"
            book = "Tintinalli's Emergency Medicine Manual"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(em_hits)))
            rationale = f"Acute resuscitation / emergency pathology identified ({', '.join(em_hits[:3]) or 'emergency symptoms'}). Routed to Emergency Medicine."
            hits = em_hits
        elif is_cardiac_emergency or (cardio_score > surgery_score and cardio_score > gyn_score and cardio_score > id_score and cardio_score > im_score):
            specialty = "CARDIOLOGY"
            specialist_name = "Dr. Rachel Vance, MD, FACC"
            book = "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine (12th Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(cardio_hits)))
            rationale = f"Primary cardiovascular presentation identified ({', '.join(cardio_hits[:3]) or 'cardiac symptoms'}). Routed to Cardiology."
            hits = cardio_hits
        elif is_surgical_emergency or (surgery_score > gyn_score and surgery_score > id_score and surgery_score > im_score):
            specialty = "SURGERY"
            specialist_name = "Dr. Sarah Lin, MD, FACS"
            book = "Schwartz's Principles of Surgery (10th Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(surgery_hits)))
            rationale = f"Surgical pathology / acute abdomen identified ({', '.join(surgery_hits[:3]) or 'surgical symptoms'}). Routed to Surgery."
            hits = surgery_hits
        elif is_gynecologic_primary or (gyn_score > id_score and gyn_score > im_score):
            specialty = "GYNECOLOGY"
            specialist_name = "Dr. Evelyn Reed, MD, FACOG"
            book = "Williams Gynecology"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(gyn_hits)))
            rationale = f"Primary gynecologic / pelvic pathology identified ({', '.join(gyn_hits[:3]) or 'gynecologic symptoms'}). Routed to Gynecology."
            hits = gyn_hits
        elif is_infectious_primary or (id_score > im_score):
            specialty = "INFECTIOUS_DISEASES"
            specialist_name = "Dr. Anthony Mercer, MD, FIDSA"
            book = "Harrison's Infectious Diseases (Fauci & Kasper)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(id_hits)))
            rationale = f"Primary infectious / microbiological pathology identified ({', '.join(id_hits[:3]) or 'infectious symptoms'}). Routed to Infectious Diseases."
            hits = id_hits
        else:
            specialty = "INTERNAL_MEDICINE"
            specialist_name = "Dr. Marcus Vance, MD, FACP"
            book = "Harrison's Principles of Internal Medicine (21st Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(im_hits)))
            rationale = f"Multisystem / internal medicine pathology identified ({', '.join(im_hits[:3]) or 'general medical symptoms'}). Routed to Internal Medicine."
            hits = im_hits

        logger.info(f"Router decision for '{complaint[:40]}...': {specialty} (Confidence: {confidence:.2f}) -> {specialist_name}")

        return RoutingDecision(
            specialty=specialty,
            confidence=confidence,
            primary_rationale=rationale,
            matched_keywords=hits,
            suggested_specialist_name=specialist_name,
            target_medical_book=book,
        )
