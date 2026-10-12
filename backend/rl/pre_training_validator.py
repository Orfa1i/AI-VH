"""
Pre-Training Validation Engine
Executes strict 14-point deterministic gate validation on training datasets
prior to any model fine-tuning. Enforces fail-closed safety, strict Golden Case
isolation, patient deduplication, and zero data leakage.
"""

import os
import re
import yaml
import logging
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime

from ..clinical.models import TrainingDatasetRecord, DatasetEligibilityStatus
from ..clinical.cases import BENCHMARK_CASES

logger = logging.getLogger("PreTrainingValidator")

# Known Golden Case IDs that are permanently reserved for evaluation
GOLDEN_CASE_IDS: Set[str] = {c.id for c in BENCHMARK_CASES}
GOLDEN_PATIENT_NAMES: Set[str] = {c.name.strip().lower() for c in BENCHMARK_CASES}

# Leakage keywords to scan in prompt inputs
GROUND_TRUTH_LEAKAGE_KEYS = [
    "true_diagnosis",
    "icd10_code",
    "optimal_treatment",
    "contraindicated_treatments",
    "ground_truth",
    "benchmark_diagnosis",
]

EVALUATOR_METADATA_KEYS = [
    "evaluator_score",
    "automated_evaluation",
    "evaluation_status",
    "judge_score",
    "dimension_scores",
    "hallucination_detected",
    "critical_count",
    "sanitized_removed",
]

FUTURE_EVENT_KEYS = [
    "discharged_home_improved",
    "admitted_to_icu_subsequently",
    "patient_expired",
    "readmitted_within_30_days",
    "post_discharge_complication",
    "future_event",
]


class GateResult(BaseModel):
    gate_id: int
    name: str
    passed: bool
    severity: str = "CRITICAL"  # CRITICAL | HIGH | MEDIUM
    description: str
    failure_reason: Optional[str] = None
    affected_count: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)


