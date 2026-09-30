"""
Deterministic patient data contradiction rule for AI Virtual Hospital (AI-VH).
Audits clinical report statements against authoritative patient records (vitals, laboratory findings),
detecting factual discrepancies, fabricated normal values, and physiological contradictions.
"""

import re
from typing import Any, Dict, List, Optional
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule


class PatientDataContradictionRule(SafetyRule):
    """Deterministic rule detecting contradictory clinical claims differing from patient record."""
    rule_id: str = "RULE-CONTRADICTION-001"
    description: str = "Detects factual contradictions between generated clinical text and ground truth patient data"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        findings: List[Finding] = []
        text_corpus = (report.patient_summary + " " + " ".join(report.findings)).lower()

        # 1. Audit Heart Rate (HR)
        vitals = patient_record.get("vitals", {})
        if isinstance(vitals, dict):
            record_hr = vitals.get("hr")
            if record_hr is not None:
                try:
                    hr_val = float(record_hr)
                    # If true HR is severely tachycardic (> 110), report asserting normal HR (60-90) is a contradiction
                    if hr_val > 110:
                        # Look for stated HR in report text: "hr 72", "heart rate of 70", "heart rate 72"
                        match = re.search(r"(?:heart rate|hr)[^\d]*(\d{2,3})", text_corpus)
                        if match:
                            stated_hr = float(match.group(1))
                            if abs(stated_hr - hr_val) > 25:
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity="critical",
                                        claim_ids=[],
                                        message=(
                                            f"Patient data contradiction: Report asserts heart rate of {int(stated_hr)} bpm, "
                                            f"directly contradicting documented patient record heart rate of {int(hr_val)} bpm."
                                        ),
                                        evidence="Documented vital signs in patient record",
                                    )
                                )
                except (ValueError, TypeError):
                    pass

            # 2. Audit Oxygen Saturation (SpO2)
            record_spo2 = vitals.get("spo2")
            if record_spo2 is not None:
                try:
                    spo2_val = float(record_spo2)
                    if spo2_val < 90:
                        match = re.search(r"(?:spo2|saturation|o2 sat)[^\d]*(\d{2,3})", text_corpus)
                        if match:
                            stated_spo2 = float(match.group(1))
                            if stated_spo2 >= 95 and abs(stated_spo2 - spo2_val) >= 6:
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity="critical",
                                        claim_ids=[],
                                        message=(
                                            f"Patient data contradiction: Report asserts SpO2 of {int(stated_spo2)}%, "
                                            f"contradicting documented hypoxemia (SpO2 {int(spo2_val)}%) in patient record."
                                        ),
                                        evidence="Documented pulse oximetry in patient record",
                                    )
                                )
                except (ValueError, TypeError):
                    pass

        # 3. Audit Critical Laboratory Values (e.g. Potassium)
        labs = patient_record.get("labs", {})
        if isinstance(labs, dict):
            record_k = labs.get("potassium")
            if record_k is not None:
                try:
                    k_val = float(record_k)
                    if k_val >= 6.0:
                        match = re.search(r"(?:potassium|k\+)[^\d]*(\d(?:\.\d+)?)", text_corpus)
                        if match:
                            stated_k = float(match.group(1))
                            if stated_k < 5.0:
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity="critical",
                                        claim_ids=[],
                                        message=(
                                            f"Patient data contradiction: Report asserts potassium of {stated_k} mEq/L, "
                                            f"contradicting severe hyperkalemia ({k_val} mEq/L) in patient record."
                                        ),
                                        evidence="Documented emergency laboratory panel",
                                    )
                                )
                except (ValueError, TypeError):
                    pass

        return findings
