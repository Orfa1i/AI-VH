# Custom Synthea Modules: Clinical Assumptions and Design Rationale

This directory contains custom Synthea Generic Module Framework (GMF) state machines designed for the AI Virtual Hospital (AI-VH) benchmark specialties. These modules address critical clinical presentation gaps in standard Synthea distributions and provide realistic, reproducible disease trajectories for synthetic patient generation.

---

## 1. Overview and Clinical Governance

Standard Synthea builds model chronic outpatient progression well, but lack the acute physiologic granularity, laboratory kinetics, and rapid pharmacologic response sequences required for emergency and inpatient clinical reasoning.

Each custom module satisfies strict terminology and clinical constraints:
- **Laboratory and Diagnostic Observations:** Standard LOINC codes with Unified Code for Units of Measure (UCUM) syntax.
- **Medications:** Standard RxNorm clinical drug concepts.
- **Condition Diagnoses:** Standard SNOMED CT terminology.
- **State Machine Topology:** Fully connected deterministic and distributed transitions ensuring finite execution from Initial to Terminal states without orphan branches.

---

## 2. Module Specifications

### Module 1: Acute Coronary Syndrome (`acute_coronary_syndrome.json`)

- **Clinical Purpose:** Simulates acute ischemic chest pain presentation requiring emergency department triage, serial high-sensitivity cardiac troponins, and dual antiplatelet therapy.
- **Clinical Guidelines:** ACC/AHA Guideline for the Evaluation and Diagnosis of Chest Pain (PMID: 34709979) and Harrison's Principles of Internal Medicine (Chapter 269: ST-Segment Elevation Myocardial Infarction).
- **Target Prevalence:** ~3.5% incidence in simulated adult emergency encounters.
- **Physiologic & Laboratory Observations:**
  - `49563-0` (Cardiac troponin I by high sensitivity): initial baseline and 3-hour serial delta (`ng/L`)
  - `8480-6` (Systolic blood pressure): baseline hemodynamics (`mm[Hg]`)
  - `8867-4` (Heart rate): autonomic response (`/min`)
- **Severity Stratification:**
  - 40% ST-Elevation Myocardial Infarction (STEMI; SNOMED `401303003`)
  - 40% Non-ST-Elevation Myocardial Infarction (NSTEMI; SNOMED `401314000`)
  - 20% High-Risk Unstable Angina (SNOMED `371809000`)
- **Standard Pharmacotherapy:**
  - Aspirin (RxNorm `1191`)
  - Ticagrelor 90 MG (RxNorm `860975`)
  - Nitroglycerin sublingual (RxNorm `32968`)

---

### Module 2: Community-Acquired Pneumonia (`community_acquired_pneumonia.json`)

- **Clinical Purpose:** Simulates acute lower respiratory tract infection requiring inpatient admission, inflammatory biomarker quantification, and empiric antimicrobial regimens.
- **Clinical Guidelines:** ATS/IDSA Clinical Practice Guideline on Community-Acquired Pneumonia (PMID: 31573350) and Harrison's Principles of Internal Medicine (Chapter 121: Pneumonia).
- **Target Prevalence:** ~4.0% incidence in simulated adult inpatient admissions.
- **Physiologic & Laboratory Observations:**
  - `2708-6` (Oxygen saturation in Arterial blood): hypoxemia assessment (`%`)
  - `9279-1` (Respiratory rate): tachypnea assessment (`/min`)
  - `8310-5` (Body temperature): pyrexia (`Cel`)
  - `6690-2` (Leukocytes by automated count): leukocytosis (`10*3/uL`)
  - `34714-6` (Procalcitonin): bacterial biomarker stratification (`ug/L`)
- **Severity Stratification:**
  - 75% General Medical Floor Admission (CURB-65 score 1-2)
  - 25% Intensive Care Unit (ICU) Admission (severe CURB-65 score 3-5 or septic shock)
- **Standard Pharmacotherapy:**
  - Ceftriaxone 1000 MG Injection (RxNorm `309362`)
  - Azithromycin 500 MG Oral Tablet (RxNorm `2551`)

---

### Module 3: Diabetic Ketoacidosis (`diabetic_ketoacidosis.json`)

- **Clinical Purpose:** Simulates acute hyperglycemic metabolic decompensation characterized by severe insulinopenia, ketonemia, and high anion gap metabolic acidosis.
- **Clinical Guidelines:** ADA Standards of Medical Care in Diabetes: Hyperglycemic Crises (Diabetes Care 2024) and Harrison's Principles of Internal Medicine (Chapter 397: Diabetes Mellitus).
- **Target Prevalence:** ~1.8% incidence in simulated adult acute populations.
- **Physiologic & Laboratory Observations:**
  - `1558-6` (Glucose in Serum or Plasma): severe hyperglycemia (`mg/dL`)
  - `2744-1` (pH of Arterial blood): arterial acidemia (`[pH]`)
  - `1963-8` (Bicarbonate in Serum or Plasma): severe bicarbonate depletion (`mmol/L`)
  - `1989-3` (Beta-hydroxybutyrate in Serum or Plasma): diagnostic ketonemia (`mmol/L`)
  - `2823-3` (Potassium in Serum or Plasma): serum potassium monitoring (`mmol/L`)
- **Standard Resuscitation Pharmacotherapy:**
  - 0.9% Sodium Chloride IV infusion (RxNorm `313007`)
  - Regular Insulin 100 UNT/ML IV continuous infusion (RxNorm `311036`)
  - Potassium Chloride 20 MEQ/L in 0.9% NaCl IV piggyback (RxNorm `313002`)

---

## 3. Physician Sign-Off & Verification (H1 Checkpoint)

This document and associated modules will be formally reviewed in Human Checkpoint H1 (`docs/signoffs/H1-spotcheck.md`) by an attending physician prior to the Phase 1 Gate.
