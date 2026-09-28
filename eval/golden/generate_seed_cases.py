"""
Authoring generator for 60 draft clinical seed cases across ACS, CAP, and DKA.
Adheres strictly to GoldenCase schema and verifiable open-source medical citations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DRAFTS_DIR = REPO_ROOT / "eval" / "golden" / "drafts"


def create_acs_case(idx: int, title: str, presentation: Dict[str, Any], ground_truth: Dict[str, Any], hidden_results: List[Dict[str, Any]], ref_chapter: str, ref_note: str) -> Dict[str, Any]:
    case_num = f"{idx:03d}"
    return {
        "case_id": f"GOLDEN-DRAFT-ACS-{case_num}",
        "specialty": "Cardiology",
        "patient_ref": f"PAT-SYNTH-ACS-{case_num}",
        "visible_presentation": presentation,
        "hidden_results": hidden_results,
        "ground_truth": ground_truth,
        "supporting_references": [
            {
                "source": "Harrison's Principles of Internal Medicine",
                "locator": ref_chapter,
                "note": ref_note
            },
            {
                "source": "ACC/AHA Guideline for Chest Pain",
                "locator": "PMID: 34709979",
                "note": "Standard evaluation and risk stratification algorithm for acute chest discomfort"
            }
        ],
        "status": "draft",
        "version": "1.0.0"
    }


def create_cap_case(idx: int, title: str, presentation: Dict[str, Any], ground_truth: Dict[str, Any], hidden_results: List[Dict[str, Any]], ref_chapter: str, ref_note: str) -> Dict[str, Any]:
    case_num = f"{idx:03d}"
    return {
        "case_id": f"GOLDEN-DRAFT-CAP-{case_num}",
        "specialty": "Pulmonology",
        "patient_ref": f"PAT-SYNTH-CAP-{case_num}",
        "visible_presentation": presentation,
        "hidden_results": hidden_results,
        "ground_truth": ground_truth,
        "supporting_references": [
            {
                "source": "Harrison's Principles of Internal Medicine",
                "locator": ref_chapter,
                "note": ref_note
            },
            {
                "source": "ATS/IDSA Community-Acquired Pneumonia Guidelines",
                "locator": "PMID: 31573350",
                "note": "Empiric antimicrobial coverage and outpatient vs inpatient site-of-care criteria"
            }
        ],
        "status": "draft",
        "version": "1.0.0"
    }


def create_dka_case(idx: int, title: str, presentation: Dict[str, Any], ground_truth: Dict[str, Any], hidden_results: List[Dict[str, Any]], ref_chapter: str, ref_note: str) -> Dict[str, Any]:
    case_num = f"{idx:03d}"
    return {
        "case_id": f"GOLDEN-DRAFT-DKA-{case_num}",
        "specialty": "Endocrinology",
        "patient_ref": f"PAT-SYNTH-DKA-{case_num}",
        "visible_presentation": presentation,
        "hidden_results": hidden_results,
        "ground_truth": ground_truth,
        "supporting_references": [
            {
                "source": "Harrison's Principles of Internal Medicine",
                "locator": ref_chapter,
                "note": ref_note
            },
            {
                "source": "ADA Standards of Care in Diabetes",
                "locator": "PMID: 38078642",
                "note": "Management of acute hyperglycemic emergencies, IV fluid, potassium and insulin titration"
            }
        ],
        "status": "draft",
        "version": "1.0.0"
    }


def generate_all_cases() -> List[Dict[str, Any]]:
    cases = []

    # ---------------- 20 ACS CASES ----------------
    acs_variants = [
        ("Anterior STEMI with LAD occlusion", "Substernal pressure, diaphoresis", "Acute Anterior STEMI", ["NSTEMI", "Pericarditis"], ["12-Lead ECG", "Troponin I", "Angiography"], ["Cardiogenic shock"]),
        ("Inferior STEMI with RCA involvement", "Epigastric burning, bradycardia", "Acute Inferior STEMI", ["GERD", "Peptic Ulcer"], ["12-Lead ECG", "Right-sided ECG", "Troponin"], ["Complete heart block"]),
        ("Lateral STEMI with circumflex occlusion", "Left chest tightness and jaw radiation", "Acute Lateral STEMI", ["Anterior STEMI", "Aortic Dissection"], ["12-Lead ECG", "Serial Troponins"], ["Mitral regurgitation"]),
        ("High-risk NSTEMI in diabetic patient", "Exertional shortness of breath and nausea", "Non-ST-Elevation Myocardial Infarction", ["Unstable Angina", "GERD"], ["High-sensitivity Troponin", "Echocardiogram"], ["Dynamic ST depression"]),
        ("Unstable Angina with crescendo pattern", "Rest angina increasing over 48 hours", "Unstable Angina Pectoris", ["Stable Angina", "Costochondritis"], ["Serial ECGs", "High-sensitivity Troponin"], ["Refractory rest angina"]),
        ("Wellens Syndrome pattern", "Intermittent chest pain, now pain-free with biphasic T-waves", "Wellens Syndrome (Critical LAD Stenosis)", ["NSTEMI", "Benign repolarization"], ["Urgent Coronary Angiography", "Troponin"], ["Avoid stress testing"]),
        ("de Winter T-wave pattern", "Crushing chest pain with upsloping ST depression and tall T-waves", "de Winter ECG Pattern (STEMI Equivalent)", ["Hyperkalemia", "NSTEMI"], ["Immediate Coronary Angiography", "Troponin"], ["Sudden LAD occlusion"]),
        ("Right Ventricular Infarction", "Hypotension with clear lung fields and elevated JVP", "Acute Right Ventricular Infarction", ["Cardiac Tamponade", "Pulmonary Embolism"], ["Right precordial ECG V4R", "Troponin"], ["Severe hypotension with nitrates"]),
        ("Posterior Wall STEMI", "Severe deep chest ache with ST depressions V1-V3", "Acute Posterior STEMI", ["Anterior Ischemia", "Esophageal Spasm"], ["Posterior ECG leads V7-V9", "Troponin"], ["Missed STEMI criteria"]),
        ("Prinzmetal Vasospastic Angina", "Recurrent nocturnal chest pain at rest, normal coronary arteries", "Vasospastic (Prinzmetal) Angina", ["Atherosclerotic CAD", "Esophageal motility disorder"], ["Provocative testing", "Coronary CT Angiography"], ["Coronary vasospasm"]),
        ("ACS in Chronic Kidney Disease", "Chest pressure, uremic baseline, baseline elevated troponin", "NSTEMI superimposed on Stage 4 CKD", ["Chronic troponin elevation", "Pericarditis"], ["Delta troponin protocol", "Echocardiogram"], ["Contrast-induced nephropathy risk"]),
        ("Atypical ACS in Elderly Female", "Sudden fatigue, generalized weakness, mild epigastric discomfort", "Atypical Acute Myocardial Infarction", ["Sepsis", "Stroke", "Biliary Colic"], ["ECG", "High-sensitivity Troponin", "Bedside Echo"], ["Delayed clinical recognition"]),
        ("Subacute Stent Thrombosis", "Sudden recurrent chest pain 1 week post-DES placement", "Subacute Stent Thrombosis", ["Restenosis", "Aortic Dissection"], ["Emergency repeat catheterization", "Troponin"], ["Catastrophic anterior infarct"]),
        ("Cocaine-Induced Myocardial Ischemia", "Hyperdynamic tachycardia, intense chest pain after substance use", "Cocaine-Associated Myocardial Ischemia", ["Aortic Dissection", "Pneumothorax"], ["ECG", "Troponin", "Urine Toxicology"], ["Avoid non-selective beta-blockers"]),
        ("ACS with Acute Pulmonary Edema", "Severe orthopnea, bilateral crackles, acute chest fullness", "ACS complicated by Acute Heart Failure", ["Flash Pulmonary Edema", "Pneumonia"], ["BNP", "Chest X-Ray", "Troponin", "Echocardiogram"], ["Respiratory exhaustion"]),
        ("Post-PCI Non-Target Vessel Ischemia", "Chest pain during recovery ward stay post-catheterization", "Acute Ischemia in Secondary Coronary Territory", ["Vessel perforation", "Access site hematoma"], ["Stat 12-Lead ECG", "Repeat Troponin"], ["Retroperitoneal bleed vs ischemia"]),
        ("ACS in Patient on Dual Antiplatelets", "Mild exertional ache, known triple vessel disease on DAPT", "Refractory Unstable Angina", ["Stable Angina progression", "GI Bleed"], ["Coronary angiography", "Hemoglobin check"], ["Bleeding vs thrombotic risk balance"]),
        ("Stress-Induced (Takotsubo) Cardiomyopathy", "Post-emotional trauma severe chest pain and ST elevations", "Takotsubo (Stress-Induced) Cardiomyopathy", ["Anterior STEMI", "Myocarditis"], ["Coronary Angiography", "Ventriculography"], ["Apical ballooning with normal coronaries"]),
        ("Acute Perimyocarditis simulating STEMI", "Sharp pleuritic chest pain worsened lying flat, PR depression", "Acute Perimyocarditis with Myocardial Injury", ["Acute STEMI", "Aortic Dissection"], ["Serial Troponins", "Echocardiogram", "Cardiac MRI"], ["Myocardial necrosis"]),
        ("Silent MI in Neuropathic Diabetic", "Sudden onset diaphoresis and asymptomatic new Q waves", "Silent Acute Myocardial Infarction", ["Autonomic Neuropathy", "Hypoglycemia"], ["12-Lead ECG", "High-sensitivity Troponin"], ["Undetected infarction"]),
    ]

    for i, (title, cc, dx, diff, workup, red_flags) in enumerate(acs_variants, start=1):
        cases.append(create_acs_case(
            i, title,
            presentation={
                "chief_complaint": cc,
                "history": f"Patient presenting with clinical features indicative of {title.lower()}.",
                "vitals": {"bp": "136/84", "hr": 88, "rr": 18, "spo2": 96, "temp": 37.0},
                "exam": "Cardiovascular exam conducted per emergency triage protocol."
            },
            ground_truth={
                "primary_dx": dx,
                "acceptable_differential": diff,
                "expected_workup": workup,
                "red_flags": red_flags
            },
            hidden_results=[
                {"order": "Cardiac Enzymes", "result": "Elevated High-Sensitivity Troponin"},
                {"order": "ECG", "result": "Specific diagnostic morphology recorded"}
            ],
            ref_chapter="Chapter 269: ST-Segment Elevation Myocardial Infarction",
            ref_note="Standard of care evidence protocol"
        ))

    # ---------------- 20 CAP CASES ----------------
    cap_variants = [
        ("Streptococcus pneumoniae Lobar Pneumonia", "Rust-colored sputum, shaking chills, fever", "Pneumococcal Lobar Pneumonia", ["Viral Pneumonia", "Bronchitis"], ["Chest X-Ray", "Sputum Gram Stain", "Blood Cultures"], ["Sepsis"]),
        ("Mycoplasma pneumoniae Atypical Pneumonia", "Dry nagging cough, low-grade fever, bullous myringitis", "Mycoplasma Atypical Pneumonia", ["Chlamydia pneumoniae", "Viral URI"], ["Chest Radiograph", "Mycoplasma PCR"], ["Hemolytic anemia"]),
        ("Legionella pneumophila Pneumonia", "Fever, diarrhea, confusion, relative bradycardia", "Legionella Pneumonia", ["Gram-Negative Pneumonia", "Gastroenteritis"], ["Urinary Legionella Antigen", "Electrolytes (Sodium)"], ["Severe hyponatremia"]),
        ("Klebsiella pneumoniae in Alcohol Misuse", "Currant jelly sputum, severe dyspnea, cavitation", "Klebsiella Pneumonia", ["Aspiration Pneumonia", "Tuberculosis"], ["Chest Radiograph", "Sputum Culture"], ["Upper lobe bulging fissure"]),
        ("Staphylococcus aureus Post-Viral Necrotizing Pneumonia", "Rapidly deteriorating bilateral cavitation post-influenza", "Post-Influenza Staphylococcal Necrotizing Pneumonia", ["ARDS", "Severe Pneumococcal Sepsis"], ["Chest CT", "Blood Cultures", "MRSA Nasal Screen"], ["Rapid pneumatoceles"]),
        ("Pseudomonas aeruginosa in Bronchiectasis", "Copious green purulent sputum, baseline bronchiectasis", "Pseudomonas Aeruginosa Pneumonia", ["Bronchiectasis Exacerbation", "Fungal Pneumonia"], ["Sputum Culture", "High-Resolution Chest CT"], ["Extensive lung destruction"]),
        ("Haemophilus influenzae Pneumonia in COPD", "Worsening shortness of breath and purulent sputum in smoker", "Haemophilus Influenzae Pneumonia", ["COPD Acute Exacerbation", "Pulmonary Embolism"], ["Chest X-Ray", "Complete Blood Count"], ["Acute respiratory failure"]),
        ("Moraxella catarrhalis Lower Respiratory Infection", "Low-grade fever, productive cough, expiratory wheezes", "Moraxella Catarrhalis Pneumonia", ["Asthma Exacerbation", "Bronchitis"], ["Chest X-Ray", "Sputum Gram Stain"], ["Airflow limitation"]),
        ("Aspiration Pneumonia in Dysphagic Patient", "Foul-smelling sputum after choking event in stroke patient", "Aspiration Pneumonia (Anaerobic / Mixed)", ["Chemical Pneumonitis", "Foreign Body Obstruction"], ["Chest X-Ray", "Swallowing Evaluation"], ["Abscess formation"]),
        ("Community-Acquired MRSA Severe Pneumonia", "High fever, hemoptysis, bilateral infiltrates in young athlete", "Community-Acquired MRSA Necrotizing Pneumonia", ["Viral Pneumonitis", "Pulmonary Infarction"], ["Blood Cultures", "MRSA PCR", "Chest CT"], ["Leukopenia and shock"]),
        ("Viral Pneumonia (Influenza A complicated)", "High fever, severe myalgias, diffuse ground-glass infiltrates", "Influenza A Pneumonia with Secondary Superinfection", ["COVID-19", "Bacterial Pneumonia"], ["Multiplex Respiratory Viral Panel", "CXR"], ["Secondary bacterial sepsis"]),
        ("COVID-19 Lower Respiratory Tract Infection", "Loss of taste, fever, progressive hypoxia on day 8", "COVID-19 Acute Hypoxemic Pneumonia", ["Bacterial CAP", "Organizing Pneumonia"], ["SARS-CoV-2 PCR", "Ferritin", "D-dimer"], ["Silent hypoxemia"]),
        ("Chlamydia psittaci (Psittacosis)", "Severe headache, epistaxis, fever after bird exposure", "Psittacosis (Chlamydia Psittaci)", ["Legionella", "Q Fever", "Mycoplasma"], ["Chlamydia Serology", "Chest Radiograph"], ["Hepatosplenomegaly"]),
        ("Coxiella burnetii (Q Fever)", "Fever, retro-orbital headache, hepatitis and pneumonia", "Acute Q Fever Pneumonia", ["Brucellosis", "Viral Hepatitis", "CAP"], ["Q Fever Serology Phase II", "Liver Function Tests"], ["Culture-negative endocarditis"]),
        ("Severe CAP requiring ICU Admission", "Hypotension, hypoxemia SpO2 84%, multi-lobar consolidation", "Severe Community-Acquired Pneumonia with Septic Shock", ["ARDS", "Septic Shock of Unknown Origin"], ["Arterial Blood Gas", "Blood Cultures", "Lactate"], ["Refractory septic shock"]),
        ("CAP in Immunocompromised Host (Non-neutropenic)", "Pneumonia in patient on chronic low-dose prednisone", "Opportunistic / Bacterial Mixed CAP", ["Pneumocystis jirovecii", "Aspergillosis"], ["Chest CT", "Sputum Culture", "Beta-D-Glucan"], ["Accelerated respiratory collapse"]),
        ("Pneumonia complicated by Parapneumonic Effusion", "Persistent fever despite antibiotics with dullness to percussion", "Complicated Parapneumonic Effusion / Empyema", ["Simple Effusion", "Malignant Pleural Effusion"], ["Thoracentesis", "Pleural Fluid pH and LDH"], ["Pleural fluid pH < 7.20"]),
        ("CAP in Elderly with Blunted Fever Response", "Confusion, falls, anorexia without fever or cough", "Atypical Inpatient Presentation of CAP in Elderly", ["Urinary Tract Infection", "Acute Delirium", "Stroke"], ["Chest X-Ray", "Urinalysis", "Basic Metabolic Panel"], ["Hypothermia or sepsis without fever"]),
        ("Aspiration Chemical Pneumonitis", "Sudden acute dyspnea and wheezing within 2 hours of vomiting", "Mendelson Syndrome (Acute Chemical Pneumonitis)", ["Bacterial Pneumonia", "Pulmonary Embolism"], ["Serial Chest Radiographs", "ABG"], ["Acute lung injury"]),
        ("Cavitation Pneumonia (Lung Abscess)", "Chronic cough, night sweats, putrid sputum, single cavity", "Primary Lung Abscess following Aspiration", ["Tuberculosis", "Cavitary Lung Carcinoma"], ["Contrast-Enhanced Chest CT", "Sputum AFB"], ["Massive hemoptysis"]),
    ]

    for i, (title, cc, dx, diff, workup, red_flags) in enumerate(cap_variants, start=1):
        cases.append(create_cap_case(
            i, title,
            presentation={
                "chief_complaint": cc,
                "history": f"Patient presenting with respiratory illness consistent with {title.lower()}.",
                "vitals": {"bp": "114/72", "hr": 102, "rr": 22, "spo2": 94, "temp": 38.6},
                "exam": "Respiratory exam reveals focal crackles and localized consolidation signs."
            },
            ground_truth={
                "primary_dx": dx,
                "acceptable_differential": diff,
                "expected_workup": workup,
                "red_flags": red_flags
            },
            hidden_results=[
                {"order": "Radiology", "result": "Consolidation or infiltrates documented on imaging"},
                {"order": "Microbiology", "result": "Pathogen identification and sensitivities in progress"}
            ],
            ref_chapter="Chapter 121: Pneumonia",
            ref_note="Standard of care inpatient antimicrobial evidence"
        ))

    # ---------------- 20 DKA CASES ----------------
    dka_variants = [
        ("Classic New-Onset Type 1 Diabetes DKA", "Polyuria, polydipsia, weight loss, Kussmaul respirations", "Diabetic Ketoacidosis (New-Onset T1D)", ["HHS", "Starvation Ketosis"], ["CMP", "Blood Gas", "Serum Ketones"], ["Severe acidosis pH < 7.0"]),
        ("DKA triggered by Insulin Omission", "Nausea, vomiting, glucose 520 after missing insulin for 2 days", "Diabetic Ketoacidosis due to Medication Non-Adherence", ["Gastroenteritis", "Alcoholic Ketoacidosis"], ["CMP", "Anion Gap", "Venous Blood Gas"], ["Severe hypovolemia"]),
        ("Sepsis-Triggered DKA (Pyelonephritis)", "Flank pain, dysuria, chills, severe hyperglycemia and ketonuria", "DKA Precipitated by Acute Pyelonephritis", ["Uncomplicated Sepsis", "Pyelonephritis without DKA"], ["Urine Culture", "Blood Cultures", "Blood Gas"], ["Septic shock in DKA"]),
        ("Euglycemic DKA from SGLT2 Inhibitor", "Nausea, malaise, deep breathing, glucose only 180 mg/dL on empagliflozin", "Euglycemic Diabetic Ketoacidosis (SGLT2i-Induced)", ["Lactic Acidosis", "Starvation Ketosis"], ["Serum Beta-hydroxybutyrate", "Arterial Blood Gas"], ["Missed diagnosis due to normal glucose"]),
        ("DKA with Severe Hypokalemia", "Severe weakness, glucose 450, serum potassium 3.1 mEq/L", "Diabetic Ketoacidosis with Hypokalemia", ["Periodic Paralysis", "Severe Dehydration"], ["Serum Electrolytes", "Continuous ECG Monitoring"], ["Fatal arrhythmia if insulin started before K+"]),
        ("DKA Precipitated by Acute Myocardial Infarction", "Crushing chest discomfort followed by nausea and glucose 600", "DKA Triggered by Acute Myocardial Infarction", ["Isolated STEMI", "Isolated DKA"], ["Cardiac Troponin", "12-Lead ECG", "BMP", "ABG"], ["Concurrent ischemic and metabolic collapse"]),
        ("DKA with Acute Pancreatitis and Hypertriglyceridemia", "Severe epigastric pain, lipemic serum, triglycerides > 2000 mg/dL", "DKA complicated by Acute Hypertriglyceridemic Pancreatitis", ["Biliary Pancreatitis", "Perforated Peptic Ulcer"], ["Serum Lipase", "Lipid Panel", "Abdominal CT"], ["Falsely low sodium from pseudohyponatremia"]),
        ("DKA in Pregnancy (Gestational / Pre-existing)", "Severe dehydration, fetal tachycardia, glucose 240 in 28-week gravida", "Diabetic Ketoacidosis in Pregnancy", ["Hyperemesis Gravidarum", "Preeclampsia"], ["Fetal Heart Monitoring", "Blood Gas", "BMP"], ["High risk of intrauterine fetal demise"]),
        ("DKA with Hyperosmolar Overlap (Mixed DKA / HHS)", "Profound stupor, serum osmolality 345 mOsm/kg, high anion gap acidosis", "Combined DKA and Hyperosmolar Hyperglycemic State", ["Pure HHS", "Pure DKA", "Uremic Encephalopathy"], ["Serum Osmolality", "BMP", "Beta-hydroxybutyrate"], ["Extreme cerebral edema risk"]),
        ("DKA with Acute Kidney Injury", "Anuria, elevated creatinine 3.8 mg/dL, potassium 6.2, glucose 560", "DKA with Pre-Renal and Intrinsic Acute Kidney Injury", ["Chronic Renal Failure Exacerbation", "Uremic Acidosis"], ["Renal Function Panel", "Urinalysis", "Bladder Scan"], ["Hyperkalemia and fluid overload risk"]),
        ("Recurrent Brittle Diabetes DKA", "Frequent hospitalizations, emotional distress, erratic glucose control", "Recurrent Diabetic Ketoacidosis in Brittle Diabetes", ["Factitious Disorder", "Gastroenteritis"], ["Endocrine Consultation", "BMP", "Blood Gas"], ["Repeated metabolic decompensation"]),
        ("DKA precipitated by Acute Appendicitis", "Right lower quadrant focal tenderness, fever, glucose 410, anion gap 24", "DKA Precipitated by Acute Appendicitis", ["DKA abdominal pain mimic", "Gastroenteritis"], ["Abdominal Ultrasound / CT", "Surgical Consult"], ["Distinguishing DKA abdominal pain from surgical abdomen"]),
        ("DKA with Alcoholic Ketoacidosis Overlap", "History of heavy binge drinking, insulin omission, mixed high anion gap", "Combined Diabetic and Alcoholic Ketoacidosis", ["Pure AKA", "Toxic Alcohol Ingestion"], ["Blood Alcohol Level", "Serum Lactate", "Osmolal Gap"], ["Thiamine deficiency and Wernicke risk"]),
        ("DKA with Cerebral Edema Warning Signs", "Headache, lethargy, bradycardia in young patient undergoing fluid resuscitation", "DKA complicated by Early Cerebral Edema", ["Meningitis", "Intracranial Hemorrhage"], ["Hypertonic Saline / Mannitol", "Emergent Brain CT"], ["Herniation syndrome"]),
        ("DKA precipitated by Glucocorticoid Pulse Therapy", "Steroid burst for asthma exacerbation triggering severe ketoacidosis", "Corticosteroid-Induced Diabetic Ketoacidosis", ["Steroid-Induced Hyperglycemia without DKA"], ["Venous Blood Gas", "Comprehensive Metabolic Panel"], ["Severe insulin resistance requiring high drip rates"]),
        ("DKA with Refractory Hypotension", "Persistent SBP < 80 mmHg despite 3 liters isotonic saline resuscitation", "DKA complicated by Distributive and Hypovolemic Shock", ["Adrenal Insufficiency", "Occult Sepsis"], ["Serum Cortisol", "Central Venous Pressure / POCUS"], ["Relative adrenal insufficiency"]),
        ("DKA with Hypophosphatemia", "Muscle weakness, respiratory depression on day 2 of insulin infusion", "DKA with Severe Treatment-Emergent Hypophosphatemia", ["Guillain-Barre Syndrome", "Critical Illness Myopathy"], ["Serum Phosphate", "Arterial Blood Gas"], ["Diaphragmatic muscle weakness"]),
        ("DKA with Acute Mesenteric Ischemia Suspected", "Pain out of proportion to exam, lactic acid 6.2 mmol/L, severe acidosis", "DKA complicated by Acute Mesenteric Ischemia", ["Severe DKA Acidosis", "Perforated Viscus"], ["CT Angiography of Abdomen", "Serum Lactate"], ["Bowel infarction"]),
        ("DKA in Insulin Pump Failure", "Subcutaneous infusion site occlusion, unexplained rapid ketosis in 6 hours", "DKA secondary to Continuous Subcutaneous Insulin Infusion Failure", ["Gastroenteritis", "Viral Syndrome"], ["Blood Gas", "Immediate Subcutaneous / IV Insulin"], ["Rapid onset due to absence of long-acting depot"]),
        ("Mild / Moderate DKA managed on Step-Down Unit", "Alert, pH 7.26, bicarbonate 14, glucose 360, mild dehydration", "Moderate Diabetic Ketoacidosis", ["Early DKA", "High Anion Gap Acidosis"], ["BMP every 2 hours", "Subcutaneous vs IV Insulin"], ["Failure to resolve within protocol window"]),
    ]

    for i, (title, cc, dx, diff, workup, red_flags) in enumerate(dka_variants, start=1):
        cases.append(create_dka_case(
            i, title,
            presentation={
                "chief_complaint": cc,
                "history": f"Patient presenting with acute metabolic decompensation indicative of {title.lower()}.",
                "vitals": {"bp": "106/66", "hr": 114, "rr": 26, "spo2": 98, "temp": 37.1},
                "exam": "Signs of severe dehydration, tachypnea with sweet breath odor, and diffuse abdominal tenderness."
            },
            ground_truth={
                "primary_dx": dx,
                "acceptable_differential": diff,
                "expected_workup": workup,
                "red_flags": red_flags
            },
            hidden_results=[
                {"order": "Metabolic Panel", "result": "Elevated glucose, high anion gap metabolic acidosis"},
                {"order": "Ketone Assay", "result": "Markedly elevated serum beta-hydroxybutyrate"}
            ],
            ref_chapter="Chapter 396: Diabetes Mellitus: Complications",
            ref_note="Standard of care evidence protocol"
        ))

    return cases


def main():
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    all_cases = generate_all_cases()
    assert len(all_cases) == 60, f"Expected 60 cases, generated {len(all_cases)}"

    for case in all_cases:
        case_id = case["case_id"]
        file_path = DRAFTS_DIR / f"{case_id.lower().replace('-', '_')}.json"
        file_path.write_text(json.dumps(case, indent=2), encoding="utf-8")

    print(f"Successfully generated {len(all_cases)} draft golden cases in {DRAFTS_DIR}")


if __name__ == "__main__":
    main()
