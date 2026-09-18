"""
Benchmark Case Bank & Dynamic Case Generator
Defines clinical cases across Levels 1 to 5 with hidden clinical states and ground truth.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
from .models import VitalSigns, LabTestType, TriageAcuity


class PatientGroundTruth(BaseModel):
    id: str
    name: str
    age: int
    sex: str
    triage_acuity: TriageAcuity
    chief_complaint: str
    history_of_present_illness: str
    past_medical_history: List[str]
    medications: List[str]
    allergies: List[str]
    
    # Baseline Vitals
    baseline_vitals: VitalSigns
    
    # Ground Truth Clinical Data (hidden until ordered or examined)
    true_diagnosis: str
    icd10_code: str
    differential_candidates: List[str]
    recommended_labs: List[LabTestType]
    contraindicated_treatments: List[str] = Field(default_factory=list)
    optimal_treatment: List[str]
    
    # Simulated lab results bank for this specific pathology
    simulated_labs: Dict[str, Dict[str, Any]]
    
    # Physical exam findings
    physical_exam: Dict[str, str]


# Benchmark Cases
BENCHMARK_CASES: List[PatientGroundTruth] = [
    # Level 1: Acute Coronary Syndrome (STEMI / NSTEMI)
    PatientGroundTruth(
        id="CASE-101",
        name="Robert Miller",
        age=62,
        sex="Male",
        triage_acuity=TriageAcuity.EMERGENT,
        chief_complaint="Substernal crushing chest pressure radiating to left arm and jaw for 2 hours",
        history_of_present_illness="62-year-old male presents with sudden onset of severe substernal chest pressure that began 2 hours ago while mowing the lawn. Rated 8/10, radiating into his left shoulder and mandible. Associated with diaphoresis, nausea, and mild dyspnea. Pain unrelieved by rest.",
        past_medical_history=["Type 2 Diabetes Mellitus (12 yrs)", "Hypertension", "Dyslipidemia", "30-pack-year smoking history"],
        medications=["Metformin 1000mg BID", "Lisinopril 20mg daily", "Atorvastatin 40mg daily"],
        allergies=["Penicillin (hives)"],
        baseline_vitals=VitalSigns(
            heart_rate=102,
            systolic_bp=158,
            diastolic_bp=94,
            respiratory_rate=22,
            temperature_c=36.9,
            spo2_percent=95.0,
            pain_score=8
        ),
        true_diagnosis="Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)",
        icd10_code="I21.4",
        differential_candidates=[
            "Acute Coronary Syndrome (NSTEMI/STEMI)",
            "Aortic Dissection",
            "Pulmonary Embolism",
            "Gastroesophageal Reflux Disease (GERD)",
            "Acute Pericarditis"
        ],
        recommended_labs=[
            LabTestType.ECG_12_LEAD,
            LabTestType.TROPONIN_I,
            LabTestType.CBC,
            LabTestType.BMP,
            LabTestType.CXR
        ],
        contraindicated_treatments=["Beta-blockers if acutely hypotensive/decompensated", "NSAIDs other than Aspirin"],
        optimal_treatment=[
            "Aspirin 325mg chewable STAT",
            "Sublingual Nitroglycerin 0.4mg q5min (if BP > 100)",
            "Unfractionated Heparin bolus + continuous drip",
            "P2Y12 inhibitor (Ticagrelor or Clopidogrel)",
            "Urgent Cardiology consult for coronary angiography within 24h"
        ],
        simulated_labs={
            LabTestType.ECG_12_LEAD.value: {
                "rhythm": "Sinus Tachycardia at 104 bpm",
                "st_segments": "2mm ST-depression in leads V4-V6 and II, III, aVF with inverted T waves",
                "q_waves": "Absent",
                "impression": "Acute subendocardial ischemia consistent with NSTEMI"
            },
            LabTestType.TROPONIN_I.value: {
                "Troponin_I": "1.84 ng/mL",
                "reference_range": "< 0.04 ng/mL",
                "flag": "CRITICAL_HIGH",
                "interpretation": "Markedly elevated cardiac biomarkers indicating acute myocardial injury"
            },
            LabTestType.CBC.value: {
                "WBC": "9.8 x10^3/uL",
                "Hemoglobin": "14.2 g/dL",
                "Hematocrit": "42.5%",
                "Platelets": "240 x10^3/uL",
                "interpretation": "Normal hematologic parameters"
            },
            LabTestType.BMP.value: {
                "Sodium": "138 mEq/L",
                "Potassium": "4.2 mEq/L",
                "Chloride": "101 mEq/L",
                "Bicarbonate": "24 mEq/L",
                "BUN": "18 mg/dL",
                "Creatinine": "1.0 mg/dL",
                "Glucose": "172 mg/dL",
                "interpretation": "Mild hyperglycemia secondary to stress/diabetes; renal function intact"
            },
            LabTestType.CXR.value: {
                "cardiomegaly": "Mild",
                "pulmonary_edema": "No acute infiltrate or pulmonary edema",
                "widened_mediastinum": "Normal mediastinal contour, no evidence of dissection"
            }
        },
        physical_exam={
            "General": "Diaphoretic, anxious male in moderate-to-severe distress, clutching center of chest (Levine sign).",
            "Cardiovascular": "Tachycardic, regular rhythm, S1 and S2 present. No S3/S4 or murmurs. Peripheral pulses 2+ symmetric.",
            "Pulmonary": "Lungs clear to auscultation bilaterally, no crackles or wheezes.",
            "Abdomen": "Soft, nontender, nondistended, normoactive bowel sounds.",
            "Extremities": "No lower extremity cyanosis or peripheral edema."
        }
    ),
    # Level 2: Diabetic Ketoacidosis (DKA)
    PatientGroundTruth(
        id="CASE-102",
        name="Elena Rostova",
        age=24,
        sex="Female",
        triage_acuity=TriageAcuity.EMERGENT,
        chief_complaint="Severe nausea, diffuse abdominal pain, and rapid deep breathing for 24 hours",
        history_of_present_illness="24-year-old female with known Type 1 Diabetes presents with persistent vomiting, diffuse abdominal cramps, and profound fatigue. Ran out of insulin 3 days ago. Family noted fruity odor on breath and deep, rapid breathing.",
        past_medical_history=["Type 1 Diabetes Mellitus since age 11", "Hypothyroidism"],
        medications=["Insulin Glargine 22u qHS (missed x3)", "Insulin Aspart with meals (missed x3)", "Levothyroxine 75mcg daily"],
        allergies=["Sulfa drugs"],
        baseline_vitals=VitalSigns(
            heart_rate=122,
            systolic_bp=96,
            diastolic_bp=58,
            respiratory_rate=30,
            temperature_c=37.2,
            spo2_percent=98.0,
            pain_score=6
        ),
        true_diagnosis="Diabetic Ketoacidosis (DKA), Severe with High Anion Gap Metabolic Acidosis",
        icd10_code="E10.10",
        differential_candidates=[
            "Diabetic Ketoacidosis (DKA)",
            "Hyperosmolar Hyperglycemic State (HHS)",
            "Acute Appendicitis / Acute Abdomen",
            "Sepsis / Septic Shock",
            "Lactic Acidosis"
        ],
        recommended_labs=[
            LabTestType.BMP,
            LabTestType.ABG,
            LabTestType.CBC,
            LabTestType.URINALYSIS,
            LabTestType.LACTATE
        ],
        contraindicated_treatments=["Insulin bolus if potassium < 3.3 mEq/L", "Bicarbonate unless pH < 6.9"],
        optimal_treatment=[
            "Aggressive IV isotonic crystalloid resuscitation (1-1.5 L NS in first hour)",
            "Check serum potassium prior to insulin; replete K+ to 4.0-5.0 mEq/L",
            "Continuous IV regular insulin infusion (0.1 units/kg/hr)",
            "Frequent point-of-care glucose and electrolyte monitoring q1-2h",
            "Transition to D5W once serum glucose < 200 mg/dL while continuing insulin drip until anion gap closes"
        ],
        simulated_labs={
            LabTestType.BMP.value: {
                "Sodium": "131 mEq/L (corrected: 139 mEq/L)",
                "Potassium": "5.4 mEq/L",
                "Chloride": "94 mEq/L",
                "Bicarbonate": "8 mEq/L",
                "Anion_Gap": "29 mEq/L (Normal 8-12)",
                "BUN": "32 mg/dL",
                "Creatinine": "1.5 mg/dL",
                "Glucose": "488 mg/dL",
                "interpretation": "Severe high anion gap metabolic acidosis with profound hyperglycemia and prerenal azotemia"
            },
            LabTestType.ABG.value: {
                "pH": "7.14",
                "pCO2": "22 mmHg (respiratory compensation)",
                "pO2": "96 mmHg",
                "HCO3": "7.5 mEq/L",
                "interpretation": "Severe metabolic acidosis with compensatory Kussmaul respiratory alkalosis"
            },
            LabTestType.URINALYSIS.value: {
                "Ketones": "Large (++++ )",
                "Glucose": "> 1000 mg/dL",
                "Nitrites": "Negative",
                "Leukocyte_Esterase": "Negative",
                "interpretation": "Heavy ketonuria and glycosuria pathognomonic for ketoacidosis"
            },
            LabTestType.CBC.value: {
                "WBC": "14.8 x10^3/uL (stress demargination)",
                "Hemoglobin": "16.1 g/dL (hemoconcentration)",
                "Hematocrit": "48.2%",
                "Platelets": "290 x10^3/uL"
            }
        },
        physical_exam={
            "General": "Lethargic young female, dry mucous membranes, sunken orbits, sweet/fruity breath odor.",
            "Respiratory": "Marked Kussmaul breathing (deep, rapid respirations at 30/min). Lungs clear bilaterally.",
            "Cardiovascular": "Sinus tachycardia, weak peripheral pulses, delayed capillary refill (3.5s).",
            "Abdomen": "Diffuse tenderness to palpation without peritoneal signs or localized guarding.",
            "Neurological": "Oriented to person and place, mildly confused about date."
        }
    ),
    # Level 3: Acute Kidney Injury (KDIGO Stage 3) / Prerenal Azotemia
    PatientGroundTruth(
        id="CASE-103",
        name="Arthur Pendelton",
        age=68,
        sex="Male",
        triage_acuity=TriageAcuity.URGENT,
        chief_complaint="Severe weakness, marked oliguria (<200 mL/day), and lightheadedness for 3 days",
        history_of_present_illness="68-year-old male with hypertension presents with profound lethargy, dry mucous membranes, and near-anuria for 48 hours following severe gastrointestinal fluid loss during a heat wave. Continued taking home lisinopril and over-the-counter ibuprofen for back pain.",
        past_medical_history=["Hypertension", "Osteoarthritis", "Chronic Kidney Disease Stage 2 (baseline Cr 1.1)"],
        medications=["Lisinopril 20mg daily", "Ibuprofen 400mg TID PRN", "Amlodipine 5mg daily"],
        allergies=["No Known Drug Allergies (NKDA)"],
        baseline_vitals=VitalSigns(
            heart_rate=98,
            systolic_bp=92,
            diastolic_bp=56,
            respiratory_rate=18,
            temperature_c=37.1,
            spo2_percent=97.0,
            pain_score=3
        ),
        true_diagnosis="Acute Kidney Injury (KDIGO Stage 3) secondary to Prerenal Azotemia and Dehydration",
        icd10_code="N17.9",
        differential_candidates=[
            "Prerenal Azotemia / Volume Depletion",
            "Acute Tubular Necrosis (ATN)",
            "Acute Interstitial Nephritis (AIN)",
            "Post-Renal Obstructive Uropathy",
            "Glomerulonephritis"
        ],
        recommended_labs=[
            LabTestType.BMP,
            LabTestType.CBC,
            LabTestType.URINALYSIS,
            LabTestType.ECG_12_LEAD
        ],
        contraindicated_treatments=[
            "Continue Lisinopril / ACE inhibitor",
            "Continue NSAIDs / Ibuprofen",
            "Loop diuretic challenge while volume depleted"
        ],
        optimal_treatment=[
            "Immediately hold Lisinopril, Amlodipine, and NSAIDs",
            "Aggressive volume expansion with 0.9% Normal Saline 1000 mL IV challenge",
            "Foley catheter placement to accurately quantify hourly urine output",
            "Serial BMP every 12 hours to verify BUN/Cr recovery and prevent hyperkalemia",
            "Renal bladder ultrasound to definitively exclude bilateral hydronephrosis"
        ],
        simulated_labs={
            LabTestType.BMP.value: {
                "Sodium": "136 mEq/L",
                "Potassium": "5.2 mEq/L",
                "BUN": "68 mg/dL",
                "Creatinine": "3.8 mg/dL (baseline 1.1)",
                "BUN_Cr_Ratio": "17.9 (Prerenal > 20:1 trend)",
                "Glucose": "118 mg/dL",
                "eGFR": "16 mL/min/1.73m2",
                "interpretation": "Severe KDIGO Stage 3 AKI with prerenal azotemia exacerbated by concurrent ACE-I and NSAID triple whammy"
            },
            LabTestType.URINALYSIS.value: {
                "Specific_Gravity": "1.028 (concentrated urine)",
                "Urine_Sodium": "< 20 mEq/L",
                "FENa": "0.6% (< 1% indicative of prerenal etiology)",
                "Protein": "Trace",
                "Casts": "Hyaline casts only, no muddy brown casts"
            },
            LabTestType.CBC.value: {
                "WBC": "8.2 x10^3/uL",
                "Hemoglobin": "15.8 g/dL (hemoconcentration)",
                "Hematocrit": "47.5%",
                "Platelets": "240 x10^3/uL"
            }
        },
        physical_exam={
            "General": "Fatigued, dry oral mucosa, furrowed tongue, flat neck veins while supine.",
            "Cardiovascular": "Orthostatic tachycardia (HR 98 sitting -> 118 standing), soft S1/S2.",
            "Abdomen": "Benign, no costovertebral angle tenderness, no palpable bladder distension.",
            "Extremities": "Poor skin turgor with tenting, no peripheral edema, cool extremities."
        }
    ),
    # Level 4: Acute Pulmonary Embolism (Submassive PE)
    PatientGroundTruth(
        id="CASE-104",
        name="Clara Vance",
        age=52,
        sex="Female",
        triage_acuity=TriageAcuity.EMERGENT,
        chief_complaint="Sudden onset sharp right-sided pleuritic chest pain and breathlessness after a 12-hour flight",
        history_of_present_illness="52-year-old female presents with acute dyspnea and sharp 7/10 right anterior chest pain worse with inspiration. Returned 24 hours ago from an international 12-hour flight. Mild right calf tenderness noted over past 2 days.",
        past_medical_history=["Oral Contraceptive Use (Estrogen/Progestin)", "Mild Asthma"],
        medications=["Combined Oral Contraceptive pill", "Albuterol inhaler PRN"],
        allergies=["Codeine (nausea)"],
        baseline_vitals=VitalSigns(
            heart_rate=114,
            systolic_bp=108,
            diastolic_bp=72,
            respiratory_rate=26,
            temperature_c=37.4,
            spo2_percent=91.0,
            pain_score=7
        ),
        true_diagnosis="Acute Pulmonary Embolism (Submassive PE) with Right Ventricular Strain",
        icd10_code="I26.92",
        differential_candidates=[
            "Acute Pulmonary Embolism",
            "Pneumothorax",
            "Aortic Dissection",
            "Acute Coronary Syndrome",
            "Pneumonia / Pleuritis"
        ],
        recommended_labs=[
            LabTestType.D_DIMER,
            LabTestType.TROPONIN_I,
            LabTestType.BNP,
            LabTestType.CT_CHEST,
            LabTestType.ECG_12_LEAD
        ],
        contraindicated_treatments=[
            "Discharge on oral analgesics alone",
            "Aspirin monotherapy without therapeutic anticoagulation",
            "Routine systemic thrombolysis without hemodynamic collapse"
        ],
        optimal_treatment=[
            "Initiate immediate therapeutic anticoagulation (Enoxaparin 1 mg/kg SC q12h or IV Heparin)",
            "Supplemental oxygen via nasal cannula targeting SpO2 >= 94%",
            "Urgent CT Pulmonary Angiogram to confirm clot burden",
            "Bedside Transthoracic Echocardiogram to evaluate RV strain and McConnell sign",
            "Admit to monitored telemetry bed; hold estrogen-containing oral contraceptives"
        ],
        simulated_labs={
            LabTestType.D_DIMER.value: {
                "D_Dimer": "3420 ng/mL FEU (Normal < 500 ng/mL)",
                "interpretation": "Markedly elevated D-Dimer indicating high probability of active venous thromboembolism"
            },
            LabTestType.TROPONIN_I.value: {
                "Troponin_I": "0.18 ng/mL (Normal < 0.04)",
                "interpretation": "Mild troponin leak consistent with right ventricular strain/micro-infarction"
            },
            LabTestType.BNP.value: {
                "BNP": "385 pg/mL (Normal < 100)",
                "interpretation": "Elevated BNP reflecting acute right ventricular stretch"
            },
            LabTestType.CT_CHEST.value: {
                "findings": "Bilateral filling defects in main right pulmonary artery extending into lower lobe segmental branches. RV/LV ratio 1.2 indicating RV enlargement.",
                "interpretation": "Acute bilateral submassive pulmonary embolism"
            }
        },
        physical_exam={
            "General": "Tachypneic female in moderate distress, splinting with deep inspiration.",
            "Cardiovascular": "Tachycardia, accentuated P2 heart sound, mild jugular venous distention at 30 degrees.",
            "Pulmonary": "Decreased breath sounds at right base with pleural friction rub.",
            "Extremities": "Right calf 2.5 cm larger in circumference than left, tender along deep posterior calf."
        }
    )
]


def get_benchmark_case(case_id: str = "CASE-101") -> PatientGroundTruth:
    # 1. Check database for manually admitted patient
    try:
        from ..database.repository import db_repo
        import json
        p = db_repo.get_patient(case_id)
        if p:
            raw = p.get("raw_json", {})
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = {}

            v_dict = raw.get("baseline_vitals", {})
            vitals = VitalSigns(
                heart_rate=v_dict.get("heart_rate", 80),
                systolic_bp=v_dict.get("systolic_bp", 120),
                diastolic_bp=v_dict.get("diastolic_bp", 80),
                respiratory_rate=v_dict.get("respiratory_rate", 16),
                temperature_c=v_dict.get("temperature_c", 37.0),
                spo2_percent=v_dict.get("spo2_percent", 98.0),
                pain_score=v_dict.get("pain_score", 0),
            )

            acuity_str = str(p.get("triage_acuity", "URGENT"))
            acuity_enum = TriageAcuity.URGENT
            if "RESUSCITATION" in acuity_str:
                acuity_enum = TriageAcuity.RESUSCITATION
            elif "EMERGENT" in acuity_str:
                acuity_enum = TriageAcuity.EMERGENT
            elif "LESS_URGENT" in acuity_str:
                acuity_enum = TriageAcuity.LESS_URGENT
            elif "NON_URGENT" in acuity_str:
                acuity_enum = TriageAcuity.NON_URGENT

            pmh = raw.get("past_medical_history", [])
            if isinstance(pmh, str):
                pmh = [s.strip() for s in pmh.split(",") if s.strip()]
            meds = raw.get("medications", [])
            if isinstance(meds, str):
                meds = [s.strip() for s in meds.split(",") if s.strip()]
            allergies = raw.get("allergies", [])
            if isinstance(allergies, str):
                allergies = [s.strip() for s in allergies.split(",") if s.strip()]

            complaint = p.get("chief_complaint", "")
            hpi = raw.get("history_of_present_illness") or raw.get("hpi") or complaint

            return PatientGroundTruth(
                id=p["id"],
                name=p["name"],
                age=p["age"],
                sex=p["sex"],
                triage_acuity=acuity_enum,
                chief_complaint=complaint,
                history_of_present_illness=hpi,
                past_medical_history=pmh,
                medications=meds,
                allergies=allergies,
                baseline_vitals=vitals,
                true_diagnosis=raw.get("true_diagnosis") or "Clinical Evaluation in Progress",
                icd10_code="R69",
                differential_candidates=[],
                recommended_labs=[LabTestType.CBC, LabTestType.BMP],
                contraindicated_treatments=[],
                optimal_treatment=["Clinical workup and specialist consultation"],
                simulated_labs={},
                physical_exam={"General": f"Patient presenting with {complaint}. Responsive and oriented."},
            )
    except Exception:
        pass

    for c in BENCHMARK_CASES:
        if c.id == case_id:
            return c
    return BENCHMARK_CASES[0] if BENCHMARK_CASES else None

