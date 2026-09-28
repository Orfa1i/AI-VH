"""
Clinical terminology registry and fixture catalog for Synthea modules.
Provides validated LOINC, UCUM, RxNorm, and SNOMED CT codes for offline verification.
"""

from typing import Dict, Set

VALID_LOINC_CODES: Dict[str, str] = {
    "49563-0": "Cardiac troponin I in Serum or Plasma by High sensitivity method",
    "10839-9": "Troponin I.cardiac in Serum or Plasma",
    "8867-4": "Heart rate",
    "8480-6": "Systolic blood pressure",
    "8462-4": "Diastolic blood pressure",
    "85354-9": "Blood pressure systolic & diastolic",
    "2708-6": "Oxygen saturation in Arterial blood",
    "59408-5": "Oxygen saturation in Arterial blood by Pulse oximetry",
    "9279-1": "Respiratory rate",
    "8310-5": "Body temperature",
    "2744-1": "pH of Arterial blood",
    "2028-9": "Carbon dioxide in Arterial blood",
    "2703-7": "Oxygen in Arterial blood",
    "1988-5": "Base deficit in Arterial blood",
    "1558-6": "Glucose in Serum or Plasma",
    "2823-3": "Potassium in Serum or Plasma",
    "2951-2": "Sodium in Serum or Plasma",
    "2075-0": "Chloride in Serum or Plasma",
    "1963-8": "Bicarbonate in Serum or Plasma",
    "1989-3": "Beta hydroxybutyrate in Serum or Plasma",
    "34714-6": "Procalcitonin in Serum or Plasma",
    "6690-2": "Leukocytes in Blood by Automated count",
    "33914-3": "Glomerular filtration rate/1.73 sq M.predicted",
}

VALID_UCUM_UNITS: Set[str] = {
    "ng/L",
    "ng/mL",
    "pg/mL",
    "/min",
    "mm[Hg]",
    "%",
    "Cel",
    "[degF]",
    "[pH]",
    "mmol/L",
    "meq/L",
    "mEq/L",
    "mg/dL",
    "ug/L",
    "10*3/uL",
    "mL/min/{1.73_m2}",
}

VALID_RXNORM_CODES: Dict[str, str] = {
    "1191": "Aspirin",
    "860975": "Ticagrelor 90 MG Oral Tablet",
    "308056": "Clopidogrel 75 MG Oral Tablet",
    "32968": "Nitroglycerin sublingual",
    "6809": "Metoprolol Tartrate 25 MG Oral Tablet",
    "7052": "Morphine sulfate 4 MG/ML Injectable Solution",
    "309362": "Ceftriaxone 1000 MG Injection",
    "2551": "Azithromycin 500 MG Oral Tablet",
    "6876": "Moxifloxacin 400 MG Oral Tablet",
    "311036": "Regular Insulin 100 UNT/ML Injectable Solution",
    "313002": "Potassium Chloride 20 MEQ/L in 0.9% Sodium Chloride Injection",
    "313007": "0.9% Sodium Chloride Injection",
}

VALID_SNOMED_CODES: Dict[str, str] = {
    "22298006": "Myocardial infarction",
    "401303003": "Acute ST segment elevation myocardial infarction",
    "401314000": "Acute non-ST segment elevation myocardial infarction",
    "371809000": "Acute coronary syndrome",
    "233604007": "Pneumonia",
    "385093006": "Community acquired pneumonia",
    "46635009": "Diabetes mellitus type 1 with ketoacidosis",
    "38341003": "Hypertension",
    "53741008": "Coronary arteriosclerosis",
    "44054006": "Type 2 diabetes mellitus",
}
