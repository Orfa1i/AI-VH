"""
Deterministic red-flag coverage safety rule for AI Virtual Hospital (AI-VH).
Inspects documented patient vitals and emergency warning signs against curated red-flag tables.
Enforces that every active physiological emergency is actively addressed in recommendations or differential.
"""

from typing import Any, Dict, List
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule


class RedFlagCoverageRule(SafetyRule):
    """Deterministic rule detecting unaddressed physiological red-flag warning signs."""
    rule_id: str = "RULE-REDFLAG-001"
    description: str = "Ensures active physiological emergency parameters are explicitly addressed in clinical plans"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        findings: List[Finding] = []
        vitals = patient_record.get("vitals", {})
        if not isinstance(vitals, dict):
            return findings

        # Assemble full generated report text
        plan_text = " ".join([
            report.patient_summary,
            " ".join(report.findings),
            " ".join([d.dx for d in report.differential]),
            " ".join([r.text for r in report.recommendations]),
        ]).lower()

        rf_table = knowledge.get("red_flags", {})
        criteria = rf_table.get("criteria", [])

        # Default criteria if table not provided
        if not criteria:
            criteria = [
                {
                    "flag_id": "RF-HYPOXEMIA",
                    "name": "Severe Hypoxemia",
                    "parameter": "spo2",
                    "operator": "lt",
                    "threshold": 90.0,
                    "severity": "critical",
                    "required_keywords": ["oxygen", "o2", "ventilat", "airway", "respirat", "hypox"],
                    "message": "Patient exhibits severe hypoxemia (SpO2 < 90%). The report must explicitly order oxygenation or airway management.",
                    "evidence": "Surviving Sepsis Campaign 2021 Guideline Section 4.2",
                },
                {
                    "flag_id": "RF-HYPOTENSION",
                    "name": "Profound Hypotension",
                    "parameter": "sbp",
                    "operator": "lt",
                    "threshold": 90.0,
                    "severity": "critical",
                    "required_keywords": ["fluid", "resuscitat", "bolus", "vasopressor", "norepinephrine", "hypotension", "shock"],
                    "message": "Patient exhibits profound hypotension (SBP < 90 mmHg). The report must address hemodynamic stabilization.",
                    "evidence": "AHA ACLS Hypotension and Shock Algorithm",
                },
                {
                    "flag_id": "RF-SEVERE-TACHYCARDIA",
                    "name": "Severe Tachycardia",
                    "parameter": "hr",
                    "operator": "gt",
                    "threshold": 120.0,
                    "severity": "major",
                    "required_keywords": ["tachycardia", "rate control", "ecg", "rhythm", "beta-blocker", "cardioversion"],
                    "message": "Patient exhibits severe tachycardia (HR > 120 bpm). The report must evaluate cardiac etiology or rate control.",
                    "evidence": "AHA Adult Tachycardia with Pulse Algorithm",
                },
            ]

        for crit in criteria:
            param = crit.get("parameter")
            op = crit.get("operator")
            threshold = float(crit.get("threshold", 0.0))
            required_kw = crit.get("required_keywords", [])
            severity = crit.get("severity", "critical")
            message = crit.get("message", "Emergency red flag omitted.")
            evidence = crit.get("evidence", "Emergency Clinical Care Guidelines")

            # Check if parameter is present in vitals
            val = vitals.get(param)
            if val is None:
                continue

            try:
                numeric_val = float(val)
            except (ValueError, TypeError):
                continue

            # Evaluate threshold
            triggered = False
            if op == "lt" and numeric_val < threshold:
                triggered = True
            elif op == "gt" and numeric_val > threshold:
                triggered = True

            if not triggered:
                continue

            # Check if report addressed the red flag
            addressed = any(kw in plan_text for kw in required_kw)
            if not addressed:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=severity,
                        claim_ids=[],
                        message=f"Unaddressed Emergency Red Flag: {message}",
                        evidence=evidence,
                    )
                )

        return findings
