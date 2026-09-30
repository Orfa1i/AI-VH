"""
Deterministic clinical safety rules engine for AI Virtual Hospital (AI-VH).
Serves as the deterministic last line of defense catching adverse drug events,
contraindications, dosage errors, physiological red-flag omissions, and factual contradictions.
Operates with zero LLM dependencies and refuses execution with draft tables in production mode.
"""

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import yaml
from pydantic import BaseModel, Field

from vh.common.logging import get_logger
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule
from .allergy import AllergyRule
from .contraindication import ContraindicationRule
from .interaction import DrugInteractionRule
from .dose import DoseRangeRule
from .contradiction import PatientDataContradictionRule
from .red_flags import RedFlagCoverageRule

logger = get_logger("vh.verification.engine")
REPO_ROOT = Path(__file__).resolve().parents[4]


class SafetyConfigurationError(Exception):
    """Raised when safety rules engine configuration is invalid (e.g. draft tables in production mode)."""
    pass


class SafetyEvaluationResult(BaseModel):
    """Aggregated safety assessment produced by the deterministic rules engine."""
    passed: bool = Field(description="True if zero critical safety violations were detected")
    findings: List[Finding] = Field(default_factory=list, description="All detected safety violations")
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0


class DeterministicSafetyEngine:
    """
    Deterministic safety rules coordinator.
    Enforces that safety tables are fully verified before production deployment
    and executes all registered clinical safety rules in fixed, deterministic order.
    """

    def __init__(
        self,
        mode: Literal["dev", "production"] = "dev",
        safety_dir: Optional[Path] = None,
        rules: Optional[List[SafetyRule]] = None,
    ):
        self.mode = mode
        self.safety_dir = Path(safety_dir or (REPO_ROOT / "configs" / "safety"))
        self.knowledge: Dict[str, Any] = {}

        # Default rules pipeline
        self.rules: List[SafetyRule] = rules or [
            AllergyRule(),
            ContraindicationRule(),
            DrugInteractionRule(),
            DoseRangeRule(),
            PatientDataContradictionRule(),
            RedFlagCoverageRule(),
        ]

        self._load_safety_tables()

    def _load_safety_tables(self) -> None:
        """Loads and validates curated safety YAML tables from disk."""
        if not self.safety_dir.exists():
            logger.warning(f"Safety configuration directory '{self.safety_dir}' does not exist.")
            return

        table_files = {
            "dose_ranges": self.safety_dir / "dose_ranges.yaml",
            "contraindications": self.safety_dir / "contraindications.yaml",
            "interactions": self.safety_dir / "drug_interactions.yaml",
            "red_flags": self.safety_dir / "red_flags.yaml",
        }

        for key, path in table_files.items():
            if path.exists():
                try:
                    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                    self.knowledge[key] = data
                    status = data.get("metadata", {}).get("status", "draft")

                    if status == "draft":
                        if self.mode == "production":
                            raise SafetyConfigurationError(
                                f"Production safety engine refusal: Safety table '{path.name}' has 'status: draft'. "
                                f"Physician review and approval at Checkpoint H4 is mandatory before production activation."
                            )
                        else:
                            logger.warning(
                                f"Development mode warning: Safety table '{path.name}' is unverified (status: draft)."
                            )
                except SafetyConfigurationError:
                    raise
                except Exception as exc:
                    logger.error(f"Failed to parse safety table '{path}': {exc}")
                    if self.mode == "production":
                        raise SafetyConfigurationError(f"Error loading safety table '{path}': {exc}")

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
    ) -> SafetyEvaluationResult:
        """
        Executes all deterministic safety rules against the clinical report and patient record.
        Sorts findings stably by severity (critical -> major -> minor) and rule_id.
        """
        all_findings: List[Finding] = []

        # Execute rules sequentially (zero randomness, zero async nondeterminism)
        for rule in self.rules:
            try:
                rule_findings = rule.evaluate(
                    report=report,
                    patient_record=patient_record,
                    knowledge=self.knowledge,
                )
                all_findings.extend(rule_findings)
            except Exception as exc:
                logger.error(f"Rule '{rule.rule_id}' raised unexpected exception: {exc}")
                # Fail closed on internal rule error
                all_findings.append(
                    Finding(
                        rule_id=rule.rule_id,
                        severity="critical",
                        claim_ids=[],
                        message=f"Safety rule evaluation failed with exception: {exc}",
                        evidence="Internal safety engine fail-closed error guard",
                    )
                )

        # Stable sorting key: severity rank, then rule_id, then message
        severity_rank = {"critical": 0, "major": 1, "minor": 2}
        all_findings.sort(key=lambda f: (severity_rank.get(f.severity, 99), f.rule_id, f.message))

        crit = sum(1 for f in all_findings if f.severity == "critical")
        maj = sum(1 for f in all_findings if f.severity == "major")
        minr = sum(1 for f in all_findings if f.severity == "minor")

        passed = bool(crit == 0)

        return SafetyEvaluationResult(
            passed=passed,
            findings=all_findings,
            critical_count=crit,
            major_count=maj,
            minor_count=minr,
        )
