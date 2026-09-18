"""
Clinical Intent Routing and Dialogue Sanitizer
Provides classification to distinguish clinical patient inquiries from conversational greetings / chatter,
preventing over-medicalization and suppressing chain-of-thought leakage.
"""

import re
from typing import Any, Dict, Optional

# Keywords that indicate clinical intent (symptoms, anatomy, diseases, diagnostics, pharmacological)
CLINICAL_KEYWORDS = {
    # Symptoms & signs
    'pain', 'ache', 'hurts', 'hurting', 'fever', 'febrile', 'chills', 'cough', 'coughing',
    'dyspnea', 'shortness of breath', 'sob', 'breathless', 'nausea', 'vomit', 'vomiting',
    'diarrhea', 'bleeding', 'hemorrhage', 'rash', 'swelling', 'swollen', 'edema', 'seizure',
    'syncope', 'faint', 'fainted', 'dizziness', 'dizzy', 'vertigo', 'numbness', 'weakness',
    'altered', 'confusion', 'lethargy', 'malaise', 'diaphoresis', 'sweating', 'angina',
    'palpitation', 'palpitations', 'tachycardia', 'bradycardia', 'hypotension', 'hypertension',
    'oliguria', 'polyuria', 'polydipsia', 'jaundice', 'cyanosis', 'pallor', 'kussmaul',
    'symptom', 'symptoms',
    # Anatomy & organ systems
    'chest', 'substernal', 'precordial', 'abdomen', 'abdominal', 'belly', 'head', 'headache',
    'neck', 'flank', 'epigastric', 'heart', 'cardiac', 'myocardial', 'coronary', 'pulmonary',
    'lung', 'respiratory', 'renal', 'kidney', 'hepatic', 'liver', 'neuro', 'neurological',
    'brain', 'vascular', 'arterial', 'venous', 'dvt', 'vessel', 'arm', 'leg', 'back',
    # Diseases & clinical conditions
    'infarction', 'infarct', 'nstemi', 'stemi', 'acs', 'pericarditis', 'myocarditis', 'dissection',
    'embolism', 'pe', 'thrombus', 'thrombosis', 'pneumonia', 'pneumothorax', 'asthma', 'copd',
    'dka', 'ketoacidosis', 'hhs', 'diabetes', 'hyperglycemia', 'hypoglycemia', 'acidosis',
    'aki', 'atn', 'failure', 'shock', 'sepsis', 'infection', 'stroke', 'tia', 'arrhythmia',
    'hyperkalemia', 'hypokalemia', 'disease', 'diseases', 'illness', 'syndrome',
    # Diagnostics & laboratory tests
    'troponin', 'ecg', 'ekg', 'bnp', 'dimer', 'd-dimer', 'creatinine', 'bun', 'potassium',
    'sodium', 'glucose', 'lactate', 'hemoglobin', 'wbc', 'platelet', 'inr', 'ct', 'mri',
    'xray', 'cxr', 'ultrasound', 'echo', 'vitals', 'bp', 'hr', 'spo2', 'pulse',
    'lab', 'labs', 'laboratory', 'investigation', 'investigations',
    # Clinical actions & intent
    'diagnose', 'diagnosing', 'diagnostic', 'diagnostics', 'diagnosis', 'differential',
    'differentials', 'workup', 'treatment', 'treatments', 'regimen', 'therapy', 'therapies',
    'protocol', 'guideline', 'prescribe', 'prescribed', 'prescription', 'medication', 'medications',
    'drug', 'drugs', 'dose', 'dosing', 'contraindication', 'contraindicated', 'contraindications',
    'prognosis', 'patient', 'patients', 'hpi', 'chief complaint', 'consult',
    # Arabic clinical terms
    'ألم', 'الم', 'وجع', 'صدر', 'صدري', 'قلب', 'قلبي', 'تنفس', 'ضيق', 'حرارة',
    'حمى', 'سخونة', 'بطن', 'مغص', 'سكر', 'سكري', 'ضغط', 'كلى', 'كلوية', 'دوار',
    'دوخة', 'جلطة', 'تخثر', 'نزيف', 'تسمم', 'التهاب', 'سعال', 'كحة', 'غثيان',
    'قيء', 'استفراغ', 'إسهال', 'اسهال', 'طفح', 'تورم', 'انتفاخ', 'ورم', 'تشنج',
    'إغماء', 'اغماء', 'خفقان', 'تشخيص', 'علاج', 'دواء', 'أدوية', 'فحص', 'تحليل',
    'مريض', 'حالة'
}

