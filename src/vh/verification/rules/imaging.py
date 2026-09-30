"""
Imaging-evidence citation rule for AI-VH (STEP 51 / P9.1 extension of P4.1).

Claims that mention imaging findings must cite a tool-output evidence id
(prefix IMG-) previously issued by an imaging tool run. Known tool ids arrive
via the knowledge context (`imaging_tool_outputs`); with none known, every
imaging-mentioning claim is flagged (fail closed).
"""

from typing import Any, Dict, List

from vh.generation.report import ClinicalReport, find_uncited_imaging_claims
from .base import Finding, SafetyRule


class ImagingCitationRule(SafetyRule):
    """Deterministic rule flagging imaging claims without tool-output citations."""
    rule_id: str = "RULE-IMAGING-CITE-001"
    description: str = "Requires imaging findings to cite tool-output evidence ids"

    def evaluate(
        self,
        report: ClinicalReport,
        patient_record: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Finding]:
        tool_ids = set(knowledge.get("imaging_tool_outputs", []) or [])
        findings: List[Finding] = []
        for claim_id in find_uncited_imaging_claims(report, tool_ids):
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity="major",
                    claim_ids=[claim_id],
                    message=(
                        f"Claim '{claim_id}' describes imaging findings without citing "
                        f"a tool-output evidence id (prefix IMG-). Imaging claims must "
                        f"reference the tool run that produced them."
                    ),
                    evidence="P9.1 imaging citation requirement (STEP-51).",
                )
            )
        return findings
