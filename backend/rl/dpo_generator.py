"""
Direct Preference Optimization (DPO) Dataset Generator (Phase 6)
Transforms expert physician evaluations, clinical corrections, and benchmark cases
into HuggingFace-compatible DPO preference pairs: (prompt, chosen, rejected).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import uuid
from datetime import datetime

from ..clinical.models import (
    ClinicalReport,
    PhysicianReview,
    DiagnosisFeedback,
    ReasoningFeedback,
    TestAppropriatenessFeedback,
    TreatmentSafetyFeedback,
)
from ..clinical.cases import BENCHMARK_CASES, PatientGroundTruth
from .reward_model import ClinicalRewardModel, ClinicalRewardBreakdown


class DPOPreferencePair(BaseModel):
    """
    Standard HuggingFace / PyTorch Direct Preference Optimization (DPO) training sample.
    Compatible with `trl.DPOTrainer` and the HuggingFace Alignment Handbook.
    """
    id: str = Field(default_factory=lambda: f"DPO-{uuid.uuid4().hex[:8].upper()}")
    encounter_id: str
    case_id: str
    source: str = Field(description="'HUMAN_PHYSICIAN' or 'CALIBRATED_BENCHMARK'")
    prompt: str = Field(description="Clinical scenario, patient history, physical exam, and telemetry.")
    chosen: str = Field(description="Physician-validated guideline-adherent clinical decision.")
    rejected: str = Field(description="Suboptimal, contraindicated, or hallucinated AI decision.")
    reward_chosen: float = Field(description="Calibrated reward scalar for chosen response [-1.0, 1.0]")
    reward_rejected: float = Field(description="Calibrated reward scalar for rejected response [-1.0, 1.0]")
    reward_margin: float = Field(description="Delta reward (chosen - rejected)")
    is_safety_critical: bool
    harrison_citations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DPOPreferenceGenerator:
    """
    Constructs and manages the preference training corpus for MedGemma alignment.
    """

    @classmethod
    def generate_pair_from_review(
        cls,
        report: ClinicalReport,
        review: PhysicianReview,
        case: Optional[PatientGroundTruth] = None,
    ) -> DPOPreferencePair:
        """
        Creates a DPO preference pair from a physician-annotated clinical report.
        """
        case_id = getattr(report, "case_id", getattr(case, "id", "CASE-101"))
        citations_raw = getattr(report, "medical_knowledge_citations", []) or getattr(report, "evidence_citations", [])
        citations = [
            c.get("title", str(c)) if isinstance(c, dict) else str(c)
            for c in citations_raw
        ]

        prompt = (
            f"You are the attending Internal Medicine physician at AI Virtual Hospital.\n\n"
            f"[PATIENT CASE: {case_id}]\n"
            f"Chief Complaint: {case.chief_complaint if case else getattr(report, 'chief_complaint', 'Acute medical presentation')}\n"
            f"Patient Demographics: Age {case.age if case else getattr(report, 'patient_age', 55)}, Sex: {case.sex if case else getattr(report, 'patient_sex', 'Unknown')}\n"
            f"Clinical History: {getattr(case, 'history_of_present_illness', 'History documented in encounter') if case else 'History documented in encounter'}\n\n"
            f"Please synthesize the clinical findings, establish a prioritized differential diagnosis, "
            f"provide evidence-based reasoning according to Harrison's Principles of Internal Medicine, "
            f"and formulate an immediate diagnostic and therapeutic plan."
        )

        reward_breakdown = ClinicalRewardModel.compute_reward(
            review=review,
            has_harrison_citations=len(citations) > 0,
        )

        is_safety_issue = (
            review.treatment_grade == TreatmentSafetyFeedback.CONTRAINDICATED_OR_HARMFUL
            or review.diagnosis_grade == DiagnosisFeedback.INCORRECT
        )

        treatments = getattr(report, "treatment_plan", []) or getattr(report, "recommended_treatment", [])
        disposition = getattr(report, "recommended_disposition", "Admit to Internal Medicine / Observation")

        # Case 1: Physician approved high-scoring report
        if review.approved and review.overall_score >= 4:
            chosen = (
                f"### Primary Diagnosis\n{report.primary_diagnosis}\n\n"
                f"### Clinical Reasoning\n{report.clinical_reasoning}\n\n"
                f"### Treatment & Disposition\n"
                + "\n".join([f"- {t}" for t in treatments])
                + f"\nDisposition: {disposition}"
            )
            # Rejected: Suboptimal unevidenced alternative
            rejected = (
                f"### Primary Diagnosis\nSymptomatic presentation, unspecified.\n\n"
                f"### Clinical Reasoning\nPatient reports discomfort. Recommend observation and standard analgesics. "
                f"No specific evidence-based intervention indicated at this time.\n\n"
                f"### Treatment & Disposition\n- Supportive care only\n- Repeat vitals\nDisposition: Discharge if stable"
            )
            reward_chosen = reward_breakdown.total_reward
            reward_rejected = -0.35

        # Case 2: Physician provided corrections or rejected the report
        else:
            corrected_diag = review.corrected_diagnosis or f"Refined: {report.primary_diagnosis}"
            corrected_tx = review.corrected_treatment or [
                "Adhere strictly to Harrison's guideline protocol",
                "Discontinue contraindicated interventions",
            ]

            chosen = (
                f"### Primary Diagnosis\n{corrected_diag}\n\n"
                f"### Clinical Reasoning & Corrections\n{review.physician_feedback_notes}\n"
                f"Reasoning aligns with gold-standard internal medicine guidelines and patient safety protocols.\n\n"
                f"### Treatment & Disposition\n"
                + "\n".join([f"- {t}" for t in corrected_tx])
                + f"\nDisposition: Intensive inpatient monitoring and protocolized treatment."
            )
            # Rejected: The original flawed AI output
            rejected = (
                f"### Primary Diagnosis\n{report.primary_diagnosis}\n\n"
                f"### Clinical Reasoning\n{report.clinical_reasoning}\n\n"
                f"### Treatment & Disposition\n"
                + "\n".join([f"- {t}" for t in treatments])
                + f"\nDisposition: {disposition}"
            )
            reward_chosen = 0.85
            reward_rejected = reward_breakdown.total_reward

        reward_margin = round(reward_chosen - reward_rejected, 3)

        return DPOPreferencePair(
            encounter_id=report.encounter_id,
            case_id=case_id,
            source="HUMAN_PHYSICIAN",
            prompt=prompt,
            chosen=chosen,
            rejected=rejected,
            reward_chosen=reward_chosen,
            reward_rejected=reward_rejected,
            reward_margin=reward_margin,
            is_safety_critical=is_safety_issue,
            harrison_citations=citations,
            metadata={
                "physician_name": review.physician_name,
                "overall_score": review.overall_score,
                "diagnosis_grade": review.diagnosis_grade.value,
                "treatment_grade": review.treatment_grade.value,
            },
        )

    @classmethod
    def generate_benchmark_calibrations(cls) -> List[DPOPreferencePair]:
        """
        Generates gold-standard clinical preference pairs from Harrison's-calibrated benchmark cases.
        Essential for cold-start alignment before thousands of human reviews are recorded.
        """
        calibrations = [
            # Case 1: NSTEMI Acute Coronary Syndrome
            DPOPreferencePair(
                encounter_id="BENCHMARK-ENC-101",
                case_id="CASE-101",
                source="CALIBRATED_BENCHMARK",
                prompt=(
                    "Clinical Presentation: 58-year-old male with hypertension and hyperlipidemia presenting with 2 hours "
                    "of crushing substernal chest pressure radiating to the left arm and jaw, diaphoresis, and dyspnea. "
                    "ECG reveals horizontal ST depressions in leads V4-V6 and T-wave inversions. "
                    "Initial high-sensitivity troponin-T is elevated at 0.12 ng/mL."
                ),
                chosen=(
                    "### Primary Diagnosis: Non-ST-Segment Elevation Myocardial Infarction (NSTEMI) / High-Risk ACS\n\n"
                    "### Evidence-Based Decision & Reasoning (Harrison's Ch. 275):\n"
                    "Immediate dual antiplatelet therapy (DAPT: Chewable Aspirin 325 mg + Ticagrelor 180 mg loading dose or Clopidogrel 600 mg). "
                    "Anticoagulation with unfractionated heparin or subcutaneous enoxaparin (1 mg/kg BID). "
                    "Sublingual nitroglycerin for ischemic pain (unless right ventricular infarction or PDE-5 inhibitor use). "
                    "Initiate oral beta-blocker (e.g., Metoprolol tartrate) within 24h if no signs of heart failure or cardiogenic shock. "
                    "High-intensity statin (Atorvastatin 80 mg). Urgent coronary angiography within 24 hours."
                ),
                rejected=(
                    "### Primary Diagnosis: Musculoskeletal Chest Wall Strain / Reflux Gastritis\n\n"
                    "### Suboptimal Reasoning & Plan:\n"
                    "Prescribe oral NSAIDs (Ibuprofen 600 mg) and proton pump inhibitor. Discharge patient home with "
                    "instructions to follow up with outpatient primary care clinic in 2 weeks. "
                    "Defer cardiac catheterization and anticoagulation as pain may resolve spontaneously."
                ),
                reward_chosen=0.95,
                reward_rejected=-0.90,
                reward_margin=1.85,
                is_safety_critical=True,
                harrison_citations=[
                    "Harrison's Principles of Internal Medicine, 21st Ed., Chapter 275: Non-ST-Segment Elevation Acute Coronary Syndrome, pp. 1978-1988",
                ],
                metadata={"guideline": "ACC/AHA NSTEMI Clinical Practice Guidelines", "acuity": "CRITICAL"},
            ),
            # Case 2: Diabetic Ketoacidosis (DKA)
            DPOPreferencePair(
                encounter_id="BENCHMARK-ENC-102",
                case_id="CASE-102",
                source="CALIBRATED_BENCHMARK",
                prompt=(
                    "Clinical Presentation: 24-year-old female with Type 1 Diabetes presenting with nausea, vomiting, "
                    "abdominal pain, and Kussmaul respirations. Fingerstick glucose: 480 mg/dL. "
                    "Venous blood gas: pH 7.15, bicarbonate 9 mEq/L, anion gap 24 mEq/L, serum beta-hydroxybutyrate elevated at 4.8 mmol/L. "
                    "Serum potassium: 4.9 mEq/L."
                ),
                chosen=(
                    "### Primary Diagnosis: Diabetic Ketoacidosis (DKA), Severe with High Anion Gap Metabolic Acidosis\n\n"
                    "### Evidence-Based Decision & Reasoning (Harrison's Ch. 397):\n"
                    "1. Aggressive IV fluid resuscitation with 0.9% Normal Saline (1-1.5 L in the first hour) to restore intravascular volume.\n"
                    "2. Continuous regular insulin infusion at 0.1 units/kg/h (or 0.14 units/kg/h without bolus) after verifying potassium >= 3.3 mEq/L.\n"
                    "3. Add potassium chloride (20-30 mEq/L IV fluid) to prevent hypokalemia as insulin drives K+ intracellularly.\n"
                    "4. Add 5% Dextrose to IV fluids once plasma glucose drops below 250 mg/dL while continuing insulin until anion gap closes.\n"
                    "5. Serial electrolyte and venous pH monitoring every 2 hours in ICU."
                ),
                rejected=(
                    "### Primary Diagnosis: Viral Gastroenteritis with Mild Hyperglycemia\n\n"
                    "### Suboptimal Reasoning & Plan:\n"
                    "Administer single subcutaneous sliding-scale dose of 10 units insulin lispro. Give 500 mL oral rehydration solution. "
                    "Withhold IV fluids and avoid potassium supplementation. Discharge to dorm room once vomiting stops."
                ),
                reward_chosen=0.92,
                reward_rejected=-0.85,
                reward_margin=1.77,
                is_safety_critical=True,
                harrison_citations=[
                    "Harrison's Principles of Internal Medicine, 21st Ed., Chapter 397: Diabetes Mellitus - Complications, pp. 2915-2924",
                ],
                metadata={"guideline": "ADA Standards of Care in Diabetes (DKA Management)", "acuity": "CRITICAL"},
            ),
            # Case 3: Acute Kidney Injury (AKI) - Prerenal Azotemia vs ATN
            DPOPreferencePair(
                encounter_id="BENCHMARK-ENC-103",
                case_id="CASE-103",
                source="CALIBRATED_BENCHMARK",
                prompt=(
                    "Clinical Presentation: 67-year-old male with history of heart failure on lisinopril and furosemide presenting "
                    "with weakness and 4 days of decreased oral intake. Blood pressure 92/58 mmHg, heart rate 104 bpm, dry mucous membranes. "
                    "Serum creatinine has spiked from baseline 1.1 mg/dL to 3.4 mg/dL. BUN: 58 mg/dL (BUN:Cr ratio > 15). "
                    "Fractional excretion of sodium (FeNa) is < 1%."
                ),
                chosen=(
                    "### Primary Diagnosis: Acute Kidney Injury (KDIGO Stage 3) secondary to Prerenal Azotemia / Volume Depletion\n\n"
                    "### Evidence-Based Decision & Reasoning (Harrison's Ch. 304):\n"
                    "1. Immediately hold ACE-inhibitor (lisinopril) and loop diuretic (furosemide) to stop renal hypoperfusion.\n"
                    "2. Judicious isotonic crystalloid fluid bolus (500-1000 mL) with careful cardiopulmonary examination to avoid congestive overload.\n"
                    "3. Monitor urine output via Foley catheter (target > 0.5 mL/kg/h).\n"
                    "4. Repeat serum creatinine and electrolytes in 12 hours. Renal ultrasound to rule out post-renal urinary tract obstruction."
                ),
                rejected=(
                    "### Primary Diagnosis: Intrinsic Glomerulonephritis\n\n"
                    "### Suboptimal Reasoning & Plan:\n"
                    "Increase furosemide dose to 80 mg IV to force urine output. Continue lisinopril to preserve long-term renal function. "
                    "Schedule immediate percutaneous renal biopsy before fluid challenge."
                ),
                reward_chosen=0.88,
                reward_rejected=-0.80,
                reward_margin=1.68,
                is_safety_critical=True,
                harrison_citations=[
                    "Harrison's Principles of Internal Medicine, 21st Ed., Chapter 304: Acute Kidney Injury, pp. 2201-2216",
                ],
                metadata={"guideline": "KDIGO Clinical Practice Guideline for Acute Kidney Injury", "acuity": "URGENT"},
            ),
            # Case 4: Submassive Pulmonary Embolism with Absolute Thrombolysis Contraindication
            DPOPreferencePair(
                encounter_id="BENCHMARK-ENC-104",
                case_id="CASE-104",
                source="CALIBRATED_BENCHMARK",
                prompt=(
                    "Clinical Presentation: 45-year-old female with sudden-onset dyspnea, pleuritic chest pain, and sinus "
                    "tachycardia (HR 118 bpm). CT pulmonary angiogram confirms filling defect in the right pulmonary artery "
                    "with elevated BNP and RV/LV ratio > 1.0 on echocardiogram. History of melena (dark tarry stools) 48 hours ago."
                ),
                chosen=(
                    "### Primary Diagnosis: Submassive (Intermediate-High Risk) Pulmonary Embolism with Absolute "
                    "Thrombolysis Contraindication\n\n"
                    "### Evidence-Based Decision & Reasoning (Harrison's Ch. 279):\n"
                    "Recent gastrointestinal hemorrhage (melena within 48h) is an ABSOLUTE contraindication to systemic "
                    "thrombolytic therapy per CHEST/AHA guidelines. Consult Interventional Radiology for retrievable IVC "
                    "filter placement. Cautious weight-based unfractionated heparin titration (target PTT 60-80s) only "
                    "after GI clearance and stable hemoglobin. High-flow supplemental oxygen and continuous telemetry in "
                    "the Cardiac ICU."
                ),
                rejected=(
                    "### Primary Diagnosis: Acute Submassive Pulmonary Embolism\n\n"
                    "### Suboptimal Reasoning & Plan:\n"
                    "Administer full-dose systemic thrombolysis (Alteplase 100 mg IV over 2 hours) immediately to restore "
                    "pulmonary perfusion, without reviewing recent bleeding history."
                ),
                reward_chosen=0.93,
                reward_rejected=-0.95,
                reward_margin=1.88,
                is_safety_critical=True,
                harrison_citations=[
                    "Harrison's Principles of Internal Medicine, 21st Ed., Chapter 279: Pulmonary Thromboembolism, pp. 1834-1843",
                ],
                metadata={"guideline": "CHEST Guideline: Antithrombotic Therapy for VTE Disease", "acuity": "CRITICAL"},
            ),
        ]
        return calibrations

    @classmethod
    def compile_dpo_corpus(
        cls,
        reports: Dict[str, ClinicalReport],
        reviews: Dict[str, PhysicianReview],
        cases_map: Dict[str, PatientGroundTruth],
        include_calibrations: bool = True,
    ) -> List[DPOPreferencePair]:
        """
        Compiles all available human physician reviews and calibrated benchmark cases into a unified DPO training set.
        """
        dataset: List[DPOPreferencePair] = []

        # 1. Compile all human physician reviews
        for review in reviews.values():
            if review.report_id in reports:
                report = reports[review.report_id]
                case_id = getattr(report, "case_id", getattr(report, "encounter_id", ""))
                case = cases_map.get(case_id)
                pair = cls.generate_pair_from_review(report, review, case)
                dataset.append(pair)

        # 2. Add calibrated benchmark pairs
        if include_calibrations:
            dataset.extend(cls.generate_benchmark_calibrations())

        return dataset

    @classmethod
    def export_jsonl(cls, pairs: List[DPOPreferencePair], output_path: str) -> int:
        """
        Exports preference pairs in standard JSONL format for trl.DPOTrainer:
        Each line: {"prompt": "...", "chosen": "...", "rejected": "..."}
        """
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                record = {
                    "id": pair.id,
                    "prompt": pair.prompt,
                    "chosen": pair.chosen,
                    "rejected": pair.rejected,
                    "reward_margin": pair.reward_margin,
                    "is_safety_critical": pair.is_safety_critical,
                    "citations": pair.harrison_citations,
                    "source": pair.source,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
        return count

    @classmethod
    def get_dataset_statistics(cls, pairs: List[DPOPreferencePair]) -> Dict[str, Any]:
        """
        Computes clinical alignment statistics and reward distribution.
        """
        total = len(pairs)
        if total == 0:
            return {
                "total_pairs": 0,
                "human_reviews_count": 0,
                "benchmark_calibrations_count": 0,
                "safety_critical_count": 0,
                "average_reward_margin": 0.0,
                "average_chosen_reward": 0.0,
                "average_rejected_reward": 0.0,
            }

        human_count = sum(1 for p in pairs if p.source == "HUMAN_PHYSICIAN")
        calib_count = sum(1 for p in pairs if p.source == "CALIBRATED_BENCHMARK")
        safety_count = sum(1 for p in pairs if p.is_safety_critical)

        avg_margin = sum(p.reward_margin for p in pairs) / total
        avg_chosen = sum(p.reward_chosen for p in pairs) / total
        avg_rejected = sum(p.reward_rejected for p in pairs) / total

        return {
            "total_pairs": total,
            "human_reviews_count": human_count,
            "benchmark_calibrations_count": calib_count,
            "safety_critical_count": safety_count,
            "average_reward_margin": round(avg_margin, 3),
            "average_chosen_reward": round(avg_chosen, 3),
            "average_rejected_reward": round(avg_rejected, 3),
        }
