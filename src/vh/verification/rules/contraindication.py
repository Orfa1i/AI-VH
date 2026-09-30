"""
Deterministic contraindication safety rule for AI Virtual Hospital (AI-VH).
Validates recommended pharmacotherapies against active medical conditions and comorbidities,
referencing curated clinical practice guidelines and FDA contraindication tables.
"""

import re
from typing import Any, Dict, List
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule


def normalize_term(term: str) -> str:
    return re.sub(r"[^\w\s]", " ", str(term).lower()).strip()


class ContraindicationRule(SafetyRule):
    """Deterministic rule detecting recommended medications contraindicated by active patient conditions."""
    rule_id: str = "RULE-CONTRAINDICATION-001"
    description: str = "Checks recommendations for absolute and high-risk disease-drug contraindications"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        findings: List[Finding] = []
        active_conditions = patient_record.get("active_conditions", [])
        if not active_conditions:
            return findings

        norm_conditions = [normalize_term(c) for c in active_conditions if c]
        rules_table = knowledge.get("contraindications", [])

        # Default rules if table not supplied
        if not rules_table:
            rules_table = [
                {
                    "drug_names": ["ketorolac", "toradol", "nsaid", "ibuprofen", "naproxen"],
                    "condition_matches": ["peptic ulcer", "gi bleed", "gastrointestinal bleeding", "active bleeding", "renal failure"],
                    "severity": "critical",
                    "rationale": "NSAIDs precipitate gastrointestinal hemorrhage and acute renal decompensation in active peptic ulcer or active bleeding.",
                    "source": "DailyMed Ketorolac Tromethamine Boxed Warning",
                },
                {
                    "drug_names": ["metoprolol", "atenolol", "propranolol", "carvedilol"],
                    "condition_matches": ["cardiogenic shock", "second degree av block", "third degree av block", "severe bradycardia"],
                    "severity": "critical",
                    "rationale": "Beta-blockers depress cardiac contractility and dromotropy in shock or advanced AV block.",
                    "source": "2023 AHA/ACC ACS Management Guideline",
                },
                {
                    "drug_names": ["metformin", "glucophage"],
                    "condition_matches": ["diabetic ketoacidosis", "metabolic acidosis", "lactic acidosis", "severe sepsis"],
                    "severity": "critical",
                    "rationale": "Metformin increases risk of fatal lactic acidosis in acute acidotic or hypoperfused states.",
                    "source": "DailyMed Metformin Boxed Warning",
                },
                {
                    "drug_names": ["nitroglycerin", "isosorbide", "nitrate"],
                    "condition_matches": ["right ventricular infarction", "pde-5 inhibitor", "severe hypotension"],
                    "severity": "critical",
                    "rationale": "Nitrates cause catastrophic refractory hypotension in right ventricular infarction or with PDE-5 inhibitors.",
                    "source": "2023 AHA/ACC ACS Guideline",
                },
            ]

        for rule in rules_table:
            drug_names = [normalize_term(d) for d in rule.get("drug_names", [])]
            condition_matches = [normalize_term(c) for c in rule.get("condition_matches", [])]
            severity = rule.get("severity", "critical")
            rationale = rule.get("rationale", "Medication contraindicated in active condition.")
            source = rule.get("source", "Clinical Practice Guideline")

            # Check if patient has any matching condition
            matched_condition = None
            for cond in norm_conditions:
                for target_cond in condition_matches:
                    if target_cond in cond:
                        matched_condition = cond
                        break
                if matched_condition:
                    break

            if not matched_condition:
                continue

            # Check if any recommendation contains contraindicated drug
            for rec in report.recommendations:
                rec_norm = normalize_term(rec.text)
                for drug in drug_names:
                    pattern = r"\b" + re.escape(drug) + r"\b"
                    if re.search(pattern, rec_norm):
                        findings.append(
                            Finding(
                                rule_id=self.rule_id,
                                severity=severity,
                                claim_ids=rec.claim_ids,
                                message=(
                                    f"Contraindication detected: Recommendation '{rec.text}' contains '{drug.upper()}', "
                                    f"which is contraindicated by active condition '{matched_condition.upper()}'. {rationale}"
                                ),
                                evidence=source,
                            )
                        )
                        break

        return findings
