"""
TEMPORARY Phase 2 compatibility adapter (remove in Phase 4).

Maps the Phase 2 AssessmentReport to the CURRENT backend/frontend response
fields (backend/clinical/models.py ClinicalReport shape, mirrored in
frontend/src/types.ts) so the existing frontend keeps working unchanged
until Phase 4 replaces the rendering with citation chips.

Owner: Software Engineer. Do not extend: Phase 4 replaces this module.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from vh.generation.v2_report import AssessmentReport


def _parse_bp(bp: Any) -> Dict[str, int]:
    """Parse 'sys/dia' string into systolic/diastolic ints (0 when unknown)."""
    try:
        parts = str(bp).split("/")
        return {"systolic_bp": int(parts[0]), "diastolic_bp": int(parts[1])}
    except (TypeError, ValueError, IndexError):
        return {"systolic_bp": 0, "diastolic_bp": 0}


def _citations_for_report(assessment: AssessmentReport, retrieval_log: Optional[Any]) -> List[Dict[str, Any]]:
    """Collect cited Harrison chunks (metadata + quote) for the legacy citations field."""
    wanted: List[str] = []
    for section in (
        [assessment.final_diagnosis, assessment.disposition]
        + list(assessment.differential_diagnosis)
        + list(assessment.severity_assessment)
        + list(assessment.workup)
        + list(assessment.treatment)
    ):
        for ev in section.evidence:
            if ev.source == "harrison" and ev.chunk_id and ev.chunk_id not in wanted:
                wanted.append(ev.chunk_id)
    chunks: Dict[str, Any] = {}
    if retrieval_log is not None:
        chunks = getattr(retrieval_log, "chunks", {}) or {}
    citations: List[Dict[str, Any]] = []
    for cid in wanted:
        stored = chunks.get(cid)
        metadata = dict(getattr(stored, "metadata", {}) or {})
        text = str(getattr(stored, "text", "") or "")
        # Prefer the model's verbatim supporting quote when present.
        quote = ""
        for section in (
            [assessment.final_diagnosis]
            + list(assessment.differential_diagnosis)
            + list(assessment.treatment)
            + list(assessment.workup)
        ):
            for ev in section.evidence:
                if ev.chunk_id == cid and ev.supporting_quote:
                    quote = ev.supporting_quote
                    break
        citations.append(
            {
                "id": cid,
                "book": metadata.get("book", "Harrison's Principles of Internal Medicine, 21st Edition (2022)"),
                "chapter": metadata.get("chapter_title") or metadata.get("chapter", ""),
                "topic": metadata.get("section_heading") or metadata.get("topic", ""),
                "page": metadata.get("page"),
                "specialty": "Internal Medicine",
                "text": quote or text[:500],
                "relevance_score": float(getattr(stored, "score", 0.0) or 0.0),
            }
        )
    return citations


def assessment_to_legacy_report(
    assessment: AssessmentReport,
    structured_case: Dict[str, Any],
    patient: Dict[str, Any],
    encounter_id: str,
    retrieval_log: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Map a Phase 2 assessment onto the current ClinicalReport response fields.
    Every legacy field is populated; nothing clinical is dropped silently:
    severity, red flags, follow-up and conflicts ride in clinical_reasoning
    provenance via the v2 report id (full v2 JSON stays in pipeline metadata).
    """
    vitals = structured_case.get("vitals", {}) or {}
    bp = _parse_bp(vitals.get("bp"))

    def _num(value: Any, default: float = 0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    differential = [
        {
            "condition": d.diagnosis,
            "likelihood": float(d.probability),
            "supporting_points": list(d.supporting_findings),
            "opposing_points": list(d.against_findings),
        }
        for d in assessment.differential_diagnosis
    ]
    treatment_plan = [
        f"{t.item} — {t.dose_route_frequency_duration} ({t.rationale})".strip(" —()")
        for t in assessment.treatment
    ]

    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": assessment.report_id,
        "encounter_id": encounter_id,
        "patient_id": str(patient.get("id") or patient.get("patient_id") or ""),
        "patient_name": str(patient.get("name") or patient.get("patient_name") or ""),
        "patient_age": int(patient.get("age") if patient.get("age") is not None else (structured_case.get("age") or 0)),
        "patient_sex": str(patient.get("sex") or structured_case.get("sex") or ""),
        "created_at": now,
        "chief_complaint": assessment.chief_complaint,
        "history_of_present_illness": assessment.case_summary,
        "past_medical_history": list(structured_case.get("comorbidities", []) or []),
        "medications": list(structured_case.get("current_medications", []) or []),
        "allergies": list(structured_case.get("allergies", []) or []),
        "vital_signs": {
            "timestamp": now,
            "heart_rate": int(_num(vitals.get("hr"))),
            "systolic_bp": bp["systolic_bp"],
            "diastolic_bp": bp["diastolic_bp"],
            "respiratory_rate": int(_num(vitals.get("rr"))),
            "temperature_c": float(_num(vitals.get("temp"))),
            "spo2_percent": float(_num(vitals.get("spo2"))),
            "pain_score": 0,
        },
        "physical_exam_findings": {"examination": structured_case.get("examination_findings") or ""},
        "investigations_ordered": [w.test for w in assessment.workup],
        "investigation_results": [],
        "differential_diagnosis": differential,
        "primary_diagnosis": assessment.final_diagnosis.diagnosis,
        "diagnostic_confidence": float(assessment.final_diagnosis.confidence),
        "clinical_reasoning": assessment.clinical_reasoning,
        "treatment_plan": treatment_plan,
        "recommended_disposition": f"{assessment.disposition.setting}: {assessment.disposition.rationale}",
        "medical_knowledge_citations": _citations_for_report(assessment, retrieval_log),
        "pharmacist_review": None,
        # Traceability back to the full v2 assessment (stored in pipeline metadata).
        "assessment_report_id": assessment.report_id,
        "prompt_version": assessment.prompt_version,
    }