# Compiled regex for whole-word matching of clinical keywords
CLINICAL_REGEX = re.compile(
    r'\b(?:' + '|'.join(re.escape(k) for k in sorted(CLINICAL_KEYWORDS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)

# Conversational greetings, identity inquiries, and pleasantries (English)
GREETING_STARTERS = (
    r'(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening|day)|'
    r'how\s+are\s+you(?:(?:\s+doing)?|\s+today)?|'
    r'who\s+are\s+you|what\s+is\s+your\s+name|what\s+is\s+your\s+role|what\s+do\s+you\s+do|'
    r'tell\s+me\s+about\s+yourself|thanks|thank\s+you(?: so much)?|'
    r'bye|goodbye|see\s+you|nice\s+to\s+meet\s+you|ok|okay|yes|no|test|testing)'
)
GREETING_SUFFIXES = (
    r'(?:[\s,]+(?:doctor|doc|dr\.?(?:\s+vance)?|marcus|vance|there|all|everyone|today))?'
)
GREETINGS_PATTERN = re.compile(
    rf'^{GREETING_STARTERS}{GREETING_SUFFIXES}[\s\.,!\?]*$',
    re.IGNORECASE
)

# Conversational greetings (Arabic)
ARABIC_GREETINGS = [
    'مرحبا', 'مرحباً', 'أهلا', 'أهلاً', 'السلام عليكم', 'سلام',
    'صباح الخير', 'مساء الخير', 'كيف حالك', 'كيفك', 'من أنت', 'مين انت',
    'شكرا', 'شكراً', 'يعطيك العافية', 'تمام', 'أوك', 'اوك', 'هلا'
]


def is_clinical_query(text: str, patient_context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Evaluates whether the user's input is a clinical medical inquiry or non-clinical chatter.
    Returns True if clinical data/questions are detected; False for conversational greetings/pleasantries.
    """
    # If patient context contains active clinical fields, treat as clinical
    if patient_context:
        for key in ('chief_complaint', 'vitals', 'hpi', 'diagnosis', 'abnormal_labs'):
            val = patient_context.get(key)
            if val and str(val).strip():
                return True

    clean = (text or '').strip()
    if not clean:
        return False

    clean_lower = clean.lower()

    # Direct match for standard English greetings & pleasantries
    if GREETINGS_PATTERN.match(clean_lower):
        return False

    # Direct match for standard Arabic greetings
    arabic_norm = re.sub(r'[\s\.,!\?]+', ' ', clean).strip()
    arabic_without_honorific = re.sub(
        r'\s+(?:يا\s+)?(?:دكتور|دكتورة|د\.|د/|طبيب|ماركوس|فانس).*$', '', arabic_norm
    ).strip()
    if any(arabic_norm == g or arabic_without_honorific == g for g in ARABIC_GREETINGS):
        return False

    # Check for presence of clinical keywords using word boundaries
    if CLINICAL_REGEX.search(clean):
        return True

    # If the message is short (< 30 characters) and has no clinical keywords, it's non-clinical chatter
    if len(clean) < 30 and not CLINICAL_REGEX.search(clean):
        return False

    # Longer queries without explicit greetings default to clinical
    return True


def clean_doctor_dialogue_text(text: str) -> str:
    """
    Sanitizes raw generation from MedGemma:
    - Strips internal thought tags (<unused94>thought, <thought>...</thought>).
    - Removes leaked numbered chain-of-thought planning steps (e.g. '1. Identify the core clinical problem').
    - Removes prompt echoes and model role prefixes.
    """
    if not text:
        return ""

    # 1. Strip raw thought tags and unused token markers
    clean = re.sub(r"(?:<unused\d+>)?thought[\s\S]*?(?:</thought>|\n\n(?=[A-Z0-9*#]))", "", text, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^thought\b.*?\n\n", "", clean, flags=re.DOTALL | re.IGNORECASE).strip()
    clean = re.sub(r"^thought\s+", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"<unused\d+>", "", clean).strip()

    # 2. Strip prompt echoes / prefixes
    clean = re.sub(r"^(?:Dr\. Marcus Vance Response:|Dr\. Marcus Vance:|Response:|Attending Response:)\s*", "", clean, flags=re.IGNORECASE).strip()

    # 3. Strip meta-reasoning / numbered chain-of-thought planning steps
    cot_pattern = r"(?im)^\s*\d+\.\s*\*{0,2}(?:Identify|Formulate|Consider|Determine|Evaluate|Analyze|Review)\b[^\n]*\n?"
    clean = re.sub(cot_pattern, "", clean).strip()

    # Strip sub-bullets if left over under stripped CoT (e.g., "    *   STEMI: Must be ruled out...")
    clean = re.sub(r"(?im)^\s*\*\s+\*\*[A-Z\s]+\*\*:[^\n]*\n?", "", clean).strip()

    # If cleaning stripped everything because the entire generation was meta-reasoning, fallback to empty
    return clean
