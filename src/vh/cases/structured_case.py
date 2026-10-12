"""
Phase 1 structured case extraction for AI-VH.

Converts a raw case into a structured object BEFORE retrieval. The extractor
never infers or invents values: anything not explicitly present in the raw
case is None (or empty) and its field name is listed in `missing_data`.

Owner: Software Engineer.
Clinical spec: Medical Expert.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StructuredVitals(BaseModel):
    """Triage vitals. Every field nullable; absent means not provided."""

    temp: Optional[float] = Field(default=None, description="Body temperature in deg C")
    hr: Optional[int] = Field(default=None, description="Heart rate in bpm")
    rr: Optional[int] = Field(default=None, description="Respiratory rate in breaths/min")
    bp: Optional[str] = Field(default=None, description="Blood pressure as 'sys/dia' string")
    spo2: Optional[float] = Field(default=None, description="Oxygen saturation in %")


class StructuredCase(BaseModel):
    """
    Structured clinical case used as the retrieval input.

    chief_complaint holds symptoms + duration only, never a diagnosis.
    missing_data lists every key field not provided in the raw case.
    """

    age: Optional[int] = None
    sex: Optional[str] = None
    presenting_symptoms: List[str] = Field(default_factory=list)
    symptom_duration: Optional[str] = None
    chief_complaint: str = Field(default="", description="Symptoms + duration only, never a diagnosis")
    vitals: StructuredVitals = Field(default_factory=StructuredVitals)
    examination_findings: Optional[str] = None
    comorbidities: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    labs: Dict[str, Any] = Field(default_factory=dict)
    imaging: Dict[str, Any] = Field(default_factory=dict)
    missing_data: List[str] = Field(default_factory=list)


_MISSING_LABELS = {
    "age": "age",
    "sex": "sex",
    "presenting_symptoms": "presenting_symptoms",
    "symptom_duration": "symptom_duration",
    "vitals.temp": "vitals.temp",
    "vitals.hr": "vitals.hr",
    "vitals.rr": "vitals.rr",
    "vitals.bp": "vitals.bp",
    "vitals.spo2": "vitals.spo2",
    "examination_findings": "examination_findings",
    "comorbidities": "comorbidities",
    "current_medications": "current_medications",
    "allergies": "allergies",
    "labs": "labs",
    "imaging": "imaging",
}


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _get(raw: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    lowered = {str(k).lower(): v for k, v in raw.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()] not in (None, ""):
            return lowered[key.lower()]
    return None


def extract_structured_case(raw_case: Dict[str, Any]) -> StructuredCase:
    """
    Build a StructuredCase from a raw case dict without inventing values.

    Reads only explicitly provided keys; everything else becomes None/empty
    and is recorded in missing_data. Never guesses vitals, labs, durations
    or examination findings.
    """
    raw: Dict[str, Any] = dict(raw_case or {})

    age_val = _get(raw, "age")
    age: Optional[int] = None
    if age_val is not None:
        try:
            age = int(age_val)
        except (TypeError, ValueError):
            age = None

    sex = _get(raw, "sex", "gender")
    sex_str: Optional[str] = str(sex).strip() if sex is not None else None
    if sex_str == "":
        sex_str = None

    symptoms = _as_list(_get(raw, "presenting_symptoms", "symptoms"))
    duration_val = _get(raw, "symptom_duration", "duration")
    duration: Optional[str] = str(duration_val).strip() if duration_val is not None else None
    if duration == "":
        duration = None

    if symptoms and duration:
        chief = f"{'; '.join(symptoms)} for {duration}"
    elif symptoms:
        chief = "; ".join(symptoms)
    else:
        chief = ""

    vitals_raw = _as_dict(_get(raw, "vitals", "initial_vitals"))

    def _num(key: str) -> Any:
        return vitals_raw.get(key, vitals_raw.get(key.lower(), vitals_raw.get(key.upper())))

    def _opt_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _opt_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    bp_val = _num("bp") if _num("bp") is not None else _num("blood_pressure")
    bp_str: Optional[str] = str(bp_val).strip() if bp_val not in (None, "") else None

    vitals = StructuredVitals(
        temp=_opt_float(_num("temp") if _num("temp") is not None else _num("temperature")),
        hr=_opt_int(_num("hr") if _num("hr") is not None else _num("heart_rate")),
        rr=_opt_int(_num("rr") if _num("rr") is not None else _num("respiratory_rate")),
        bp=bp_str,
        spo2=_opt_float(_num("spo2") if _num("spo2") is not None else _num("o2_sat")),
    )

    exam_val = _get(raw, "examination_findings", "exam", "physical_exam")
    exam: Optional[str] = str(exam_val).strip() if exam_val not in (None, "") else None

    comorbidities = _as_list(_get(raw, "comorbidities", "past_medical_history", "history"))
    medications = _as_list(_get(raw, "current_medications", "medications", "meds"))
    allergies = _as_list(_get(raw, "allergies"))
    labs = _as_dict(_get(raw, "labs", "initial_labs", "laboratory"))
    imaging = _as_dict(_get(raw, "imaging"))

    missing: List[str] = []
    if age is None:
        missing.append(_MISSING_LABELS["age"])
    if not sex_str:
        missing.append(_MISSING_LABELS["sex"])
    if not symptoms:
        missing.append(_MISSING_LABELS["presenting_symptoms"])
    if not duration:
        missing.append(_MISSING_LABELS["symptom_duration"])
    if vitals.temp is None:
        missing.append(_MISSING_LABELS["vitals.temp"])
    if vitals.hr is None:
        missing.append(_MISSING_LABELS["vitals.hr"])
    if vitals.rr is None:
        missing.append(_MISSING_LABELS["vitals.rr"])
    if not vitals.bp:
        missing.append(_MISSING_LABELS["vitals.bp"])
    if vitals.spo2 is None:
        missing.append(_MISSING_LABELS["vitals.spo2"])
    if not exam:
        missing.append(_MISSING_LABELS["examination_findings"])
    if not comorbidities:
        missing.append(_MISSING_LABELS["comorbidities"])
    if not medications:
        missing.append(_MISSING_LABELS["current_medications"])
    if not allergies:
        missing.append(_MISSING_LABELS["allergies"])
    if not labs:
        missing.append(_MISSING_LABELS["labs"])
    if not imaging:
        missing.append(_MISSING_LABELS["imaging"])

    return StructuredCase(
        age=age,
        sex=sex_str,
        presenting_symptoms=symptoms,
        symptom_duration=duration,
        chief_complaint=chief,
        vitals=vitals,
        examination_findings=exam,
        comorbidities=comorbidities,
        current_medications=medications,
        allergies=allergies,
        labs=labs,
        imaging=imaging,
        missing_data=missing,
    )


def structured_case_to_agentview_dict(case: StructuredCase) -> Dict[str, Any]:
    """Render a StructuredCase as plain retrieval-input dict (no hidden data)."""
    return {
        "age": case.age,
        "sex": case.sex,
        "chief_complaint": case.chief_complaint,
        "presenting_symptoms": list(case.presenting_symptoms),
        "symptom_duration": case.symptom_duration,
        "vitals": case.vitals.model_dump(),
        "examination_findings": case.examination_findings,
        "comorbidities": list(case.comorbidities),
        "current_medications": list(case.current_medications),
        "allergies": list(case.allergies),
        "labs": dict(case.labs),
        "imaging": dict(case.imaging),
        "missing_data": list(case.missing_data),
    }
