"""
Deterministic allergy safety rule for AI Virtual Hospital (AI-VH).
Checks clinical recommendations and claims against patient allergy records,
matching both exact ingredients and broader drug classes (e.g., penicillins, sulfonamides, NSAIDs).
"""

import re
from typing import Any, Dict, List, Set
from vh.generation.report import ClinicalReport
from .base import Finding, SafetyRule

# Drug class expansion mappings (clinical pharmacology aliases)
DRUG_CLASSES: Dict[str, List[str]] = {
    "penicillin": [
        "penicillin", "amoxicillin", "ampicillin", "piperacillin",
        "augmentin", "nafcillin", "oxacillin", "unasyn", "zosyn"
    ],
    "cephalosporin": [
        "cephalexin", "cefazolin", "ceftriaxone", "cefepime", "cefdinir"
    ],
    "sulfonamide": [
        "sulfamethoxazole", "bactrim", "septra", "sulfadiazine", "sulfasalazine"
    ],
    "nsaid": [
        "aspirin", "ibuprofen", "naproxen", "ketorolac", "toradol",
        "meloxicam", "indomethacin", "celecoxib", "diclofenac"
    ],
    "ace_inhibitor": [
        "lisinopril", "enalapril", "ramipril", "benazepril", "captopril"
    ],
    "statin": [
        "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin"
    ],
}


def normalize_term(term: str) -> str:
    return re.sub(r"[^\w\s]", " ", str(term).lower()).strip()


class AllergyRule(SafetyRule):
    """Deterministic rule detecting recommended medications contraindicated by patient allergies."""
    rule_id: str = "RULE-ALLERGY-001"
    description: str = "Checks recommendations for documented patient drug allergies and cross-reactive classes"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        findings: List[Finding] = []
        raw_allergies = patient_record.get("allergies", [])
        if not raw_allergies:
            return findings

        # Extract allergy terms and their class expansions
        allergic_terms: Set[str] = set()
        for allergy in raw_allergies:
            substance = allergy.get("substance", "") if isinstance(allergy, dict) else str(allergy)
            norm_sub = normalize_term(substance)
            if not norm_sub:
                continue
            allergic_terms.add(norm_sub)

            # Check if substance maps to a known drug class
            for cls_name, members in DRUG_CLASSES.items():
                if norm_sub == cls_name or norm_sub in members:
                    allergic_terms.update(members)
                    allergic_terms.add(cls_name)

        # Inspect all recommendations
        for rec in report.recommendations:
            rec_text = normalize_term(rec.text)
            for allergic_term in allergic_terms:
                if not allergic_term or len(allergic_term) < 3:
                    continue
                # Word boundary check
                pattern = r"\b" + re.escape(allergic_term) + r"\b"
                if re.search(pattern, rec_text):
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity="critical",
                            claim_ids=rec.claim_ids,
                            message=(
                                f"Recommended therapy '{rec.text}' contains or belongs to allergic class "
                                f"'{allergic_term.upper()}', violating documented patient allergy."
                            ),
                            evidence="Patient documented allergy record; FDA Boxed Warnings on Hypersensitivity",
                        )
                    )
                    break

        return findings
