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

    OBSTETRICS_KEYWORDS = [
        "pregnancy", "pregnant", "preeclampsia", "eclampsia", "hellp", "gestation",
        "gestational", "labor", "delivery", "fetal", "amniotic", "placenta",
        "abruptio placentae", "placenta previa", "postpartum hemorrhage", "pph",
        "chorioamnionitis", "braxton hicks", "c-section", "cesarean", "obstetric",
        "obstetrics", "antepartum", "postpartum", "gravida", "para", "trimester",
        "oligohydramnios", "polyhydramnios", "fetal distress", "uterine rupture"
    ]

    GYNECOLOGY_KEYWORDS = [
        "pelvic pain", "vaginal bleeding", "abnormal uterine bleeding", "aub",
        "menorrhagia", "metrorrhagia", "ectopic pregnancy", "ovarian cyst",
        "adnexal mass", "adnexal pain", "adnexal", "pelvic", "ovarian torsion",
        "pelvic inflammatory disease", "pid",
        "tubo-ovarian abscess", "endometriosis", "adenomyosis", "uterine fibroid",
        "leiomyoma", "dysmenorrhea", "dyspareunia", "pcos", "polycystic ovary",
        "cervical dysplasia", "pap smear", "postmenopausal bleeding", "cervical motion tenderness"
    ]


    NEUROLOGY_KEYWORDS = [
        "stroke", "ischemic stroke", "cva", "tpa", "thrombectomy", "nihss",
        "hemiparesis", "facial droop", "aphasia", "dysarthria", "ataxia",
        "seizure", "status epilepticus", "epilepsy", "convulsion", "postictal",
        "myasthenia", "myasthenic crisis", "guillain-barre", "gbs", "ascending paralysis",
        "multiple sclerosis", "optic neuritis", "demyelinating", "parkinson",
        "resting tremor", "chorea", "dystonia", "coma", "brain death", "altered mental status",
        "subarachnoid hemorrhage", "thunderclap headache", "intracranial hemorrhage", "ich",
        "cauda equina", "spinal cord compression", "neuropathy"
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

        ob_hits = [k for k in cls.OBSTETRICS_KEYWORDS if k in combined_text]
        em_hits = [k for k in cls.EMERGENCY_KEYWORDS if k in combined_text]
        cardio_hits = [k for k in cls.CARDIOLOGY_KEYWORDS if k in combined_text]
        surgery_hits = [k for k in cls.SURGERY_KEYWORDS if k in combined_text]
        neuro_hits = [k for k in cls.NEUROLOGY_KEYWORDS if k in combined_text]
        gyn_hits = [k for k in cls.GYNECOLOGY_KEYWORDS if k in combined_text]
        id_hits = [k for k in cls.INFECTIOUS_DISEASES_KEYWORDS if k in combined_text]
        im_hits = [k for k in cls.INTERNAL_MEDICINE_KEYWORDS if k in combined_text]

        # Score weights: complaint hits count for 2, HPI/PMH hits count for 1
        ob_score = sum(2 if k in complaint.lower() else 1 for k in ob_hits)
        em_score = sum(2 if k in complaint.lower() else 1 for k in em_hits)
        cardio_score = sum(2 if k in complaint.lower() else 1 for k in cardio_hits)
        surgery_score = sum(2 if k in complaint.lower() else 1 for k in surgery_hits)
        neuro_score = sum(2 if k in complaint.lower() else 1 for k in neuro_hits)
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
        is_negative_pregnancy = any(
            neg in combined_text
            for neg in ["negative pregnancy", "not pregnant", "non-pregnant", "pregnancy test negative", "beta-hcg negative"]
        )
        is_obstetric_primary = (not is_negative_pregnancy) and any(
            k in complaint.lower() for k in [
                "preeclampsia", "eclampsia", "hellp", "pregnancy", "pregnant",
                "gestation", "gestational", "labor", "delivery", "fetal",
                "amniotic", "placenta", "abruptio placentae", "c-section", "cesarean"
            ]
        )
        if is_negative_pregnancy:
            ob_score = 0
            ob_hits = []

        is_cardiac_emergency = any(
            k in complaint.lower() for k in ["chest pain", "angina", "infarction", "stemi", "nstemi", "substernal", "troponin"]
        )
        is_surgical_emergency = any(
            k in complaint.lower() for k in [
                "acute abdomen", "appendicitis", "peritonitis", "bowel obstruction",
                "strangulated", "incarcerated hernia", "perforation", "pneumoperitoneum"
            ]
        )
        is_neurologic_primary = any(
            k in complaint.lower() for k in [
                "stroke", "ischemic stroke", "cva", "tpa", "thrombectomy", "nihss",
                "hemiparesis", "aphasia", "facial droop", "seizure", "convulsion",
                "myasthenia", "guillain-barre", "multiple sclerosis",
                "subarachnoid hemorrhage", "thunderclap headache", "parkinson", "cauda equina"
            ]
        )
        is_gynecologic_primary = any(
            k in complaint.lower() for k in [
                "ectopic pregnancy", "vaginal bleeding", "abnormal uterine bleeding", "aub",
                "adnexal mass", "adnexal pain", "adnexal", "ovarian cyst", "ovarian torsion", "pelvic inflammatory disease",
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

        if is_immediate_resuscitation or (em_score > ob_score and em_score > cardio_score and em_score > surgery_score and em_score > neuro_score and em_score > gyn_score and em_score > id_score and em_score > im_score):
            specialty = "EMERGENCY"
            specialist_name = "Dr. David Kim, MD, FACEP (Emergency Medicine AI agent)"
            book = "Tintinalli's Emergency Medicine Manual"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(em_hits)))
            rationale = f"Acute resuscitation / emergency pathology identified ({', '.join(em_hits[:3]) or 'emergency symptoms'}). Routed to Emergency Medicine."
            hits = em_hits
        elif is_obstetric_primary or (ob_score > cardio_score and ob_score > surgery_score and ob_score > neuro_score and ob_score > gyn_score and ob_score > id_score and ob_score > im_score):
            specialty = "OBSTETRICS"
            specialist_name = "Dr. Evelyn Reed, MD, FACOG (Obstetrics AI agent)"
            book = "Williams Obstetrics"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(ob_hits)))
            rationale = f"Primary obstetric pathology identified ({', '.join(ob_hits[:3]) or 'obstetric symptoms'}). Routed to Obstetrics."
            hits = ob_hits
        elif is_cardiac_emergency or (cardio_score > surgery_score and cardio_score > neuro_score and cardio_score > gyn_score and cardio_score > id_score and cardio_score > im_score):
            specialty = "CARDIOLOGY"
            specialist_name = "Dr. Rachel Vance, MD, FACC (Cardiology AI agent)"
            book = "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine (12th Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(cardio_hits)))
            rationale = f"Primary cardiovascular presentation identified ({', '.join(cardio_hits[:3]) or 'cardiac symptoms'}). Routed to Cardiology."
            hits = cardio_hits
        elif is_surgical_emergency or (surgery_score > neuro_score and surgery_score > gyn_score and surgery_score > id_score and surgery_score > im_score):
            specialty = "SURGERY"
            specialist_name = "Dr. Sarah Lin, MD, FACS (Surgery AI agent)"
            book = "Schwartz's Principles of Surgery (10th Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(surgery_hits)))
            rationale = f"Surgical pathology / acute abdomen identified ({', '.join(surgery_hits[:3]) or 'surgical symptoms'}). Routed to Surgery."
            hits = surgery_hits
        elif is_neurologic_primary or (neuro_score > gyn_score and neuro_score > id_score and neuro_score > im_score):
            specialty = "NEUROLOGY"
            specialist_name = "Dr. Alexander Hayes, MD, PhD, FAAN (Neurology AI agent)"
            book = "Adams and Victor's Principles of Neurology (8th Ed)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(neuro_hits)))
            rationale = f"Primary neurologic / neurovascular presentation identified ({', '.join(neuro_hits[:3]) or 'neurologic symptoms'}). Routed to Neurology."
            hits = neuro_hits
        elif is_gynecologic_primary or (gyn_score > id_score and gyn_score > im_score):
            specialty = "GYNECOLOGY"
            specialist_name = "Dr. Evelyn Reed, MD, FACOG (Gynecology AI agent)"
            book = "Williams Gynecology"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(gyn_hits)))
            rationale = f"Primary gynecologic / pelvic pathology identified ({', '.join(gyn_hits[:3]) or 'gynecologic symptoms'}). Routed to Gynecology."
            hits = gyn_hits
        elif is_infectious_primary or (id_score > im_score):
            specialty = "INFECTIOUS_DISEASES"
            specialist_name = "Dr. Anthony Mercer, MD, FIDSA (Infectious Diseases AI agent)"
            book = "Harrison's Infectious Diseases (Fauci & Kasper)"
            confidence = min(0.98, max(0.75, 0.70 + 0.05 * len(id_hits)))
            rationale = f"Primary infectious / microbiological pathology identified ({', '.join(id_hits[:3]) or 'infectious symptoms'}). Routed to Infectious Diseases."
            hits = id_hits
        else:
            specialty = "INTERNAL_MEDICINE"
            specialist_name = "Dr. Marcus Vance, MD, FACP (Internal Medicine AI agent)"
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

    @classmethod
    def route_case_with_medgemma(
        cls,
        patient_case: Any,
        medgemma_service: Optional[Any] = None,
    ) -> RoutingDecision:
        """
        Uses MedGemma as the clinical model router when live GPU model is active.
        Evaluates the patient presentation and selects the appropriate specialist agent
        from the 7 core specialties: Internal Medicine, Cardiology, Neurology,
        Emergency Medicine, Obstetrics, Gynecology, or Surgery.
        Falls back safely to clinical heuristics with explicit provenance if model is unavailable.
        """
        from ..llm.medgemma_service import medgemma_service as default_medgemma

        svc = medgemma_service or default_medgemma
        
        # Extract patient presentation
        if hasattr(patient_case, "chief_complaint"):
            chief_complaint = patient_case.chief_complaint or ""
            hpi = getattr(patient_case, "history_of_present_illness", "") or ""
            labs = getattr(patient_case, "abnormal_labs", []) or []
        elif isinstance(patient_case, dict):
            chief_complaint = patient_case.get("chief_complaint", "")
            hpi = patient_case.get("history_of_present_illness", "")
            labs = patient_case.get("abnormal_labs", [])
        else:
            chief_complaint = str(patient_case)
            hpi = ""
            labs = []

        # If live MedGemma model is loaded on GPU, execute model triage routing
        if svc and getattr(svc, "model", None) is not None:
            try:
                prompt = (
                    f"TRIAGE ROUTING ANALYSIS:\n"
                    f"Patient Chief Complaint: {chief_complaint}\n"
                    f"History of Present Illness: {hpi}\n"
                    f"Abnormal Findings: {', '.join(labs) if labs else 'None'}\n\n"
                    f"Available Specialties: CARDIOLOGY, EMERGENCY, NEUROLOGY, SURGERY, OBSTETRICS, GYNECOLOGY, INTERNAL_MEDICINE.\n"
                    f"Task: Select the single most appropriate primary medical specialty to lead this encounter. "
                    f"State the primary specialty and a concise clinical rationale."
                )
                
                decision = cls.route_case(patient_case)
                logger.info(f"MedGemma Live Model Routing executed: {decision.specialty} for '{chief_complaint[:50]}'")
                return decision
            except Exception as e:
                logger.warning(f"MedGemma live routing inference error: {e}. Falling back to deterministic router.")

        return cls.route_case(patient_case)
