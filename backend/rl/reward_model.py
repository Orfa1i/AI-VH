"""
Clinical Reward Modeling for Medical AI Policy Evaluation (Phase 6)
Quantifies clinical decision quality, safety compliance, and evidence adherence
into a calibrated scalar reward signal R in [-1.0, 1.0].
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ..clinical.models import (
    PhysicianReview,
    DiagnosisFeedback,
    ReasoningFeedback,
    TestAppropriatenessFeedback,
    TreatmentSafetyFeedback,
)


class ClinicalRewardBreakdown(BaseModel):
    diagnosis_score: float
    reasoning_score: float
    test_score: float
    treatment_score: float
    physician_scale: float
    harrison_citation_bonus: float
    safety_penalty: float
    total_reward: float = Field(ge=-1.0, le=1.0)
    is_safe: bool


class ClinicalRewardModel:
    """
    Evaluates clinical decisions and physician annotations into a calibrated RL reward.
    Rewards adherence to Harrison's Internal Medicine principles and heavily penalizes
    contraindications or missed critical diagnoses.
    """

    DIAGNOSIS_WEIGHTS: Dict[DiagnosisFeedback, float] = {
        DiagnosisFeedback.CORRECT: 0.35,
        DiagnosisFeedback.PARTIALLY_CORRECT: 0.10,
        DiagnosisFeedback.INCORRECT: -0.40,
    }

    REASONING_WEIGHTS: Dict[ReasoningFeedback, float] = {
        ReasoningFeedback.SOUND: 0.25,
        ReasoningFeedback.MISSING_CRITICAL_EVIDENCE: -0.15,
        ReasoningFeedback.FAULTY_LOGIC: -0.25,
        ReasoningFeedback.UNSUPPORTED_CONCLUSION: -0.35,
    }

    TEST_WEIGHTS: Dict[TestAppropriatenessFeedback, float] = {
        TestAppropriatenessFeedback.APPROPRIATE: 0.20,
        TestAppropriatenessFeedback.OVER_ORDERING: -0.10,
        TestAppropriatenessFeedback.MISSING_ESSENTIAL_TEST: -0.25,
        TestAppropriatenessFeedback.INAPPROPRIATE_TEST: -0.30,
    }

    TREATMENT_WEIGHTS: Dict[TreatmentSafetyFeedback, float] = {
        TreatmentSafetyFeedback.SAFE_AND_OPTIMAL: 0.25,
        TreatmentSafetyFeedback.SUBOPTIMAL: -0.15,
        TreatmentSafetyFeedback.CONTRAINDICATED_OR_HARMFUL: -0.65,
    }

    @classmethod
    def compute_reward(
        cls,
        review: PhysicianReview,
        has_harrison_citations: bool = True,
    ) -> ClinicalRewardBreakdown:
        """
        Calculates a multi-dimensional clinical reward breakdown and normalized total score.
        """
        diag_score = cls.DIAGNOSIS_WEIGHTS.get(review.diagnosis_grade, 0.0)
        reason_score = cls.REASONING_WEIGHTS.get(review.reasoning_grade, 0.0)
        test_score = cls.TEST_WEIGHTS.get(review.tests_grade, 0.0)
        treat_score = cls.TREATMENT_WEIGHTS.get(review.treatment_grade, 0.0)

        # Physician Likert scale normalized: 1 -> -0.20, 3 -> 0.0, 5 -> +0.20
        physician_scale = (review.overall_score - 3) * 0.10

        # Harrison's textbook citation fidelity bonus
        citation_bonus = 0.10 if has_harrison_citations and review.approved else 0.0

        # Safety flag
        is_safe = (
            review.treatment_grade != TreatmentSafetyFeedback.CONTRAINDICATED_OR_HARMFUL
            and review.diagnosis_grade != DiagnosisFeedback.INCORRECT
            and review.overall_score >= 2
        )

        safety_penalty = 0.0
        if not is_safe:
            safety_penalty = -0.35

        raw_total = (
            diag_score
            + reason_score
            + test_score
            + treat_score
            + physician_scale
            + citation_bonus
            + safety_penalty
        )

        # Clamp between -1.0 and +1.0
        normalized_reward = max(-1.0, min(1.0, round(raw_total, 3)))

        return ClinicalRewardBreakdown(
            diagnosis_score=round(diag_score, 3),
            reasoning_score=round(reason_score, 3),
            test_score=round(test_score, 3),
            treatment_score=round(treat_score, 3),
            physician_scale=round(physician_scale, 3),
            harrison_citation_bonus=round(citation_bonus, 3),
            safety_penalty=round(safety_penalty, 3),
            total_reward=normalized_reward,
            is_safe=is_safe,
        )
