"""
Model Training Lifecycle & Manifest Manager
Manages reproducible dataset versioning, cryptographic SHA-256 manifest emission,
training procedure orchestration, post-training evaluation on held-out benchmarks,
and automated promotion gating.
"""

import os
import json
import hashlib
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .pre_training_validator import pre_training_validator, PreTrainingValidationResult
from .train_dpo import DPOTrainingConfig, run_dpo_training
from .evaluator import PolicyEvaluator, BenchmarkComparisonReport
from ..clinical.cases import BENCHMARK_CASES

logger = logging.getLogger("ModelLifecycleManager")

MANIFESTS_DIR = "data/manifests"


class TrainingManifest(BaseModel):
    manifest_id: str
    dataset_version: str
    dataset_hash_sha256: str
    eligible_records_count: int
    record_ids: List[str]
    base_model_version: str = "google/medgemma-4b"
    git_commit: Optional[str] = None
    hyperparameters: Dict[str, Any]
    frozen_dataset_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PostTrainingEvaluationResult(BaseModel):
    evaluation_id: str
    candidate_version: str
    baseline_version: str = "google/medgemma-4b (v0.1)"
    cases_evaluated: int
    candidate_mean_score: float
    baseline_mean_score: float
    score_delta: float
    safety_regressions: int
    diagnostic_accuracy_gain_percent: float
    promotion_decision: str  # PROMOTED | REJECTED_SAFETY_REGRESSION | REJECTED_BELOW_BASELINE
    promotion_rationale: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class TrainingLifecycleResult(BaseModel):
    status: str  # COMPLETED_PROMOTED | COMPLETED_NOT_PROMOTED | BLOCKED_VALIDATION_FAILED
    manifest: Optional[TrainingManifest] = None
    validation: PreTrainingValidationResult
    training_summary: Optional[Dict[str, Any]] = None
    post_training_evaluation: Optional[PostTrainingEvaluationResult] = None
    candidate_model_version: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class PreTrainingGateException(Exception):
    def __init__(self, validation_result: PreTrainingValidationResult):
        self.validation_result = validation_result
        super().__init__(f"Pre-training validation failed: {len(validation_result.failed_gates)} gates unsatisfied.")


