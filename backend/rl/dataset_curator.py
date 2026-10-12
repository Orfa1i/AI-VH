"""
AI Virtual Hospital - Training Dataset Curator
Processes physician and student reviews into immutable, provenance-linked,
deduplicated training dataset records preserving all 13 lifecycle fields.
Guarantees zero automatic training triggers.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..clinical.models import (
    ClinicalReport,
    PhysicianReview,
    TrainingDatasetRecord,
    ReviewAssessment,
    ReviewErrorTaxonomy,
    DatasetEligibilityStatus,
)
from ..clinical.cases import PatientGroundTruth
from ..llm.model_config import get_model_id
from ..database.repository import db_repo, DatabaseRepository

logger = logging.getLogger("DatasetCurator")


class DatasetCurator:
    """
    Curates human review data into production training datasets.
    Enforces deduplication by patient/case, completeness validation,
    provenance tracking, and strict distinction between human review
    and automated review data.
    """

    def __init__(self, repository: Optional[DatabaseRepository] = None):
        self.repo = repository or db_repo

    def evaluate_eligibility(
        self,
        report: ClinicalReport,
        review: PhysicianReview,
        is_duplicate: bool = False,
    ) -> DatasetEligibilityStatus:
        """
        Evaluates training dataset eligibility based on completeness,
        deduplication, and clinical grounding.
        """
        # 1. Duplicate check: prevent duplicate patient cases from artificially inflating training counts
        if is_duplicate:
            return DatasetEligibilityStatus.INELIGIBLE_DUPLICATE

        # 2. Ungrounded AI report check: if report was ungrounded and no human corrections provided
        if getattr(report, "ungrounded", False):
            has_human_correction = bool(
                review.corrected_diagnosis
                or review.corrected_reasoning
                or review.corrected_treatment
                or review.corrected_recommendations
            )
            if not has_human_correction:
                return DatasetEligibilityStatus.INELIGIBLE_UNGROUNDED

        # 3. Completeness check:
        # If the reviewer marked the report INCORRECT or PARTIALLY_CORRECT,
        # there must be a corrected diagnosis, reasoning, recommendations, or substantive feedback
        if review.assessment in [ReviewAssessment.INCORRECT, ReviewAssessment.PARTIALLY_CORRECT]:
            has_actionable_correction = bool(
                (review.corrected_diagnosis and len(review.corrected_diagnosis.strip()) >= 3)
                or (review.corrected_reasoning and len(review.corrected_reasoning.strip()) >= 5)
                or (review.corrected_treatment and len(review.corrected_treatment) > 0)
                or (review.corrected_recommendations and len(review.corrected_recommendations) > 0)
                or (review.physician_feedback_notes and len(review.physician_feedback_notes.strip()) >= 15)
            )
            if not has_actionable_correction:
                return DatasetEligibilityStatus.INELIGIBLE_INCOMPLETE

        return DatasetEligibilityStatus.ELIGIBLE

    def build_training_record(
        self,
        report: ClinicalReport,
        review: PhysicianReview,
        case: Optional[PatientGroundTruth] = None,
        is_duplicate: bool = False,
    ) -> TrainingDatasetRecord:
        """
        Builds a TrainingDatasetRecord preserving all 13 required fields:
        1. case_id
        2. patient_id
        3. report_id
        4. model_version
        5. specialty
        6. original_input
        7. original_ai_output
        8. reviewer_feedback
        9. corrected_output / preferred_output
        10. provenance
        11. review_status
        12. dataset_eligibility
        13. timestamp
        """
        case_id = getattr(report, "case_id", getattr(case, "id", getattr(report, "patient_id", "CASE-UNKNOWN")))
        patient_id = getattr(report, "patient_id", getattr(case, "id", "PAT-UNKNOWN"))
        report_id = report.id
        model_version = get_model_id()
        specialty = getattr(review, "specialty", getattr(report, "specialty", "INTERNAL_MEDICINE"))

        # 6. Original Input: reconstruct clinical presentation presented to the model
        original_input = {
            "case_id": case_id,
            "patient_id": patient_id,
            "age": getattr(case, "age", getattr(report, "patient_age", None)),
            "sex": getattr(case, "sex", getattr(report, "patient_sex", None)),
            "chief_complaint": getattr(case, "chief_complaint", getattr(report, "chief_complaint", "")),
            "history_of_present_illness": getattr(case, "history_of_present_illness", getattr(report, "history_of_present_illness", "")),
            "past_medical_history": getattr(case, "past_medical_history", getattr(report, "past_medical_history", [])),
            "medications": getattr(case, "medications", getattr(report, "medications", [])),
            "allergies": getattr(case, "allergies", getattr(report, "allergies", [])),
            "investigations_ordered": getattr(report, "investigations_ordered", []),
            "investigation_results": getattr(report, "investigation_results", []),
        }

        # 7. Original AI Output: preserved unchanged
        original_ai_output = report.model_dump() if hasattr(report, "model_dump") else dict(report)

        # 8. Reviewer Feedback: structured errors and evaluations
        assessment_val = review.assessment.value if hasattr(review.assessment, "value") else str(review.assessment)
        error_tags = [
            e.value if hasattr(e, "value") else str(e)
            for e in getattr(review, "identified_errors", [])
        ]
        reviewer_feedback = {
            "review_id": review.id,
            "reviewer_name": review.physician_name,
            "reviewer_role": getattr(review, "reviewer_role", "ATTENDING_PHYSICIAN"),
            "reviewed_at": review.reviewed_at.isoformat() if hasattr(review.reviewed_at, "isoformat") else str(review.reviewed_at),
            "assessment": assessment_val,
            "identified_errors": error_tags,
            "diagnosis_grade": getattr(review.diagnosis_grade, "value", str(review.diagnosis_grade)),
            "reasoning_grade": getattr(review.reasoning_grade, "value", str(review.reasoning_grade)),
            "tests_grade": getattr(review.tests_grade, "value", str(review.tests_grade)),
            "treatment_grade": getattr(review.treatment_grade, "value", str(review.treatment_grade)),
            "overall_score": review.overall_score,
            "approved": review.approved,
            "notes": review.physician_feedback_notes,
        }

        # 9. Corrected Output / Preferred Output: human-refined clinical solution
        has_corrections = bool(
            review.corrected_diagnosis
            or review.corrected_reasoning
            or review.corrected_treatment
            or review.corrected_recommendations
        )
        corrected_output = {
            "primary_diagnosis": review.corrected_diagnosis or report.primary_diagnosis,
            "clinical_reasoning": review.corrected_reasoning or report.clinical_reasoning,
            "treatment_plan": review.corrected_treatment or review.corrected_recommendations or report.treatment_plan,
            "recommended_next_steps": review.corrected_recommendations or report.recommended_next_steps,
            "corrections_applied": has_corrections,
            "preferred_basis": "PHYSICIAN_CORRECTION" if has_corrections else "APPROVED_AI_OUTPUT",
        }

        # 10. Provenance: complete audit metadata
        provenance = {
            "source_type": "HUMAN_CLINICAL_REVIEW",
            "evaluator_type": "HUMAN_EXPERT",
            "model_provenance": model_version,
            "review_id": review.id,
            "encounter_id": report.encounter_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        # 11. Review Status
        if review.approved and review.overall_score >= 4 and not has_corrections:
            review_status = "APPROVED"
        elif has_corrections:
            review_status = "CORRECTED"
        else:
            review_status = "REJECTED"

        # 12. Dataset Eligibility
        eligibility = self.evaluate_eligibility(report, review, is_duplicate=is_duplicate)

        return TrainingDatasetRecord(
            id=f"TDR-{uuid.uuid4().hex[:8].upper()}",
            case_id=case_id,
            patient_id=patient_id,
            report_id=report_id,
            model_version=model_version,
            specialty=specialty,
            original_input=original_input,
            original_ai_output=original_ai_output,
            reviewer_feedback=reviewer_feedback,
            corrected_output=corrected_output,
            provenance=provenance,
            review_status=review_status,
            dataset_eligibility=eligibility,
            timestamp=datetime.now(timezone.utc),
        )

    def process_review_submission(
        self,
        report: ClinicalReport,
        review: PhysicianReview,
        case: Optional[PatientGroundTruth] = None,
    ) -> TrainingDatasetRecord:
        """
        Processes submitted review, checks for duplicate patient/case entries,
        persists the curated TrainingDatasetRecord, and returns it.
        Guarantees that no model training is triggered.
        """
        # Check if this patient/case has already been processed with an ELIGIBLE review
        patient_id = getattr(report, "patient_id", getattr(case, "id", "PAT-UNKNOWN"))
        case_id = getattr(report, "case_id", getattr(case, "id", patient_id))
        is_duplicate = self.repo.is_patient_case_reviewed(patient_id=patient_id, case_id=case_id)

        record = self.build_training_record(
            report=report,
            review=review,
            case=case,
            is_duplicate=is_duplicate,
        )

        self.repo.save_training_dataset_record(record)
        logger.info(
            f"Curated training record {record.id} for case={case_id}, patient={patient_id}. "
            f"Eligibility: {record.dataset_eligibility.value} (is_duplicate={is_duplicate}). "
            f"Zero automatic training triggered."
        )
        return record


# Global singleton curator
dataset_curator = DatasetCurator()
