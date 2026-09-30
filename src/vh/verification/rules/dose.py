"""
Deterministic dose range and renal adjustment safety rule for AI Virtual Hospital (AI-VH).
Inspects recommended medication dosages and regimens against physiological parameters,
specifically renal clearance (eGFR / Serum Creatinine) and standard dose range limits.
"""

import re
from typing import Any, Dict, List, Optional
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule


def normalize_term(term: str) -> str:
    return re.sub(r"[^\w\s]", " ", str(term).lower()).strip()


class DoseRangeRule(SafetyRule):
    """Deterministic rule detecting supratherapeutic dosages and failure to adjust for renal impairment."""
    rule_id: str = "RULE-DOSE-001"
    description: str = "Validates dosage limits and enforces mandatory renal dose adjustments based on eGFR"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        findings: List[Finding] = []

        # Extract eGFR if available
        egfr: Optional[float] = None
        if "egfr" in patient_record and patient_record["egfr"] is not None:
            try:
                egfr = float(patient_record["egfr"])
            except (ValueError, TypeError):
                egfr = None
        elif "labs" in patient_record and isinstance(patient_record["labs"], dict):
            raw_egfr = patient_record["labs"].get("egfr")
            if raw_egfr is not None:
                try:
                    egfr = float(raw_egfr)
                except (ValueError, TypeError):
                    egfr = None

        # Dose rules configuration
        dose_table = knowledge.get("dose_ranges", {})

        # Default rules if table not provided
        if not dose_table:
            dose_table = {
                "enoxaparin": {
                    "generic_name": "enoxaparin",
                    "renal_adjustments": [
                        {
                            "egfr_threshold": 30.0,
                            "disallowed_patterns": ["every 12 hours", "q12h", "twice daily", "bid", "12 hours"],
                            "required_patterns": ["once daily", "q24h", "every 24 hours", "24 hours"],
                            "message": "Enoxaparin requires dose reduction to once daily in severe renal impairment (eGFR < 30 mL/min) to prevent lethal accumulation.",
                            "source": "DailyMed SPL Enoxaparin Sodium Section 2.2",
                        }
                    ],
                },
                "aspirin": {
                    "generic_name": "aspirin",
                    "max_dose_mg": 325.0,
                    "renal_adjustments": [],
                    "source": "2023 AHA/ACC ACS Guideline Section 5.1",
                },
                "metformin": {
                    "generic_name": "metformin",
                    "max_daily_dose_mg": 2550.0,
                    "renal_adjustments": [
                        {
                            "egfr_threshold": 30.0,
                            "disallowed_patterns": ["administer", "initiate", "continue", "prescribe", "mg"],
                            "message": "Metformin is strictly contraindicated in patients with eGFR < 30 mL/min due to lactic acidosis risk.",
                            "source": "FDA Drug Safety Communication Metformin",
                        }
                    ],
                },
                "amiodarone": {
                    "generic_name": "amiodarone",
                    "max_single_dose_mg": 400.0,
                    "max_daily_dose_mg": 1200.0,
                    "renal_adjustments": [],
                    "source": "AHA ACLS Guidelines 2020",
                },
            }

        drugs_dict = dose_table.get("drugs", dose_table)

        for drug_key, drug_info in drugs_dict.items():
            generic_name = normalize_term(drug_info.get("generic_name", drug_key))
            renal_rules = drug_info.get("renal_adjustments", [])
            max_dose = (
                drug_info.get("max_single_dose_mg")
                or drug_info.get("max_dose_mg")
                or drug_info.get("max_daily_dose_mg")
            )

            for rec in report.recommendations:
                rec_norm = normalize_term(rec.text)
                if not re.search(r"\b" + re.escape(generic_name) + r"\b", rec_norm):
                    continue

                # Check maximum dosage limits
                if max_dose is not None:
                    try:
                        max_limit = float(max_dose)
                        dose_match = re.search(r"(\d+(?:\.\d+)?)\s*mg", rec_norm)
                        if dose_match:
                            prescribed_dose = float(dose_match.group(1))
                            if prescribed_dose > max_limit:
                                source = drug_info.get("source", "FDA Package Insert")
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity="critical",
                                        claim_ids=rec.claim_ids,
                                        message=(
                                            f"Supratherapeutic dosage violation: Recommendation '{rec.text}' prescribes "
                                            f"{prescribed_dose} mg of '{generic_name.upper()}', exceeding maximum safe dosage limit of "
                                            f"{max_limit} mg."
                                        ),
                                        evidence=source,
                                    )
                                )
                    except (ValueError, TypeError):
                        pass

                # Check renal adjustments if eGFR is known
                if egfr is not None:
                    for r_rule in renal_rules:
                        threshold = float(r_rule.get("egfr_threshold", 30.0))
                        if egfr < threshold:
                            disallowed = r_rule.get("disallowed_patterns", [])
                            message = r_rule.get("message", f"Renal adjustment required for eGFR < {threshold}.")
                            source = r_rule.get("source", "FDA Package Insert")

                            # Check for violation of disallowed frequency/dosing
                            violated = False
                            for pattern in disallowed:
                                if pattern in rec_norm:
                                    violated = True
                                    break

                            if violated:
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity="critical",
                                        claim_ids=rec.claim_ids,
                                        message=(
                                            f"Renal dosing violation: Recommendation '{rec.text}' prescribes unadjusted regimen for "
                                            f"'{generic_name.upper()}' in patient with eGFR = {egfr} mL/min (threshold < {threshold} mL/min). "
                                            f"{message}"
                                        ),
                                        evidence=source,
                                    )
                                )

        return findings
