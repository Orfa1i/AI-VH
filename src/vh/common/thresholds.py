"""
Thresholds configuration loader for the AI Virtual Hospital platform.
Loads configs/thresholds.yaml, enforces mandatory keys, and treats null as NOT SET.
Any evaluation gate relying on a NOT SET threshold fails automatically.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from pydantic import BaseModel, Field


class ThresholdStatus(str, Enum):
    SET = "SET"
    NOT_SET = "NOT_SET"


class MissingThresholdError(KeyError):
    """Raised when a required threshold key or section is absent."""
    pass


class ThresholdNotSetError(ValueError):
    """Raised when an operation requires an explicit threshold value but it is null/NOT SET."""
    pass


class GoldenThresholds(BaseModel):
    min_verified_cases: int


class CasesThresholds(BaseModel):
    fhir_valid_rate: float
    leakage_count: int
    plausibility_pass_rate: float
    spotcheck_defect_rate_max: float


class RetrievalThresholds(BaseModel):
    recall_at_10: float
    mrr_min: float
    traceability_rate: float
    stale_retrieval_count: int
    p95_latency_s: float


class GenerationThresholds(BaseModel):
    schema_valid_rate: float
    fabricated_citation_rate: float
    abstention_correct_rate: float
    dx_top3_min: Optional[float] = None
    rag_beats_baseline: bool


class VerificationThresholds(BaseModel):
    critical_fault_detection: float
    noncritical_fault_detection: float
    false_flag_rate_max: float
    judge_kappa_min: float
    faithfulness_min: float
    contextual_relevancy_min: float
    p95_latency_s: float


class AgentsThresholds(BaseModel):
    permission_violations: int
    runaway_loops: int
    replay_mismatch_count: int
    encounter_score_min: Optional[float] = None


class ReviewThresholds(BaseModel):
    kappa_min: float
    overlap_fraction: float


class TrainingThresholds(BaseModel):
    min_reviewed_cases: int
    safety_regressions: int
    must_beat_production: bool
    # Updated STEP-02/53: owner sets this before STEP 53; null means BLOCKED.
    min_preference_pairs: Optional[int] = None


class UIThresholds(BaseModel):
    min_fps: int
    max_load_s: int
    max_sync_lag_ms: int
    output_divergence_count: int


class ThresholdsConfig(BaseModel):
    golden: GoldenThresholds
    cases: CasesThresholds
    retrieval: RetrievalThresholds
    generation: GenerationThresholds
    verification: VerificationThresholds
    agents: AgentsThresholds
    review: ReviewThresholds
    training: TrainingThresholds
    ui: UIThresholds


REQUIRED_SECTIONS = {
    "golden", "cases", "retrieval", "generation",
    "verification", "agents", "review", "training", "ui"
}

REQUIRED_KEYS: Dict[str, set[str]] = {
    "golden": {"min_verified_cases"},
    "cases": {"fhir_valid_rate", "leakage_count", "plausibility_pass_rate", "spotcheck_defect_rate_max"},
    "retrieval": {"recall_at_10", "mrr_min", "traceability_rate", "stale_retrieval_count", "p95_latency_s"},
    "generation": {"schema_valid_rate", "fabricated_citation_rate", "abstention_correct_rate", "dx_top3_min", "rag_beats_baseline"},
    "verification": {"critical_fault_detection", "noncritical_fault_detection", "false_flag_rate_max", "judge_kappa_min", "faithfulness_min", "contextual_relevancy_min", "p95_latency_s"},
    "agents": {"permission_violations", "runaway_loops", "replay_mismatch_count", "encounter_score_min"},
    "review": {"kappa_min", "overlap_fraction"},
    "training": {"min_reviewed_cases", "safety_regressions", "must_beat_production"},
    "ui": {"min_fps", "max_load_s", "max_sync_lag_ms", "output_divergence_count"}
}


class ThresholdsLoader:
    """Loads and validates thresholds configuration with strict gate checks."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else None
        self._raw_data: Dict[str, Any] = {}
        self._config: Optional[ThresholdsConfig] = None

    def load(self, path: Optional[Union[str, Path]] = None) -> "ThresholdsLoader":
        target_path = Path(path) if path else (self.config_path or Path("configs/thresholds.yaml"))
        if not target_path.exists():
            raise FileNotFoundError(f"Thresholds file not found at: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise MissingThresholdError("Thresholds configuration must be a dictionary")

        return self.load_from_dict(raw)

    def load_from_dict(self, raw: Dict[str, Any]) -> "ThresholdsLoader":
        self._raw_data = raw

        # Validate mandatory sections
        missing_sections = REQUIRED_SECTIONS - set(raw.keys())
        if missing_sections:
            raise MissingThresholdError(f"Missing required threshold sections: {sorted(missing_sections)}")

        # Validate mandatory keys per section
        for section, keys in REQUIRED_KEYS.items():
            section_data = raw.get(section)
            if not isinstance(section_data, dict):
                raise MissingThresholdError(f"Section '{section}' must be a dictionary")
            missing_keys = keys - set(section_data.keys())
            if missing_keys:
                raise MissingThresholdError(f"Missing required keys in section '{section}': {sorted(missing_keys)}")

        self._config = ThresholdsConfig(**raw)
        return self

    @property
    def config(self) -> ThresholdsConfig:
        if self._config is None:
            self.load()
        assert self._config is not None
        return self._config

    def __getattr__(self, name: str) -> Any:
        return getattr(self.config, name)

    def get(self, section: str, key: str) -> Any:
        """Retrieve threshold value. Raises KeyError if section or key is missing."""
        if section not in self._raw_data:
            raise MissingThresholdError(f"Threshold section not found: '{section}'")
        section_dict = self._raw_data[section]
        if key in section_dict:
            return section_dict[key]
        # Forward compatibility: a key known to the schema but not yet present
        # in the file (owner-provisioned provisional key) resolves to its
        # schema default (typically None -> NOT SET -> gates fail until set).
        section_model = getattr(self.config, section, None)
        if section_model is not None and key in type(section_model).model_fields:
            return getattr(section_model, key)
        raise MissingThresholdError(f"Threshold key not found: '{section}.{key}'")

    def is_set(self, section: str, key: str) -> bool:
        """Returns True if the threshold has a non-null value, False if null (NOT SET)."""
        val = self.get(section, key)
        return val is not None

    def get_status(self, section: str, key: str) -> ThresholdStatus:
        """Reports whether a threshold is SET or NOT_SET."""
        return ThresholdStatus.SET if self.is_set(section, key) else ThresholdStatus.NOT_SET

    def evaluate_gate(
        self,
        section: str,
        key: str,
        candidate_value: Any,
        comparator: str = ">="
    ) -> bool:
        """
        Evaluate candidate metric against threshold.
        Rule: A gate using a NOT SET (null) value FAILS automatically (returns False).
        """
        if not self.is_set(section, key):
            return False

        threshold_val = self.get(section, key)

        if comparator == ">=":
            return bool(candidate_value >= threshold_val)
        elif comparator == "<=":
            return bool(candidate_value <= threshold_val)
        elif comparator == "==":
            return bool(candidate_value == threshold_val)
        elif comparator == ">":
            return bool(candidate_value > threshold_val)
        elif comparator == "<":
            return bool(candidate_value < threshold_val)
        else:
            raise ValueError(f"Unsupported comparator: {comparator}")


_cached_loader: Optional[ThresholdsLoader] = None


def load_thresholds(path: Optional[Union[str, Path]] = None, reload: bool = False) -> ThresholdsLoader:
    """Global helper to load and cache thresholds configuration."""
    global _cached_loader
    if _cached_loader is None or reload:
        loader = ThresholdsLoader()
        loader.load(path)
        _cached_loader = loader
    return _cached_loader
