"""
TEMPORARY Phase 2 grounded-path shim for the legacy encounter flow.

When VH_PIPELINE=grounded, step 5 of conduct_clinical_encounter routes through
src/vh grounded assessment (mandatory Harrison retrieval + v2 schema) and maps
the result back onto the legacy decision/citation shapes. Any other mode (or
any grounded-path failure) returns None and the caller uses the legacy
MedGemma path unchanged. Rollback is a flag change only.

Legacy run(), generate_clinical_decision() and medgemma_service paths are NOT
modified and must not be deleted before Phase 6.

Owner: Software Engineer.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("GroundedShim")


def maybe_grounded_assessment(
    patient_info: Dict[str, Any],
    vital_signs: Any,
    exam_findings: Dict[str, str],
    lab_results: List[Dict[str, Any]],
    case_id: str,
) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    Return (decision_dict, citations) for the grounded path, or None to stay legacy.

    decision_dict carries exactly the keys conduct_clinical_encounter consumes:
    primary_diagnosis, confidence, differential[{condition, likelihood,
    supporting_points, opposing_points}], clinical_reasoning, treatment_plan,
    recommended_disposition.
    """
    from vh.generation.flag import is_grounded

    if not is_grounded():
        return None

    try:
        return _run_grounded(patient_info, vital_signs, exam_findings, lab_results, case_id)
    except Exception as exc:
        logger.warning(f"Grounded assessment unavailable ({exc}); falling back to legacy decision path.")
        return None


def _pipeline_class() -> Any:
    """Lazy vh import (keeps legacy backend import graph untouched)."""
    from vh.generation.pipeline import GroundedGenerationPipeline

    return GroundedGenerationPipeline


def _run_grounded(
    patient_info: Dict[str, Any],
    vital_signs: Any,
    exam_findings: Dict[str, str],
    lab_results: List[Dict[str, Any]],
    case_id: str,
) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    from vh.cases.structured_case import extract_structured_case, structured_case_to_agentview_dict
    from vh.generation.medgemma import MedGemmaAdapter, Phase2GenerationConfig

    def _vital(name: str, default: Any = None) -> Any:
        if isinstance(vital_signs, dict):
            return vital_signs.get(name, default)
        return getattr(vital_signs, name, default)

    sys_bp = _vital("systolic_bp")
    dia_bp = _vital("diastolic_bp")
    bp_str = f"{sys_bp}/{dia_bp}" if sys_bp and dia_bp else None

    labs: Dict[str, Any] = {}
    for item in lab_results or []:
        if isinstance(item, dict):
            key = str(item.get("test_type") or item.get("order_name") or "lab")
            labs[key] = item.get("interpretation") or item.get("result") or item.get("values")

    raw_case = {
        "age": patient_info.get("age"),
        "sex": patient_info.get("sex"),
        "presenting_symptoms": [str(patient_info.get("chief_complaint") or "")],
        "vitals": {
            "temp": _vital("temperature_c"),
            "hr": _vital("heart_rate"),
            "rr": _vital("respiratory_rate"),
            "bp": bp_str,
            "spo2": _vital("spo2_percent"),
        },
        "examination_findings": json.dumps(exam_findings or {}),
        "comorbidities": patient_info.get("past_medical_history") or [],
        "current_medications": patient_info.get("medications") or [],
        "allergies": patient_info.get("allergies") or [],
        "labs": labs,
        "imaging": {},
    }
    structured = extract_structured_case(raw_case)
    structured_dict = structured_case_to_agentview_dict(structured)

    pipeline = _pipeline_class()(adapter=MedGemmaAdapter())
    result = pipeline.run_grounded_assessment(
        case_id=case_id,
        specialty="Internal Medicine",
        structured_case=structured_dict,
        phase2_config=Phase2GenerationConfig(),
    )
    metadata = result.metadata or {}
    if metadata.get("generation_status") != "success":
        return None

    assessment = metadata["assessment_report"]
    final = assessment["final_diagnosis"]
    differential = [
        {
            "condition": d["diagnosis"],
            "likelihood": float(d["probability"]),
            "supporting_points": list(d.get("supporting_findings", [])),
            "opposing_points": list(d.get("against_findings", [])),
        }
        for d in assessment["differential_diagnosis"]
    ]
    decision = {
        "primary_diagnosis": final["diagnosis"],
        "confidence": float(final["confidence"]),
        "differential": differential,
        "clinical_reasoning": assessment["clinical_reasoning"],
        "treatment_plan": [
            f"{t['item']} — {t['dose_route_frequency_duration']}".strip(" —")
            for t in assessment["treatment"]
        ],
        "recommended_disposition": (
            f"{assessment['disposition']['setting']}: {assessment['disposition']['rationale']}"
        ),
    }

    log_chunks = (metadata.get("retrieval_log", {}) or {}).get("chunks", {})
    wanted: List[str] = []
    for section in [final] + assessment["differential_diagnosis"]:
        for ev in section.get("evidence", []):
            if ev.get("source") == "harrison" and ev.get("chunk_id") and ev["chunk_id"] not in wanted:
                wanted.append(ev["chunk_id"])
    citations = []
    for cid in wanted:
        stored = log_chunks.get(cid, {})
        meta = stored.get("metadata", {}) if isinstance(stored, dict) else {}
        citations.append(
            {
                "id": cid,
                "book": meta.get("book", "Harrison's Principles of Internal Medicine, 21st Edition (2022)"),
                "chapter": meta.get("chapter_title") or meta.get("chapter", ""),
                "topic": meta.get("section_heading") or meta.get("topic", ""),
                "page": meta.get("page"),
                "specialty": "Internal Medicine",
                "text": (stored.get("text", "") if isinstance(stored, dict) else "")[:500],
            }
        )
    return decision, citations