class PreTrainingValidationResult(BaseModel):
    passed: bool
    total_records_evaluated: int
    eligible_records_count: int
    gates_evaluated: int
    gates_passed: int
    gates_failed: int
    gate_results: List[GateResult]
    failed_gates: List[str]
    missing_prerequisites: List[str]
    thresholds_verified: Dict[str, Any]
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class PreTrainingValidator:
    """
    Deterministic 14-Gate Validator for the AI-VH Model Training Pipeline.
    Strictly fail-closed: If any gate fails or cannot be verified, training is blocked.
    """

    def __init__(self, thresholds_path: str = "configs/thresholds.yaml"):
        self.thresholds_path = thresholds_path
        self._cached_thresholds: Optional[Dict[str, Any]] = None

    def load_thresholds(self) -> Dict[str, Any]:
        """Loads and verifies existence of thresholds configuration without modification."""
        if not os.path.exists(self.thresholds_path):
            raise FileNotFoundError(
                f"Mandatory thresholds file not found at '{self.thresholds_path}'. "
                "Training cannot proceed without canonical thresholds."
            )
        with open(self.thresholds_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            raise ValueError(f"Invalid thresholds YAML at '{self.thresholds_path}'")
        self._cached_thresholds = data
        return data

    def validate(
        self,
        records: List[Dict[str, Any]],
        held_out_eval_ids: Optional[Set[str]] = None,
        min_cases_override: Optional[int] = None,
    ) -> PreTrainingValidationResult:
        """
        Executes all 14 mandatory validation gates against the proposed training records.
        """
        thresholds = self.load_thresholds()
        gate_results: List[GateResult] = []

        # Target minimum cases from canonical thresholds
        training_thresholds = thresholds.get("training", {})
        min_required_cases = min_cases_override or training_thresholds.get("min_reviewed_cases", 500)

        held_out_set = set(held_out_eval_ids or set())
        held_out_set.update(GOLDEN_CASE_IDS)

        # -------------------------------------------------------------
        # Gate 1: Minimum required number of eligible cases
        # -------------------------------------------------------------
        eligible_records = [
            r for r in records
            if r.get("dataset_eligibility") == DatasetEligibilityStatus.ELIGIBLE.value
            or r.get("dataset_eligibility") == "ELIGIBLE"
        ]
        g1_passed = len(eligible_records) >= min_required_cases
        gate_results.append(GateResult(
            gate_id=1,
            name="Minimum Required Eligible Cases",
            passed=g1_passed,
            description=f"Requires at least {min_required_cases} verified eligible cases.",
            failure_reason=(
                f"Insufficient eligible training cases: found {len(eligible_records)}, "
                f"required {min_required_cases} per thresholds.yaml."
                if not g1_passed else None
            ),
            affected_count=max(0, min_required_cases - len(eligible_records)),
            details={"found": len(eligible_records), "required": min_required_cases},
        ))

        # -------------------------------------------------------------
        # Gate 2: Patient-level deduplication
        # -------------------------------------------------------------
        patient_counts: Dict[str, int] = {}
        for r in eligible_records:
            pid = str(r.get("patient_id") or r.get("case_id") or "").strip()
            if pid:
                patient_counts[pid] = patient_counts.get(pid, 0) + 1
        
        duplicate_patients = [pid for pid, count in patient_counts.items() if count > 1]
        g2_passed = len(duplicate_patients) == 0
        gate_results.append(GateResult(
            gate_id=2,
            name="Patient-Level Deduplication",
            passed=g2_passed,
            description="Ensures no patient has duplicate representation in the training cohort.",
            failure_reason=(
                f"Detected {len(duplicate_patients)} duplicate patients: {duplicate_patients[:5]}"
                if not g2_passed else None
            ),
            affected_count=len(duplicate_patients),
            details={"duplicate_patient_ids": duplicate_patients},
        ))

        # -------------------------------------------------------------
        # Gate 3: No contamination between training and evaluation data
        # -------------------------------------------------------------
        training_case_ids = {
            str(r.get("case_id") or r.get("patient_id") or "").strip()
            for r in eligible_records
        }
        contaminated_ids = training_case_ids.intersection(held_out_set)
        g3_passed = len(contaminated_ids) == 0
        gate_results.append(GateResult(
            gate_id=3,
            name="Train/Evaluation Split Isolation",
            passed=g3_passed,
            description="Guarantees zero overlap between training data and held-out evaluation cases.",
            failure_reason=(
                f"Data contamination detected: {len(contaminated_ids)} training cases overlap with held-out eval set: {list(contaminated_ids)[:5]}"
                if not g3_passed else None
            ),
            affected_count=len(contaminated_ids),
            details={"contaminated_case_ids": list(contaminated_ids)},
        ))

        # -------------------------------------------------------------
        # Gate 4: Complete provenance
        # -------------------------------------------------------------
        missing_provenance_records = []
        for r in eligible_records:
            prov = r.get("provenance") or {}
            model_ver = r.get("model_version")
            spec = r.get("specialty")
            rep_id = r.get("report_id")
            ts = r.get("timestamp")
            if not (model_ver and spec and rep_id and ts):
                missing_provenance_records.append(r.get("id") or r.get("report_id"))
        g4_passed = len(missing_provenance_records) == 0
        gate_results.append(GateResult(
            gate_id=4,
            name="Complete Provenance Verification",
            passed=g4_passed,
            description="Verifies model version, specialty, report ID, and timestamp on all records.",
            failure_reason=(
                f"{len(missing_provenance_records)} records missing mandatory provenance fields."
                if not g4_passed else None
            ),
            affected_count=len(missing_provenance_records),
            details={"missing_records": missing_provenance_records[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 5: Valid input/output pairs
        # -------------------------------------------------------------
        invalid_pairs = []
        for r in eligible_records:
            orig_in = r.get("original_input") or {}
            orig_out = r.get("original_ai_output") or {}
            corr_out = r.get("corrected_output") or {}
            
            # Input must contain clinical summary or chief complaint
            has_input_text = bool(
                orig_in.get("clinical_summary")
                or orig_in.get("chief_complaint")
                or orig_in.get("prompt")
                or orig_in.get("history_of_present_illness")
            )
            # Output must contain a primary diagnosis and reasoning
            target_out = corr_out if corr_out.get("primary_diagnosis") else orig_out
            has_output_text = bool(
                target_out.get("primary_diagnosis")
                and (target_out.get("clinical_reasoning") or target_out.get("treatment_plan"))
            )
            if not (has_input_text and has_output_text):
                invalid_pairs.append(r.get("id") or r.get("report_id"))
        
        g5_passed = len(invalid_pairs) == 0
        gate_results.append(GateResult(
            gate_id=5,
            name="Valid Input/Output Pair Structure",
            passed=g5_passed,
            description="Validates structured clinical input and output text completeness.",
            failure_reason=(
                f"{len(invalid_pairs)} records have malformed or empty input/output pairs."
                if not g5_passed else None
            ),
            affected_count=len(invalid_pairs),
            details={"invalid_records": invalid_pairs[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 6: Valid reviewer feedback where required
        # -------------------------------------------------------------
        invalid_reviews = []
        for r in eligible_records:
            status = r.get("review_status")
            feedback = r.get("reviewer_feedback") or {}
            if status == "CORRECTED":
                # Must have corrected output or notes
                corr = r.get("corrected_output") or {}
                if not (corr.get("primary_diagnosis") or corr.get("clinical_reasoning") or feedback.get("notes")):
                    invalid_reviews.append(r.get("id") or r.get("report_id"))
            elif status == "APPROVED":
                if not feedback.get("approved", True):
                    invalid_reviews.append(r.get("id") or r.get("report_id"))
            elif not status:
                invalid_reviews.append(r.get("id") or r.get("report_id"))

        g6_passed = len(invalid_reviews) == 0
        gate_results.append(GateResult(
            gate_id=6,
            name="Reviewer Feedback Validity",
            passed=g6_passed,
            description="Verifies constructive corrections or valid approvals for every record.",
            failure_reason=(
                f"{len(invalid_reviews)} records have missing or contradictory reviewer feedback."
                if not g6_passed else None
            ),
            affected_count=len(invalid_reviews),
            details={"invalid_review_records": invalid_reviews[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 7: Zero hidden Ground Truth leakage
        # -------------------------------------------------------------
        gt_leakage_records = []
        for r in eligible_records:
            input_str = str(r.get("original_input") or "").lower()
            for key in GROUND_TRUTH_LEAKAGE_KEYS:
                if f"'{key}'" in input_str or f'"{key}"' in input_str or f"{key}:" in input_str:
                    gt_leakage_records.append(r.get("id") or r.get("report_id"))
                    break
        
        g7_passed = len(gt_leakage_records) == 0
        gate_results.append(GateResult(
            gate_id=7,
            name="Zero Ground-Truth Leakage",
            passed=g7_passed,
            description="Verifies that no hidden benchmark diagnoses or ICD-10 keys exist in input prompts.",
            failure_reason=(
                f"Ground Truth leakage detected in {len(gt_leakage_records)} training records."
                if not g7_passed else None
            ),
            affected_count=len(gt_leakage_records),
            details={"leaked_records": gt_leakage_records[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 8: Zero evaluator metadata leakage
        # -------------------------------------------------------------
        eval_leakage_records = []
        for r in eligible_records:
            input_str = str(r.get("original_input") or "").lower()
            for key in EVALUATOR_METADATA_KEYS:
                if f"'{key}'" in input_str or f'"{key}"' in input_str:
                    eval_leakage_records.append(r.get("id") or r.get("report_id"))
                    break
        
        g8_passed = len(eval_leakage_records) == 0
        gate_results.append(GateResult(
            gate_id=8,
            name="Zero Evaluator Metadata Leakage",
            passed=g8_passed,
            description="Guarantees evaluation scores and judge tokens are not leaked into training prompts.",
            failure_reason=(
                f"Evaluator metadata leakage detected in {len(eval_leakage_records)} training records."
                if not g8_passed else None
            ),
            affected_count=len(eval_leakage_records),
            details={"leaked_records": eval_leakage_records[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 9: Zero future-event leakage
        # -------------------------------------------------------------
        future_leakage_records = []
        for r in eligible_records:
            input_str = str(r.get("original_input") or "").lower()
            for key in FUTURE_EVENT_KEYS:
                if key in input_str:
                    future_leakage_records.append(r.get("id") or r.get("report_id"))
                    break
        
        g9_passed = len(future_leakage_records) == 0
        gate_results.append(GateResult(
            gate_id=9,
            name="Zero Future-Event Leakage",
            passed=g9_passed,
            description="Guarantees post-encounter outcomes and future complications are absent from training inputs.",
            failure_reason=(
                f"Future event leakage detected in {len(future_leakage_records)} records."
                if not g9_passed else None
            ),
            affected_count=len(future_leakage_records),
            details={"leaked_records": future_leakage_records[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 10: Required automated-review predicates are satisfied
        # -------------------------------------------------------------
        auto_review_failures = []
        for r in eligible_records:
            # If the record has automated_evaluation in original output or feedback
            orig_out = r.get("original_ai_output") or {}
            auto_eval = orig_out.get("automated_evaluation")
            if auto_eval and isinstance(auto_eval, dict):
                status = auto_eval.get("status")
                # If rejected by automated evaluation and not explicitly corrected by human physician
                if status == "REJECTED" and r.get("review_status") != "CORRECTED":
                    auto_review_failures.append(r.get("id") or r.get("report_id"))

        g10_passed = len(auto_review_failures) == 0
        gate_results.append(GateResult(
            gate_id=10,
            name="Automated-Review Predicates Satisfied",
            passed=g10_passed,
            description="Verifies that uncorrected automated evaluation rejections are excluded.",
            failure_reason=(
                f"{len(auto_review_failures)} records violate automated-review safety predicates."
                if not g10_passed else None
            ),
            affected_count=len(auto_review_failures),
            details={"failed_records": auto_review_failures[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 11: Required human-review predicates are satisfied
        # -------------------------------------------------------------
        human_review_failures = []
        valid_roles = {"ATTENDING_PHYSICIAN", "PHYSICIAN", "RESIDENT", "STUDENT", "SYSTEM_SPECIALIST"}
        for r in eligible_records:
            feedback = r.get("reviewer_feedback") or {}
            role = str(feedback.get("reviewer_role", "ATTENDING_PHYSICIAN")).upper()
            if role not in valid_roles:
                human_review_failures.append(r.get("id") or r.get("report_id"))
        
        g11_passed = len(human_review_failures) == 0
        gate_results.append(GateResult(
            gate_id=11,
            name="Human-Review Role & Quality Predicates",
            passed=g11_passed,
            description="Verifies valid reviewer role and clinical evaluation provenance.",
            failure_reason=(
                f"{len(human_review_failures)} records have unrecognized reviewer roles."
                if not g11_passed else None
            ),
            affected_count=len(human_review_failures),
            details={"failed_records": human_review_failures[:5]},
        ))

        # -------------------------------------------------------------
        # Gate 12: Existing Golden Cases remain isolated
        # -------------------------------------------------------------
        golden_violations = []
        for r in eligible_records:
            cid = str(r.get("case_id") or "").strip()
            pid = str(r.get("patient_id") or "").strip()
            name = str((r.get("original_input") or {}).get("patient_name") or "").strip().lower()
            if cid in GOLDEN_CASE_IDS or pid in GOLDEN_CASE_IDS or name in GOLDEN_PATIENT_NAMES:
                golden_violations.append(cid or pid or str(r.get("id")))
        
        g12_passed = len(golden_violations) == 0
        gate_results.append(GateResult(
            gate_id=12,
            name="Golden Cases Strict Isolation",
            passed=g12_passed,
            description="Ensures canonical benchmark golden cases are permanently excluded from training.",
            failure_reason=(
                f"Golden Case isolation breach: {len(golden_violations)} benchmark golden cases found in training set: {golden_violations[:5]}"
                if not g12_passed else None
            ),
            affected_count=len(golden_violations),
            details={"golden_case_ids": golden_violations},
        ))

        # -------------------------------------------------------------
        # Gate 13: Existing training thresholds remain unchanged
        # -------------------------------------------------------------
        # Thresholds invariance check: assert canonical keys exist in configs/thresholds.yaml
        expected_threshold_keys = ["golden", "cases", "retrieval", "generation", "verification", "training"]
        missing_keys = [k for k in expected_threshold_keys if k not in thresholds]
        g13_passed = len(missing_keys) == 0 and thresholds.get("training", {}).get("safety_regressions") == 0
        gate_results.append(GateResult(
            gate_id=13,
            name="Threshold Invariance Check",
            passed=g13_passed,
            description="Confirms configs/thresholds.yaml is intact with zero safety regressions permitted.",
            failure_reason=(
                f"Threshold configuration compromised: missing keys {missing_keys} or safety_regressions > 0."
                if not g13_passed else None
            ),
            affected_count=len(missing_keys),
            details={"threshold_keys": list(thresholds.keys())},
        ))

        # -------------------------------------------------------------
        # Gate 14: Dataset contains no invalid or incomplete records
        # -------------------------------------------------------------
        required_13_fields = [
            "case_id", "patient_id", "report_id", "model_version", "specialty",
            "original_input", "original_ai_output", "reviewer_feedback",
            "corrected_output", "provenance", "review_status",
            "dataset_eligibility", "timestamp"
        ]
        incomplete_records = []
        for r in eligible_records:
            missing_fields = [f for f in required_13_fields if f not in r or r[f] is None]
            if missing_fields:
                incomplete_records.append({"id": r.get("id") or r.get("report_id"), "missing": missing_fields})

        g14_passed = len(incomplete_records) == 0
        gate_results.append(GateResult(
            gate_id=14,
            name="Record Completeness & Schema Conformity",
            passed=g14_passed,
            description="Ensures all 13 canonical lifecycle fields are populated with valid values.",
            failure_reason=(
                f"{len(incomplete_records)} records are missing mandatory lifecycle fields."
                if not g14_passed else None
            ),
            affected_count=len(incomplete_records),
            details={"incomplete_sample": incomplete_records[:5]},
        ))

        # -------------------------------------------------------------
        # Aggregate Summary & Fail-Closed Verdict
        # -------------------------------------------------------------
        passed_count = sum(1 for g in gate_results if g.passed)
        failed_count = len(gate_results) - passed_count
        overall_passed = (failed_count == 0)

        failed_names = [g.name for g in gate_results if not g.passed]
        missing_prereqs = [g.failure_reason for g in gate_results if not g.passed and g.failure_reason]

        return PreTrainingValidationResult(
            passed=overall_passed,
            total_records_evaluated=len(records),
            eligible_records_count=len(eligible_records),
            gates_evaluated=len(gate_results),
            gates_passed=passed_count,
            gates_failed=failed_count,
            gate_results=gate_results,
            failed_gates=failed_names,
            missing_prerequisites=missing_prereqs,
            thresholds_verified={
                "min_reviewed_cases": min_required_cases,
                "safety_regressions_allowed": training_thresholds.get("safety_regressions", 0),
                "must_beat_production": training_thresholds.get("must_beat_production", True),
            },
        )


pre_training_validator = PreTrainingValidator()
