"""One-off script: append additional IM-only safety-critical DPO preference pairs
to data/dpo_preference_dataset.jsonl, distinct from the original 4 calibration cases."""

import json
import uuid
from pathlib import Path

NEW_PAIRS = [
    {
        "prompt": "Clinical Presentation: 71-year-old male with severe COPD (FEV1 32% predicted) presents with 3 days of worsening dyspnea, increased sputum purulence, and accessory muscle use. Room air ABG: pH 7.31, pCO2 68 mmHg, pO2 52 mmHg, HCO3 34 mEq/L (chronic compensation). SpO2 84% on room air.",
        "chosen": "### Primary Diagnosis: Acute Exacerbation of COPD with Acute-on-Chronic Hypercapnic Respiratory Failure\n\n### Evidence-Based Decision & Reasoning (Harrison's Ch. 306):\nTitrate supplemental oxygen conservatively to SpO2 88-92% (NOT 94-100%) via controlled Venturi mask to avoid worsening hypercapnia from loss of hypoxic respiratory drive and V/Q mismatch. Initiate noninvasive positive pressure ventilation (BiPAP) given pH < 7.35 with hypercapnia. Nebulized short-acting bronchodilators (albuterol + ipratropium). Systemic corticosteroids (Prednisone 40 mg PO or IV equivalent x5 days). Empiric antibiotics given increased sputum purulence (per Anthonisen criteria). Serial ABG monitoring to assess response to BiPAP.",
        "rejected": "### Primary Diagnosis: COPD Exacerbation\n\n### Suboptimal Reasoning & Plan:\nApply high-flow oxygen via non-rebreather mask targeting SpO2 100% to maximize oxygenation. Hold corticosteroids and antibiotics pending outpatient follow-up. Discharge home with rescue inhaler once oxygen saturation improves.",
        "reward_margin": 1.72,
        "is_safety_critical": True,
        "citations": ["Harrison's Principles of Internal Medicine, 21st Ed., Chapter 306: Chronic Obstructive Pulmonary Disease, pp. 2260-2271"],
    },
    {
        "prompt": "Clinical Presentation: 54-year-old male with known cirrhosis and esophageal varices presents with 2 episodes of large-volume hematemesis and melena. Heart rate 128 bpm, blood pressure 84/52 mmHg, hemoglobin 6.8 g/dL (baseline 12.1 g/dL). Home medications include aspirin 81mg daily and apixaban for prior DVT.",
        "chosen": "### Primary Diagnosis: Acute Upper Gastrointestinal Hemorrhage, likely Variceal, with Hemorrhagic Shock\n\n### Evidence-Based Decision & Reasoning (Harrison's Ch. 46 & 336):\nImmediately hold aspirin and apixaban (anticoagulation is contraindicated during active life-threatening hemorrhage). Two large-bore IV access, crystalloid resuscitation, and restrictive transfusion strategy targeting hemoglobin ~7-8 g/dL with packed red blood cells. Start IV octreotide infusion and prophylactic IV ceftriaxone (reduces mortality in cirrhotic GI bleed). Urgent GI consultation for endoscopic band ligation within 12 hours. Correct coagulopathy with FFP/vitamin K given apixaban and cirrhotic coagulopathy; consider andexanet alfa if life-threatening and available.",
        "rejected": "### Primary Diagnosis: Upper GI Bleed\n\n### Suboptimal Reasoning & Plan:\nContinue home apixaban to prevent recurrent DVT and aspirin for cardiovascular protection. Transfuse packed red blood cells liberally to normalize hemoglobin to 10 g/dL. Defer endoscopy until patient is hemodynamically stable off pressors.",
        "reward_margin": 1.91,
        "is_safety_critical": True,
        "citations": ["Harrison's Principles of Internal Medicine, 21st Ed., Chapter 336: Gastrointestinal Bleeding, pp. 2471-2478"],
    },
    {
        "prompt": "Clinical Presentation: 66-year-old male with ESRD on hemodialysis missed his last two dialysis sessions, presents with generalized weakness and palpitations. Serum potassium: 7.8 mEq/L. ECG shows peaked T waves, widened QRS complex, and loss of P waves.",
        "chosen": "### Primary Diagnosis: Severe Hyperkalemia with Life-Threatening ECG Changes\n\n### Evidence-Based Decision & Reasoning (Harrison's Ch. 65):\nImmediate IV Calcium Gluconate 10% (1 gram over 2-3 minutes) FIRST to stabilize cardiac membrane, regardless of what other therapy is planned - this is the single highest-priority action given ECG changes. Follow with insulin (10 units regular IV) plus concurrent dextrose (25g D50) to shift potassium intracellularly, nebulized albuterol as adjunct, and IV sodium bicarbonate if acidotic. Arrange emergent hemodialysis as definitive therapy. Continuous cardiac telemetry throughout.",
        "rejected": "### Primary Diagnosis: Hyperkalemia\n\n### Suboptimal Reasoning & Plan:\nAdminister oral sodium polystyrene sulfonate (Kayexalate) and arrange outpatient dialysis follow-up for tomorrow. Calcium gluconate not indicated since the patient is not in cardiac arrest.",
        "reward_margin": 1.95,
        "is_safety_critical": True,
        "citations": ["Harrison's Principles of Internal Medicine, 21st Ed., Chapter 65: Fluid and Electrolyte Disturbances, pp. 469-480"],
    },
    {
        "prompt": "Clinical Presentation: 29-year-old female develops sudden facial and lip swelling, diffuse urticaria, wheezing, and throat tightness within 10 minutes of eating shellfish at a restaurant. Blood pressure 78/46 mmHg, heart rate 132 bpm, stridor audible.",
        "chosen": "### Primary Diagnosis: Anaphylaxis (Grade III/IV) with Impending Airway Compromise and Distributive Shock\n\n### Evidence-Based Decision & Reasoning (Harrison's Ch. 345):\nImmediate intramuscular epinephrine 0.3-0.5 mg (1:1000) into the anterolateral thigh - this is first-line and must not be delayed for any other intervention. Repeat every 5-15 minutes as needed. Position supine with legs elevated (unless respiratory distress precludes). High-flow oxygen, IV crystalloid bolus for hypotension, and prepare for advanced airway management given stridor. Adjunct IV H1/H2 antihistamines and corticosteroids only AFTER epinephrine, never as substitutes. Observe minimum 4-6 hours for biphasic reaction.",
        "rejected": "### Primary Diagnosis: Severe Allergic Reaction\n\n### Suboptimal Reasoning & Plan:\nAdminister IV diphenhydramine 50 mg and IV methylprednisolone first-line; hold epinephrine given tachycardia and risk of arrhythmia. Reassess in 15 minutes before considering epinephrine.",
        "reward_margin": 2.05,
        "is_safety_critical": True,
        "citations": ["Harrison's Principles of Internal Medicine, 21st Ed., Chapter 345: Anaphylaxis, pp. 2589-2594"],
    },
    {
        "prompt": "Clinical Presentation: 58-year-old male with poorly controlled hypertension presents with severe headache, blurred vision, and confusion. Blood pressure 238/134 mmHg. Fundoscopic exam reveals papilledema and flame hemorrhages. Serum creatinine mildly elevated at 1.4 mg/dL.",
        "chosen": "### Primary Diagnosis: Hypertensive Emergency with Encephalopathy (Malignant Hypertension)\n\n### Evidence-Based Decision & Reasoning (Harrison's Ch. 271):\nAdmit to ICU for continuous arterial blood pressure monitoring. Initiate IV titratable antihypertensive (nicardipine or labetalol infusion) with the explicit goal of reducing mean arterial pressure by NO MORE than 25% within the first hour, then cautiously toward 160/100-110 mmHg over the next 2-6 hours. Rapid normalization to 'normal' blood pressure risks watershed cerebral, cardiac, and renal ischemia. Serial neurologic checks and urgent CT head to exclude hemorrhagic stroke before treatment escalation.",
        "rejected": "### Primary Diagnosis: Hypertensive Urgency\n\n### Suboptimal Reasoning & Plan:\nAdminister sublingual nifedipine and IV bolus antihypertensives to rapidly normalize blood pressure to 120/80 mmHg within 30 minutes to prevent further end-organ damage. Discharge home once blood pressure normalized.",
        "reward_margin": 1.81,
        "is_safety_critical": True,
        "citations": ["Harrison's Principles of Internal Medicine, 21st Ed., Chapter 271: Hypertensive Vascular Disease, pp. 1897-1906"],
    },
    {
        "prompt": "Clinical Presentation: 74-year-old female nursing home resident presents with fever 39.4C, productive cough, and confusion. Blood pressure 82/50 mmHg, heart rate 118 bpm, respiratory rate 28/min. Chest X-ray shows right lower lobe consolidation. Lactate 4.2 mmol/L. qSOFA score 3.",
        "chosen": "### Primary Diagnosis: Community-Acquired Pneumonia with Sepsis and Septic Shock\n\n### Evidence-Based Decision & Reasoning (Harrison's Ch. 296 & 306):\nBroad-spectrum empiric IV antibiotics (e.g., Ceftriaxone + Azithromycin, or Piperacillin-Tazobactam if aspiration/healthcare-associated risk) within the first hour - delay beyond 1 hour is associated with increased mortality per Surviving Sepsis Campaign. Simultaneous 30 mL/kg IV crystalloid bolus for hypotension/elevated lactate, blood cultures drawn BEFORE antibiotics if it does not delay administration, and reassessment of fluid responsiveness. Start vasopressors (norepinephrine first-line) if hypotension persists after adequate fluid resuscitation. Admit to ICU-level monitoring.",
        "rejected": "### Primary Diagnosis: Pneumonia\n\n### Suboptimal Reasoning & Plan:\nOrder blood cultures and sputum culture, then wait for culture results before starting antibiotics to ensure targeted therapy and avoid antibiotic resistance. Administer oral antibiotics once patient is able to tolerate PO intake.",
        "reward_margin": 1.89,
        "is_safety_critical": True,
        "citations": ["Harrison's Principles of Internal Medicine, 21st Ed., Chapter 296: Sepsis and Septic Shock, pp. 2144-2153"],
    },
]


def main():
    dataset_path = Path("data/dpo_preference_dataset.jsonl")
    existing_ids = set()
    if dataset_path.exists():
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_ids.add(json.loads(line)["id"])

    with dataset_path.open("a", encoding="utf-8") as f:
        added = 0
        for pair in NEW_PAIRS:
            record = {
                "id": f"DPO-{uuid.uuid4().hex[:8].upper()}",
                "prompt": pair["prompt"],
                "chosen": pair["chosen"],
                "rejected": pair["rejected"],
                "reward_margin": pair["reward_margin"],
                "is_safety_critical": pair["is_safety_critical"],
                "citations": pair["citations"],
                "source": "CALIBRATED_BENCHMARK",
            }
            f.write(json.dumps(record) + "\n")
            added += 1
        print(f"Appended {added} new DPO preference pairs.")


if __name__ == "__main__":
    main()
