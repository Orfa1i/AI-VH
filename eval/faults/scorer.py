"""
Fault evaluation and scoring engine for AI Virtual Hospital (AI-VH).
Audits verification layer performance across injected clinical faults,
computing detection rates per fault type, critical vs non-critical sensitivity,
and false-flag rate on clean original reports.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import uuid
import yaml

from vh.common.logging import get_logger
from vh.verification.router import ClinicalVerificationRouter, VerificationStatus
from .models import (
    FaultEvaluationReport,
    FaultSet,
    FaultSeverity,
    FaultType,
)

logger = get_logger("vh.eval.faults.scorer")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_THRESHOLDS_PATH = REPO_ROOT / "configs" / "thresholds.yaml"


class FaultInjectionScorer:
    """
    Evaluates the ClinicalVerificationRouter across clean and corrupted test cases.
    Verifies detection sensitivity and false-flag rates against threshold constraints.
    """

    def __init__(
        self,
        router: Optional[ClinicalVerificationRouter] = None,
        thresholds_path: Optional[Path] = None,
    ):
        self.router = router or ClinicalVerificationRouter()
        self.thresholds_path = thresholds_path or DEFAULT_THRESHOLDS_PATH
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> Dict[str, float]:
        """Loads verification thresholds from thresholds.yaml."""
        if not self.thresholds_path.exists():
            return {
                "critical_fault_detection": 1.0,
                "noncritical_fault_detection": 0.90,
                "false_flag_rate_max": 0.10,
            }
        with open(self.thresholds_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("verification", {})

    def evaluate(
        self,
        fault_set: FaultSet,
        run_id: Optional[str] = None,
    ) -> FaultEvaluationReport:
        """
        Executes verification across all clean cases and corrupted variants in fault_set.
        Computes detection rates and compares against thresholds.
        """
        active_run_id = run_id or f"run-fault-eval-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Audit Clean Originals (False-Flag Rate)
        total_clean = len(fault_set.clean_cases)
        false_flag_count = 0
        clean_results = []

        for clean_case in fault_set.clean_cases:
            envelope = self.router.verify(
                report=clean_case.report,
                patient_record=clean_case.patient_record,
                retrieved_chunks=clean_case.retrieved_chunks,
            )
            is_flagged = (envelope.status == VerificationStatus.FLAGGED)
            if is_flagged:
                false_flag_count += 1
                logger.warning(
                    f"False flag on clean case {clean_case.case_id}: reasons={envelope.reasons}"
                )
            clean_results.append({
                "case_id": clean_case.case_id,
                "status": envelope.status.value,
                "reasons": list(envelope.reasons),
            })

        false_flag_rate = (false_flag_count / total_clean) if total_clean > 0 else 0.0

        # 2. Audit Corrupted Variants (Detection Rates)
        total_corrupted = len(fault_set.corrupted_cases)
        stats_by_type: Dict[str, Dict[str, Any]] = {
            ft.value: {"total": 0, "detected": 0, "rate": 0.0, "severity": ""}
            for ft in FaultType
        }

        critical_total = 0
        critical_detected = 0
        noncritical_total = 0
        noncritical_detected = 0

        for corrupt_case in fault_set.corrupted_cases:
            ft_key = corrupt_case.fault_type.value
            stats = stats_by_type[ft_key]
            stats["total"] += 1
            stats["severity"] = corrupt_case.severity.value

            is_critical = (corrupt_case.severity == FaultSeverity.CRITICAL)
            if is_critical:
                critical_total += 1
            else:
                noncritical_total += 1

            envelope = self.router.verify(
                report=corrupt_case.corrupted_report,
                patient_record=corrupt_case.patient_record,
                retrieved_chunks=corrupt_case.retrieved_chunks,
            )

            is_detected = (envelope.status == VerificationStatus.FLAGGED)
            if is_detected:
                stats["detected"] += 1
                if is_critical:
                    critical_detected += 1
                else:
                    noncritical_detected += 1
            else:
                logger.warning(
                    f"Missed fault detection on {corrupt_case.case_id} ({ft_key}): "
                    f"Report unexpectedly verified!"
                )

        # Compute rates per fault type
        for ft_key, stats in stats_by_type.items():
            t = stats["total"]
            d = stats["detected"]
            stats["rate"] = round(d / t, 4) if t > 0 else 0.0

        critical_detection_rate = (
            round(critical_detected / critical_total, 4) if critical_total > 0 else 0.0
        )
        noncritical_detection_rate = (
            round(noncritical_detected / noncritical_total, 4) if noncritical_total > 0 else 0.0
        )
        false_flag_rate = round(false_flag_rate, 4)

        # 3. Compare with thresholds
        crit_min = self.thresholds.get("critical_fault_detection", 1.0)
        noncrit_min = self.thresholds.get("noncritical_fault_detection", 0.90)
        false_max = self.thresholds.get("false_flag_rate_max", 0.10)

        passed = (
            critical_detection_rate >= crit_min
            and noncritical_detection_rate >= noncrit_min
            and false_flag_rate <= false_max
        )

        return FaultEvaluationReport(
            run_id=active_run_id,
            total_cases=total_clean + total_corrupted,
            total_corrupted=total_corrupted,
            total_clean=total_clean,
            detection_by_fault_type=stats_by_type,
            critical_detection_rate=critical_detection_rate,
            noncritical_detection_rate=noncritical_detection_rate,
            false_flag_rate=false_flag_rate,
            thresholds={
                "critical_fault_detection": crit_min,
                "noncritical_fault_detection": noncrit_min,
                "false_flag_rate_max": false_max,
            },
            passed=passed,
            evaluated_at=now_iso,
        )
