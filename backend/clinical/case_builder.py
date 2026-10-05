"""
Synthetic Clinical Case Builder.
Transforms raw Synthea FHIR profiles or clinical demographic records into
rich, fully-simulated PatientGroundTruth cases with realistic laboratory banks,
imaging studies, physical examination findings, and hidden ground-truth solutions.
"""

import logging
from typing import Dict, List, Any, Optional
from backend.clinical.models import VitalSigns, LabTestType, TriageAcuity
from backend.clinical.cases import PatientGroundTruth

logger = logging.getLogger("CaseBuilder")


class SyntheticClinicalCaseBuilder:
    """
    Constructs high-fidelity PatientGroundTruth instances from synthetic data.
    Ensures laboratory investigations, physical exams, and clinical differentials
    reflect pathophysiological realities without exposing ground-truth to the agent.
    """

    @staticmethod
    def build_from_profile(profile_dict: Dict[str, Any]) -> PatientGroundTruth:
        """Constructs a complete PatientGroundTruth case from a profile dictionary."""
        case_id = profile_dict.get("id") or f"CASE-{profile_dict.get('mrn', 'SYNTH')}"
        name = profile_dict.get("name", "Synthetic Patient")
        age = int(profile_dict.get("age", 58))
        sex = profile_dict.get("sex") or profile_dict.get("gender") or "Male"
        sex = sex.capitalize()

        # Extract conditions & complaints
        active_conditions = profile_dict.get("active_conditions", [])
        if isinstance(active_conditions, list) and active_conditions and isinstance(active_conditions[0], dict):
            cond_names = [c.get("name", "") for c in active_conditions if c.get("name")]
        elif isinstance(active_conditions, list):
            cond_names = [str(c) for c in active_conditions]
        else:
            cond_names = []

        complaint = profile_dict.get("chief_complaint")
        if not complaint and cond_names:
            complaint = cond_names[0]
        elif not complaint:
            complaint = "Acute worsening of generalized malaise and clinical symptoms"

        hpi = profile_dict.get("history_of_present_illness") or profile_dict.get("hpi")
        if not hpi:
            hpi = (
                f"{age}-year-old {sex.lower()} presents with acute onset of {complaint.lower()} "
                f"progressing over the last 48 hours. Accompanied by progressive fatigue and clinical deterioration."
            )

        pmh = profile_dict.get("past_medical_history", [])
        if isinstance(pmh, str):
            pmh = [s.strip() for s in pmh.split(",") if s.strip()]
        if not pmh and len(cond_names) > 1:
            pmh = cond_names[1:]

        meds = profile_dict.get("medications", [])
        if isinstance(meds, list) and meds and isinstance(meds[0], dict):
            meds = [m.get("name", "") for m in meds if m.get("name")]
        elif isinstance(meds, str):
            meds = [s.strip() for s in meds.split(",") if s.strip()]

        allergies = profile_dict.get("allergies", [])
        if isinstance(allergies, list) and allergies and isinstance(allergies[0], dict):
            allergies = [a.get("substance", "") for a in allergies if a.get("substance")]
        elif isinstance(allergies, str):
            allergies = [s.strip() for s in allergies.split(",") if s.strip()]

        # Vitals extraction
        v_dict = profile_dict.get("baseline_vitals") or profile_dict.get("latest_vitals") or {}
        vitals = VitalSigns(
            heart_rate=int(v_dict.get("heart_rate", 84)),
            systolic_bp=int(v_dict.get("systolic_bp", 128)),
            diastolic_bp=int(v_dict.get("diastolic_bp", 82)),
            respiratory_rate=int(v_dict.get("respiratory_rate", 18)),
            temperature_c=float(v_dict.get("temperature_c", 37.1)),
            spo2_percent=float(v_dict.get("spo2_percent", 97.0)),
            pain_score=int(v_dict.get("pain_score", 4)),
        )

        # Detect clinical pathology archetype
        complaint_lower = complaint.lower()
        hpi_lower = hpi.lower()
        full_text = f"{complaint_lower} {hpi_lower} {' '.join(cond_names).lower()}"

        if any(w in full_text for w in ["chest pain", "infarction", "angina", "stemi", "nstemi", "coronary", "substernal"]):
            archetype = "CARDIOLOGY_ACS"
        elif any(w in full_text for w in ["heart failure", "dyspnea", "orthopnea", "edema", "chf"]):
            archetype = "CARDIOLOGY_CHF"
        elif any(w in full_text for w in ["ketoacidosis", "dka", "glucose", "hyperglycemia", "diabetic"]):
            archetype = "ENDOCRINOLOGY_DKA"
        elif any(w in full_text for w in ["pneumonia", "cough", "sputum", "infiltrate", "fever"]):
            archetype = "PULMONOLOGY_CAP"
        elif any(w in full_text for w in ["kidney", "creatinine", "oliguria", "aki", "renal"]):
            archetype = "NEPHROLOGY_AKI"
        else:
            archetype = "INTERNAL_MEDICINE_GENERAL"

        return SyntheticClinicalCaseBuilder._generate_ground_truth(
            case_id=case_id,
            name=name,
            age=age,
            sex=sex,
            complaint=complaint,
            hpi=hpi,
            pmh=pmh,
            meds=meds,
            allergies=allergies,
            vitals=vitals,
            archetype=archetype,
        )

    @staticmethod
    def _generate_ground_truth(
        case_id: str,
        name: str,
        age: int,
        sex: str,
        complaint: str,
        hpi: str,
        pmh: List[str],
        meds: List[str],
        allergies: List[str],
        vitals: VitalSigns,
        archetype: str,
    ) -> PatientGroundTruth:
        """Populates pathophysiologically consistent ground truth and lab bank."""

        if archetype == "CARDIOLOGY_ACS":
            true_dx = "Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)"
            icd10 = "I21.4"
            acuity = TriageAcuity.EMERGENT
            differentials = ["Unstable Angina", "Acute Pericarditis", "Pulmonary Embolism", "Aortic Dissection", "Gastroesophageal Reflux"]
            recommended_labs = [
                LabTestType.CBC,
                LabTestType.BMP,
                LabTestType.TROPONIN_I,
                LabTestType.ECG_12_LEAD,
                LabTestType.CXR,
                LabTestType.CMP,
            ]
            contraindicated = ["NSAIDs (except Aspirin)", "Immediate discharge without telemetry", "Thrombolysis in NSTEMI"]
            optimal = [
                "Aspirin 325 mg oral chewable",
                "Ticagrelor 180 mg oral loading dose",
                "Unfractionated Heparin IV infusion (weight-adjusted)",
                "Sublingual Nitroglycerin 0.4 mg PRN for active chest pain",
                "High-intensity Atorvastatin 80 mg daily",
                "Admission to Cardiac Care Unit / Telemetry and urgent coronary angiography",
            ]
            physical_exam = {
                "General": "Diaphoretic, anxious male in moderate distress holding center of chest (Levine sign).",
                "Cardiovascular": "Tachycardic, regular rhythm. S4 gallop present at apex. No murmurs or friction rubs. JVP normal.",
                "Respiratory": "Bilateral vesicular breath sounds, mild bibasilar end-inspiratory crackles, no wheezes.",
                "Abdomen": "Soft, non-tender, non-distended, normal active bowel sounds.",
                "Neurological": "Alert and fully oriented x 4, no focal neurological deficits.",
            }
            simulated_labs = {
                "Troponin I / T": {
                    "Troponin_I": "1.84 ng/mL",
                    "Troponin_T": "0.62 ng/mL",
                    "reference": "< 0.04 ng/mL",
                    "flag": "CRITICAL_HIGH",
                    "interpretation": "Significantly elevated cardiac troponin indicating acute myocardial necrosis.",
                },
                "12-Lead ECG": {
                    "rhythm": "Sinus tachycardia at 102 bpm",
                    "st_segment": "2 mm ST depression in leads V4-V6, II, III, aVF; inverted T waves in V5-V6",
                    "q_waves": "No pathologic Q waves",
                    "flag": "ABNORMAL_ISCHEMIA",
                    "interpretation": "Acute subendocardial ischemia in anterolateral and inferior distributions without ST elevation.",
                },
                "Complete Blood Count (CBC)": {
                    "WBC": "10.4 x10^3/uL",
                    "Hemoglobin": "14.2 g/dL",
                    "Hematocrit": "42.5%",
                    "Platelets": "245 x10^3/uL",
                    "interpretation": "Normal CBC indices without evidence of acute occult bleeding or infection.",
                },
                "Basic Metabolic Panel (BMP)": {
                    "Sodium": "139 mEq/L",
                    "Potassium": "4.2 mEq/L",
                    "Chloride": "101 mEq/L",
                    "Bicarbonate": "24 mEq/L",
                    "BUN": "18 mg/dL",
                    "Creatinine": "1.0 mg/dL",
                    "Glucose": "142 mg/dL",
                    "interpretation": "Electrolytes and renal function within normal limits. Mild stress hyperglycemia.",
                },
                "Chest X-Ray (PA & Lateral)": {
                    "cardiac_silhouette": "Upper limit of normal cardiac silhouette",
                    "pulmonary_fields": "Mild pulmonary vascular congestion, no focal consolidations or pneumothorax",
                    "interpretation": "Mild early pulmonary venous congestion without florid alveolar edema.",
                },
                "Coagulation Panel": {
                    "PT": "11.8 sec",
                    "INR": "1.0",
                    "aPTT": "28.4 sec",
                    "interpretation": "Baseline coagulation profile within standard limits prior to anticoagulation.",
                },
            }

        elif archetype == "CARDIOLOGY_CHF":
            true_dx = "Acute Decompensated Heart Failure (ADHF)"
            icd10 = "I50.9"
            acuity = TriageAcuity.EMERGENT
            differentials = ["COPD Exacerbation", "Acute Pulmonary Embolism", "Community-Acquired Pneumonia", "Nephrotic Syndrome"]
            recommended_labs = [
                LabTestType.CBC,
                LabTestType.BMP,
                LabTestType.BNP,
                LabTestType.CXR,
                LabTestType.ECG_12_LEAD,
                LabTestType.CT_CHEST,
            ]
            contraindicated = ["Aggressive IV fluid boluses", "NSAIDs", "Calcium channel blockers with negative inotropy"]
            optimal = [
                "Furosemide 40-80 mg IV bolus",
                "Supplemental oxygen to maintain SpO2 >= 94%",
                "Upright positioning and strict fluid restriction (1.5 L/day)",
                "Daily weights and strict intake/output tracking",
                "Cardiology consultation for inpatient guideline-directed medical therapy titration",
            ]
            physical_exam = {
                "General": "Dyspneic at rest, sitting upright (orthopnea), using accessory respiratory muscles.",
                "Cardiovascular": "Jugular venous distension 8 cm above sternal angle. S3 gallop audible at apex. Lateral displacement of PMI.",
                "Respiratory": "Bilateral coarse crackles spanning lower halves of lung fields. Expiratory wheezing (cardiac asthma).",
                "Abdomen": "Mild hepatomegaly with positive hepatojugular reflux. No ascites.",
                "Extremities": "2+ bilateral pitting lower extremity edema extending to mid-shin.",
            }
            simulated_labs = {
                "B-Type Natriuretic Peptide (BNP)": {
                    "BNP": "1280 pg/mL",
                    "reference": "< 100 pg/mL",
                    "flag": "CRITICAL_HIGH",
                    "interpretation": "Markedly elevated BNP diagnostic of acute hemodynamic ventricular volume overload and heart failure.",
                },
                "Chest X-Ray (PA & Lateral)": {
                    "findings": "Cardiomegaly, bilateral cephalization of pulmonary veins, Kerley B lines, and blunting of costophrenic angles.",
                    "interpretation": "Classic radiographic hallmarks of acute biventricular congestive heart failure with interstitial pulmonary edema.",
                },
                "Basic Metabolic Panel (BMP)": {
                    "Sodium": "134 mEq/L",
                    "Potassium": "4.5 mEq/L",
                    "BUN": "28 mg/dL",
                    "Creatinine": "1.4 mg/dL",
                    "interpretation": "Mild prerenal azotemia secondary to cardiorenal syndrome and decreased effective arterial perfusion.",
                },
                "Complete Blood Count (CBC)": {
                    "WBC": "8.2 x10^3/uL",
                    "Hemoglobin": "12.8 g/dL",
                    "Hematocrit": "38.2%",
                    "Platelets": "210 x10^3/uL",
                    "interpretation": "Normal CBC indices.",
                },
            }

        elif archetype == "ENDOCRINOLOGY_DKA":
            true_dx = "Diabetic Ketoacidosis (DKA)"
            icd10 = "E11.10"
            acuity = TriageAcuity.EMERGENT
            differentials = ["Hyperosmolar Hyperglycemic State (HHS)", "Alcoholic Ketoacidosis", "Uremic Acidosis", "Lactic Acidosis"]
            recommended_labs = [
                LabTestType.BMP,
                LabTestType.ABG,
                LabTestType.CBC,
                LabTestType.URINALYSIS,
                LabTestType.LACTATE,
            ]
            contraindicated = ["Subcutaneous insulin monotherapy for severe DKA", "Hypokalemia ignored during insulin infusion"]
            optimal = [
                "Aggressive fluid resuscitation with 0.9% Normal Saline (1-1.5 L in 1st hour)",
                "Regular Insulin IV infusion 0.1 units/kg/hr after ensuring potassium > 3.3 mEq/L",
                "Potassium chloride supplementation (20-30 mEq/L IV fluids) once urine output established",
                "Point-of-care capillary glucose monitoring q1h; basic metabolic panel q2-4h",
                "Transition to D5W when blood glucose falls below 200 mg/dL to maintain gap closure",
            ]
            physical_exam = {
                "General": "Lethargic, deeply breathing with fruity/ketotic breath odor (Kussmaul breathing). Mucous membranes dry.",
                "Cardiovascular": "Tachycardia, regular rhythm, normal S1/S2, weak peripheral pulses.",
                "Respiratory": "Rapid, deep Kussmaul respirations. Lungs clear to auscultation bilaterally.",
                "Abdomen": "Diffuse mild epigastric tenderness without rebound or peritoneal signs.",
            }
            simulated_labs = {
                "Basic Metabolic Panel (BMP)": {
                    "Glucose": "486 mg/dL",
                    "Sodium": "131 mEq/L (corrected: 138 mEq/L)",
                    "Potassium": "5.4 mEq/L",
                    "Chloride": "98 mEq/L",
                    "Bicarbonate": "11 mEq/L",
                    "BUN": "36 mg/dL",
                    "Creatinine": "1.8 mg/dL",
                    "Anion_Gap": "22 mEq/L",
                    "flag": "CRITICAL_HIGH_GAP",
                    "interpretation": "Severe high anion gap metabolic acidosis with marked hyperglycemia and hyperkalemia.",
                },
                "Arterial Blood Gas (ABG)": {
                    "pH": "7.21",
                    "pCO2": "26 mmHg",
                    "pO2": "94 mmHg",
                    "HCO3": "10 mEq/L",
                    "flag": "METABOLIC_ACIDOSIS",
                    "interpretation": "Primary metabolic acidosis with respiratory compensatory hyperventilation (Kussmaul breathing).",
                },
                "Urinalysis": {
                    "Ketones": "Large (>= 80 mg/dL)",
                    "Glucose": ">= 1000 mg/dL",
                    "Protein": "Trace",
                    "interpretation": "Marked ketonuria and glycosuria verifying systemic ketoacidosis.",
                },
            }

        elif archetype == "PULMONOLOGY_CAP":
            true_dx = "Community-Acquired Pneumonia (CAP)"
            icd10 = "J18.9"
            acuity = TriageAcuity.URGENT
            differentials = ["Acute Bronchitis", "Pulmonary Embolism", "Exacerbation of COPD", "Heart Failure"]
            recommended_labs = [
                LabTestType.CBC,
                LabTestType.BMP,
                LabTestType.CXR,
                LabTestType.CMP,
                LabTestType.ABG,
            ]
            contraindicated = ["Antitussive suppression of productive cough", "Delaying antibiotic therapy beyond 4 hours"]
            optimal = [
                "Ceftriaxone 1g IV daily + Azithromycin 500mg IV daily",
                "Supplemental oxygen via nasal cannula targeting SpO2 94-98%",
                "IV hydration with balanced crystalloids",
                "Blood cultures x 2 and sputum analysis prior to antibiotic initiation if feasible",
            ]
            physical_exam = {
                "General": "Febrile, flushed, tachypneic with productive cough yielding rust-colored sputum.",
                "Respiratory": "Bronchial breath sounds and inspiratory crackles over the right lower lung base. Increased tactile fremitus.",
                "Cardiovascular": "Tachycardic, regular, no murmurs.",
                "Abdomen": "Soft, non-tender, benign.",
            }
            simulated_labs = {
                "Complete Blood Count (CBC)": {
                    "WBC": "16.8 x10^3/uL",
                    "Neutrophils": "84% (Left shift with bands)",
                    "Hemoglobin": "13.6 g/dL",
                    "Platelets": "285 x10^3/uL",
                    "flag": "LEUKOCYTOSIS_LEFT_SHIFT",
                    "interpretation": "Marked leukocytosis with neutrophilic left shift indicative of acute bacterial infection.",
                },
                "Chest X-Ray (PA & Lateral)": {
                    "findings": "Dense consolidation in the right lower lobe with patent air bronchograms. No large pleural effusion.",
                    "interpretation": "Lobar consolidation diagnostic of right lower lobe community-acquired pneumonia.",
                },
                "Basic Metabolic Panel (BMP)": {
                    "Sodium": "136 mEq/L",
                    "Potassium": "4.1 mEq/L",
                    "BUN": "22 mg/dL",
                    "Creatinine": "1.1 mg/dL",
                    "Glucose": "118 mg/dL",
                    "interpretation": "Mildly elevated BUN with stable baseline renal indices (CURB-65 component).",
                },
            }

        else:
            # General Internal Medicine Default
            true_dx = "Acute Unspecified Medical Condition"
            icd10 = "R69"
            acuity = TriageAcuity.URGENT
            differentials = ["Systemic Infection", "Metabolic Derangement", "Occult Inflammatory Syndrome"]
            recommended_labs = [LabTestType.CBC, LabTestType.BMP, LabTestType.URINALYSIS]
            contraindicated = ["Premature discharge without diagnostic clarification"]
            optimal = ["Supportive hydration", "Diagnostic laboratory evaluation", "Inpatient clinical monitoring"]
            physical_exam = {
                "General": f"Patient presenting with {complaint}. Alert, oriented, mildly fatigued.",
                "Cardiovascular": "Regular rate and rhythm, normal S1 and S2.",
                "Respiratory": "Clear to auscultation bilaterally, unlabored breathing.",
                "Abdomen": "Soft, non-distended, normoactive bowel sounds.",
            }
            simulated_labs = {
                "Complete Blood Count (CBC)": {
                    "WBC": "7.8 x10^3/uL",
                    "Hemoglobin": "13.4 g/dL",
                    "Platelets": "230 x10^3/uL",
                    "interpretation": "CBC parameters within normal physiological limits.",
                },
                "Basic Metabolic Panel (BMP)": {
                    "Sodium": "138 mEq/L",
                    "Potassium": "4.0 mEq/L",
                    "BUN": "16 mg/dL",
                    "Creatinine": "0.9 mg/dL",
                    "Glucose": "98 mg/dL",
                    "interpretation": "Metabolic panel demonstrates normal electrolyte and kidney profiles.",
                },
            }

        return PatientGroundTruth(
            id=case_id,
            name=name,
            age=age,
            sex=sex,
            triage_acuity=acuity,
            chief_complaint=complaint,
            history_of_present_illness=hpi,
            past_medical_history=pmh,
            medications=meds,
            allergies=allergies,
            baseline_vitals=vitals,
            true_diagnosis=true_dx,
            icd10_code=icd10,
            differential_candidates=differentials,
            recommended_labs=recommended_labs,
            contraindicated_treatments=contraindicated,
            optimal_treatment=optimal,
            simulated_labs=simulated_labs,
            physical_exam=physical_exam,
        )