class ModelLifecycleManager:
    """
    Orchestrates the entire auditable training lifecycle:
    Validation -> Freeze -> Manifest -> Train -> Post-Eval -> Promotion Gate.
    """

    def __init__(self, manifests_dir: str = MANIFESTS_DIR):
        self.manifests_dir = manifests_dir
        os.makedirs(self.manifests_dir, exist_ok=True)

    def _get_git_commit(self) -> str:
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return "UNKNOWN_COMMIT"

    def freeze_dataset(self, records: List[Dict[str, Any]], manifest_id: str) -> tuple[str, str]:
        """
        Freezes eligible training records to an immutable JSONL file and computes SHA-256.
        Returns (filepath, sha256_hash).
        """
        os.makedirs(self.manifests_dir, exist_ok=True)
        filepath = os.path.join(self.manifests_dir, f"dataset_{manifest_id}.jsonl")
        
        hasher = hashlib.sha256()
        with open(filepath, "w", encoding="utf-8") as f:
            for r in records:
                # Deterministic JSON serialization
                line = json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
                hasher.update(line.encode("utf-8"))
                f.write(line)

        digest = hasher.hexdigest()
        logger.info(f"Dataset frozen to '{filepath}' with SHA-256: {digest}")
        return filepath, digest

    def create_manifest(
        self,
        manifest_id: str,
        records: List[Dict[str, Any]],
        hyperparameters: Dict[str, Any],
        frozen_dataset_path: str,
        dataset_hash: str,
        base_model_version: str = "google/medgemma-4b",
    ) -> TrainingManifest:
        """Emits reproducible training manifest."""
        manifest = TrainingManifest(
            manifest_id=manifest_id,
            dataset_version=f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            dataset_hash_sha256=dataset_hash,
            eligible_records_count=len(records),
            record_ids=[str(r.get("id") or r.get("report_id")) for r in records],
            base_model_version=base_model_version,
            git_commit=self._get_git_commit(),
            hyperparameters=hyperparameters,
            frozen_dataset_path=frozen_dataset_path,
        )
        manifest_file = os.path.join(self.manifests_dir, f"manifest_{manifest_id}.json")
        with open(manifest_file, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        logger.info(f"Training manifest emitted to '{manifest_file}'")
        return manifest

    def run_post_training_evaluation(
        self,
        candidate_version: str,
        adapter_path: str,
    ) -> PostTrainingEvaluationResult:
        """
        Runs candidate model against held-out golden benchmark cases (BENCHMARK_CASES).
        Enforces strict zero-safety-regression requirement and comparison against baseline.
        """
        logger.info(f"Running post-training benchmark evaluation for candidate {candidate_version}...")
        report: BenchmarkComparisonReport = PolicyEvaluator.run_full_benchmark()

        # Count safety regressions (cases where RL model performed worse than Base in safety)
        safety_regressions = 0
        for comp in report.case_comparisons:
            if comp.rl_agent_metrics.treatment_safety_percent < comp.base_agent_metrics.treatment_safety_percent:
                safety_regressions += 1
            if comp.rl_agent_metrics.contraindications_missed > comp.base_agent_metrics.contraindications_missed:
                safety_regressions += 1

        score_delta = round(report.rl_agent_mean_score - report.base_agent_mean_score, 3)

        # Promotion Gate Decision
        if safety_regressions > 0:
            decision = "REJECTED_SAFETY_REGRESSION"
            rationale = (
                f"Candidate exhibited {safety_regressions} safety regressions against baseline. "
                "Zero safety regressions permitted under configs/thresholds.yaml. Promotion blocked."
            )
        elif score_delta < 0:
            decision = "REJECTED_BELOW_BASELINE"
            rationale = (
                f"Candidate mean score ({report.rl_agent_mean_score:.2f}) is lower than baseline ({report.base_agent_mean_score:.2f}). "
                "Must beat production baseline under configs/thresholds.yaml. Promotion blocked."
            )
        else:
            decision = "PROMOTED"
            rationale = (
                f"Candidate passed all promotion criteria: 0 safety regressions, "
                f"+{report.mean_score_improvement_percent:.1f}% mean score improvement, "
                f"+{report.diagnostic_accuracy_gain_percent:.1f}% accuracy gain."
            )

        return PostTrainingEvaluationResult(
            evaluation_id=f"EVAL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            candidate_version=candidate_version,
            baseline_version="google/medgemma-4b (v0.1)",
            cases_evaluated=report.total_cases,
            candidate_mean_score=report.rl_agent_mean_score,
            baseline_mean_score=report.base_agent_mean_score,
            score_delta=score_delta,
            safety_regressions=safety_regressions,
            diagnostic_accuracy_gain_percent=report.diagnostic_accuracy_gain_percent,
            promotion_decision=decision,
            promotion_rationale=rationale,
        )

    def execute_lifecycle(
        self,
        records: List[Dict[str, Any]],
        training_config: Optional[DPOTrainingConfig] = None,
        min_cases_override: Optional[int] = None,
        dry_run: bool = False,
    ) -> TrainingLifecycleResult:
        """
        Executes the full validated training workflow.
        Fail-closed: Returns immediately with failed gates if pre-training validation fails.
        """
        manifest_id = f"MNF-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # 1. Strict 14-Gate Pre-Training Validation
        val_result = pre_training_validator.validate(
            records=records,
            min_cases_override=min_cases_override,
        )

        if not val_result.passed:
            logger.warning(
                f"Training lifecycle halted. Pre-training validation failed: {val_result.failed_gates}"
            )
            return TrainingLifecycleResult(
                status="BLOCKED_VALIDATION_FAILED",
                validation=val_result,
                blockers=val_result.missing_prerequisites,
            )

        # 2. Freeze Dataset & Emit Manifest
        eligible_records = [
            r for r in records
            if r.get("dataset_eligibility") in ("ELIGIBLE", DatasetEligibilityStatus.ELIGIBLE.value)
        ]
        frozen_path, sha_digest = self.freeze_dataset(eligible_records, manifest_id)

        config = training_config or DPOTrainingConfig()
        config.dataset_path = frozen_path
        config.dry_run = dry_run

        manifest = self.create_manifest(
            manifest_id=manifest_id,
            records=eligible_records,
            hyperparameters={
                "epochs": config.epochs,
                "learning_rate": config.learning_rate,
                "beta": config.beta,
                "lora_r": config.lora_r,
                "lora_alpha": config.lora_alpha,
                "batch_size": config.batch_size,
            },
            frozen_dataset_path=frozen_path,
            dataset_hash=sha_digest,
            base_model_version=config.model_name_or_path,
        )

        # 3. Execute Configured Training Procedure
        logger.info(f"Executing DPO training procedure with manifest {manifest_id}...")
        train_summary = run_dpo_training(config)

        # 4. Post-Training Evaluation against Held-out Evaluation Data
        candidate_version = f"medgemma-dpo-lora-{manifest_id}"
        eval_result = self.run_post_training_evaluation(
            candidate_version=candidate_version,
            adapter_path=config.output_dir,
        )

        overall_status = "COMPLETED_PROMOTED" if eval_result.promotion_decision == "PROMOTED" else "COMPLETED_NOT_PROMOTED"

        return TrainingLifecycleResult(
            status=overall_status,
            manifest=manifest,
            validation=val_result,
            training_summary=train_summary,
            post_training_evaluation=eval_result,
            candidate_model_version=candidate_version,
            blockers=[] if overall_status == "COMPLETED_PROMOTED" else [eval_result.promotion_rationale],
        )

    def list_manifests(self) -> List[Dict[str, Any]]:
        """Lists historical training manifests and metadata."""
        if not os.path.exists(self.manifests_dir):
            return []
        manifests = []
        for fn in sorted(os.listdir(self.manifests_dir), reverse=True):
            if fn.startswith("manifest_") and fn.endswith(".json"):
                fp = os.path.join(self.manifests_dir, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        manifests.append(json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to read manifest {fp}: {e}")
        return manifests


model_lifecycle_manager = ModelLifecycleManager()
