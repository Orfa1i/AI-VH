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
        "aki", "oliguria", "sepsis", "bacteremia", "abdominal pain", "nausea",
        "vomiting", "diarrhea", "jaundice", "pancreatitis", "rash", "malaise",
        "fatigue", "weight loss", "anemia", "hyponatremia", "hyperkalemia"
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

        cardio_hits = [k for k in cls.CARDIOLOGY_KEYWORDS if k in combined_text]
        im_hits = [k for k in cls.INTERNAL_MEDICINE_KEYWORDS if k in combined_text]

        # Score weights: complaint hits count for 2, HPI/PMH hits count for 1
        cardio_score = sum(2 if k in complaint.lower() else 1 for k in cardio_hits)
        im_score = sum(2 if k in complaint.lower() else 1 for k in im_hits)

        # High-acuity cardiac triggers take precedent in emergency routing
        is_cardiac_emergency = any(
            k in complaint.lower() for k in ["chest pain", "angina", "infarction", "stemi", "nstemi", "substernal", "troponin"]
        )

        if is_cardiac_emergency or cardio_score > im_score:
            specialty = "CARDIOLOGY"
            specialist_name = "Dr. Rachel Vance, MD, FACC"
            book = "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine (12th Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(cardio_hits)))
            rationale = f"Primary cardiovascular presentation identified ({', '.join(cardio_hits[:3]) or 'cardiac symptoms'}). Routed to Cardiology."
            hits = cardio_hits
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
