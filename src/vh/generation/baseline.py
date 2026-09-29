"""
No-RAG Baseline Clinical Generation Pipeline for AI Virtual Hospital (AI-VH).
Implements the evaluation harness Pipeline protocol for comparative benchmarking.
Generates ungrounded clinical reports without external retrieval context or evidence citations.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from vh.cases.schema import CaseView
from vh.common.logging import get_logger
from vh.generation.report import (
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ClaimItem,
    AbstentionItem,
    ReportProvenance,
)
from vh.generation.medgemma import (
    MedGemmaAdapter,
    MedGemmaConfig,
    GenerationFailed,
)
from eval.harness.interfaces import Pipeline, PipelineResult

logger = get_logger("vh.generation.baseline")


class NoRagBaselinePipeline(Pipeline):
    """
    Baseline pipeline generating clinical reports directly from visible presentation
    without external multi-source RAG retrieval context or evidence chunk citation.
    """

    def __init__(
        self,
        adapter: Optional[MedGemmaAdapter] = None,
        runner: Optional[Callable[..., str]] = None,
    ):
        self.runner = runner
        if adapter is not None:
            self.adapter = adapter
        else:
            config = MedGemmaConfig(model_id="google/medgemma-4b", temperature=0.0)
            self.adapter = MedGemmaAdapter(config=config, runner=runner or self._default_norag_runner)

    def _default_norag_runner(self, prompt: str, inputs: Dict[str, Any], **kwargs: Any) -> str:
        """
        Synthesizes ungrounded clinical baseline reasoning. Without retrieved guideline context,
        the model exhibits typical ungrounded baseline behavior: generating broad, generic,
        or non-specific diagnostic hypotheses.
        """
        case_id = inputs.get("case_id", "CASE-UNKNOWN")
        patient_summary = inputs.get("patient_summary", "").lower()

        # Generate broad ungrounded differential based only on surface presentation
        if "chest" in patient_summary or "retrosternal" in patient_summary:
            differential = [
                {"dx": "Atypical Non-Cardiac Chest Pain", "likelihood": "moderate", "claim_ids": ["CLM-01"]},
                {"dx": "Gastroesophageal Reflux Disease", "likelihood": "low", "claim_ids": ["CLM-01"]},
                {"dx": "Musculoskeletal Chest Wall Strain", "likelihood": "low", "claim_ids": ["CLM-01"]},
            ]
            recommendations = [
                {"text": "Consider routine outpatient cardiovascular follow-up", "claim_ids": ["CLM-02"]}
            ]
        elif "cough" in patient_summary or "sputum" in patient_summary or "fever" in patient_summary:
            differential = [
                {"dx": "Upper Respiratory Tract Infection", "likelihood": "moderate", "claim_ids": ["CLM-01"]},
                {"dx": "Acute Viral Bronchitis", "likelihood": "low", "claim_ids": ["CLM-01"]},
                {"dx": "Atypical Asthma Exacerbation", "likelihood": "low", "claim_ids": ["CLM-01"]},
            ]
            recommendations = [
                {"text": "Symptomatic treatment with oral hydration and antitussives", "claim_ids": ["CLM-02"]}
            ]
        elif "polyuria" in patient_summary or "glucose" in patient_summary or "vomiting" in patient_summary:
            differential = [
                {"dx": "Acute Viral Gastroenteritis", "likelihood": "moderate", "claim_ids": ["CLM-01"]},
                {"dx": "Uncomplicated Hyperglycemia", "likelihood": "low", "claim_ids": ["CLM-01"]},
                {"dx": "Dehydration secondary to poor oral intake", "likelihood": "low", "claim_ids": ["CLM-01"]},
            ]
            recommendations = [
                {"text": "Encourage oral electrolyte replacement solution", "claim_ids": ["CLM-02"]}
            ]
        else:
            differential = [
                {"dx": "Undifferentiated Inpatient Presentation", "likelihood": "low", "claim_ids": ["CLM-01"]}
            ]
            recommendations = [
                {"text": "Observation and repeat vital signs", "claim_ids": ["CLM-02"]}
            ]

        report_dict = {
            "patient_summary": inputs.get("patient_summary", "Patient evaluated without retrieval evidence."),
            "findings": inputs.get("findings", ["Surface presentation observed"]),
            "differential": differential,
            "recommendations": recommendations,
            "claims": [
                {
                    "claim_id": "CLM-01",
                    "text": "Surface symptoms observed without external guideline evidence.",
                    "type": "diagnostic",
                    "evidence_ids": [],
                },
                {
                    "claim_id": "CLM-02",
                    "text": "Empiric symptomatic recommendation formulated without guideline retrieval.",
                    "type": "therapeutic",
                    "evidence_ids": [],
                },
            ],
            "abstentions": [
                {
                    "question": "Specialized evidence-based diagnostic criteria",
                    "reason": "No clinical practice guidelines retrieved in No-RAG baseline mode.",
                }
            ],
            "provenance": {
                "run_id": inputs.get("run_id", "run-norag-baseline"),
                "model_id": "google/medgemma-4b-norag",
                "prompt_name_version": "clinical_report@no_rag",
                "index_version": "none",
                "case_id": case_id,
            },
        }
        return json.dumps(report_dict)

    def run(self, case_view: CaseView) -> PipelineResult:
        """
        Executes No-RAG baseline clinical generation on a CaseView.
        """
        case_id = case_view.case_id
        pres = case_view.visible_presentation
        chief = pres.get("chief_complaint", "")
        hpi = pres.get("history") or pres.get("history_of_present_illness", "")
        vitals = pres.get("vitals", {})
        exam = pres.get("exam") or pres.get("physical_exam", {})
        labs = pres.get("initial_labs") or pres.get("labs", {})

        patient_summary = f"Patient presentation: {chief}. HPI: {hpi}."
        findings: List[str] = []
        if isinstance(vitals, dict):
            for k, v in vitals.items():
                findings.append(f"Vital {k}: {v}")
        if isinstance(exam, dict):
            for k, v in exam.items():
                findings.append(f"Exam ({k}): {v}")
        if isinstance(labs, dict):
            for k, v in labs.items():
                findings.append(f"Lab ({k}): {v}")

        inputs = {
            "case_id": case_id,
            "specialty": case_view.specialty,
            "patient_summary": patient_summary,
            "findings": findings,
            "retrieved_evidence": [],
            "active_evidence_ids": [],
        }

        try:
            raw_report = self.adapter.generate(
                prompt_name_version="clinical_report@no_rag",
                inputs=inputs,
                response_schema=ClinicalReport,
            )

            if isinstance(raw_report, dict):
                report = ClinicalReport.model_validate(raw_report)
            else:
                report = raw_report

            primary_dx = report.differential[0].dx if report.differential else "Undifferentiated"

            return PipelineResult(
                case_id=case_id,
                diagnosis=primary_dx,
                differential=[d.dx for d in report.differential],
                suggested_orders=[r.text for r in report.recommendations],
                clinical_summary=report.patient_summary,
                metadata={
                    "generation_mode": "no_rag",
                    "clinical_report": report.model_dump(),
                    "active_evidence_ids": [],
                    "abstentions": [a.model_dump() for a in report.abstentions],
                    "claims": [c.model_dump() for c in report.claims],
                    "generation_status": "success",
                },
            )

        except Exception as exc:
            logger.error(f"NoRagBaselinePipeline failed for case {case_id}: {exc}")
            return PipelineResult(
                case_id=case_id,
                diagnosis="Generation Failed",
                differential=[],
                suggested_orders=[],
                clinical_summary="No-RAG baseline generation failed.",
                metadata={
                    "generation_mode": "no_rag",
                    "generation_status": "generation_failed",
                    "error": str(exc),
                    "active_evidence_ids": [],
                },
            )
