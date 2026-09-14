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
    )
]


def get_benchmark_case(case_id: str = "CASE-101") -> PatientGroundTruth:
    for c in BENCHMARK_CASES:
        if c.id == case_id:
            return c
    return BENCHMARK_CASES[0]
