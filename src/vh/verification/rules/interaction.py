"""
Deterministic drug-drug interaction (DDI) safety rule for AI Virtual Hospital (AI-VH).
Cross-references newly recommended medications against active outpatient prescriptions,
identifying pharmacokinetic (e.g. CYP3A4, CYP2C19 inhibition) and pharmacodynamic interactions.
"""

import re
from typing import Any, Dict, List
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule


def normalize_term(term: str) -> str:
    return re.sub(r"[^\w\s]", " ", str(term).lower()).strip()


class DrugInteractionRule(SafetyRule):
    """Deterministic rule detecting severe drug-drug interactions between recommendations and current meds."""
    rule_id: str = "RULE-DDI-001"
    description: str = "Checks recommendations against current outpatient medications for severe adverse interactions"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        findings: List[Finding] = []
        current_meds = patient_record.get("current_medications", [])
        if not current_meds:
            return findings

        norm_current_meds = [normalize_term(m) for m in current_meds if m]
        interactions_table = knowledge.get("interactions", [])

        # Default rules if table not supplied
        if not interactions_table:
            interactions_table = [
                {
                    "drug_a_names": ["simvastatin", "zocor", "lovastatin"],
                    "drug_b_names": ["amiodarone", "cordarone", "clarithromycin", "erythromycin"],
                    "severity": "critical",
                    "message": "CYP3A4 inhibition markedly elevates statin concentrations, substantially increasing rhabdomyolysis risk.",
                    "evidence": "DailyMed Simvastatin SPL Section 7; FDA Drug Safety Communication",
                },
                {
                    "drug_a_names": ["clopidogrel", "plavix"],
                    "drug_b_names": ["omeprazole", "esomeprazole"],
                    "severity": "major",
                    "message": "Omeprazole inhibits CYP2C19 activation of Clopidogrel, significantly reducing antiplatelet efficacy.",
                    "evidence": "FDA Boxed Warning on Clopidogrel and Omeprazole",
                },
                {
                    "drug_a_names": ["aspirin", "nsaid", "ibuprofen"],
                    "drug_b_names": ["warfarin", "coumadin", "rivaroxaban", "apixaban", "dabigatran"],
                    "severity": "major",
                    "message": "Concurrent antiplatelet and anticoagulant therapy substantially elevates major bleeding risk.",
                    "evidence": "CHEST Guideline for Antithrombotic Therapy",
                },
                {
                    "drug_a_names": ["potassium", "kcl"],
                    "drug_b_names": ["spironolactone", "eplerenone"],
                    "severity": "critical",
                    "message": "Potassium supplementation with potassium-sparing diuretics precipitates life-threatening hyperkalemia.",
                    "evidence": "DailyMed Spironolactone SPL Warnings",
                },
            ]

        for ddi in interactions_table:
            drug_a_list = [normalize_term(d) for d in ddi.get("drug_a_names", [])]
            drug_b_list = [normalize_term(d) for d in ddi.get("drug_b_names", [])]
            severity = ddi.get("severity", "critical")
            message = ddi.get("message", "Adverse drug-drug interaction detected.")
            evidence = ddi.get("evidence", "DailyMed Drug Interaction Section 7")

            # Check if any current medication matches drug_a or drug_b
            current_matches_a = []
            current_matches_b = []

            for med in norm_current_meds:
                for a in drug_a_list:
                    if re.search(r"\b" + re.escape(a) + r"\b", med):
                        current_matches_a.append((a, med))
                for b in drug_b_list:
                    if re.search(r"\b" + re.escape(b) + r"\b", med):
                        current_matches_b.append((b, med))

            # Now check recommendations for the complementary partner
            for rec in report.recommendations:
                rec_norm = normalize_term(rec.text)

                # Case 1: current med is A, recommendation contains B
                if current_matches_a:
                    for b in drug_b_list:
                        if re.search(r"\b" + re.escape(b) + r"\b", rec_norm):
                            for matched_a, orig_med in current_matches_a:
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity=severity,
                                        claim_ids=rec.claim_ids,
                                        message=(
                                            f"Severe Drug Interaction: Recommended therapy '{rec.text}' contains '{b.upper()}', "
                                            f"which interacts adversely with current medication '{orig_med}'. {message}"
                                        ),
                                        evidence=evidence,
                                    )
                                )
                                break

                # Case 2: current med is B, recommendation contains A
                if current_matches_b:
                    for a in drug_a_list:
                        if re.search(r"\b" + re.escape(a) + r"\b", rec_norm):
                            for matched_b, orig_med in current_matches_b:
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity=severity,
                                        claim_ids=rec.claim_ids,
                                        message=(
                                            f"Severe Drug Interaction: Recommended therapy '{rec.text}' contains '{a.upper()}', "
                                            f"which interacts adversely with current medication '{orig_med}'. {message}"
                                        ),
                                        evidence=evidence,
                                    )
                                )
                                break

        return findings
