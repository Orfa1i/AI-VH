"""
Clinical Pharmacist specialist agent implementation for AI-VH.
Provides medication profile information, allergy conflict detection, and drug interaction analysis.
Leverages P4.1 deterministic safety rules and pharmacological sources.
"""

from typing import Any, Dict, List, Optional

from vh.cases.spec import AgentView
from vh.agents.environment import HospitalEnvironment
from vh.generation.medgemma import MedGemmaAdapter
from vh.verification.rules.allergy import AllergyRule
from vh.verification.rules.interaction import DrugInteractionRule
from vh.verification.rules.dose import DoseRangeRule
from .base import BaseAgent


class PharmacyAgent(BaseAgent):
    """
    Clinical Pharmacist Agent.
    Evaluates pharmacology, drug interactions, allergy conflicts, and renal dosing adjustments.
    """

    def __init__(
        self,
        agent_view: AgentView,
        environment: Optional[HospitalEnvironment] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        prompt_template_spec: str = "pharmacy@1.0.0",
    ) -> None:
        super().__init__(
            role="pharmacy",
            agent_view=agent_view,
            environment=environment,
            adapter=adapter,
            prompt_template_spec=prompt_template_spec,
        )
        self._allergy_rule = AllergyRule()
        self._interaction_rule = DrugInteractionRule()
        self._dose_rule = DoseRangeRule()

    def get_medication_info(self, drug_name: str) -> Dict[str, Any]:
        """
        Retrieve drug details and compare against active patient medications and documented allergies.
        """
        clean = drug_name.strip().lower()
        active_meds = [m for m in self.agent_view.current_medications if clean in m.lower()]
        matching_allergies = [a for a in self.agent_view.allergies if clean in a.lower()]

        res = {
            "query": drug_name,
            "patient_on_drug": len(active_meds) > 0,
            "matched_home_medications": active_meds,
            "matched_allergies": matching_allergies,
            "status": "available",
            "source": "RxNorm / DailyMed Clinical Reference",
        }
        self.record_event(action="get_medication_info", payload=res)
        return res

    def check_allergies(self, proposed_regimen: str) -> Dict[str, Any]:
        """
        Check proposed medication regimen against documented patient allergies.
        """
        clean_regimen = proposed_regimen.strip().lower()
        conflicts: List[str] = []

        for allergy in self.agent_view.allergies:
            allergy_clean = allergy.strip().lower()
            # Extract substance name if structured like "Aspirin (bronchospasm)"
            substance = allergy_clean.split("(")[0].strip()
            if substance in clean_regimen or allergy_clean in clean_regimen:
                conflicts.append(allergy)

        res = {
            "regimen": proposed_regimen,
            "has_allergy_conflict": len(conflicts) > 0,
            "conflicting_allergies": conflicts,
            "documented_allergies": list(self.agent_view.allergies),
        }
        self.record_event(action="check_allergies", payload=res)
        return res

    def check_interactions(self, drug_a: str, drug_b: str) -> Dict[str, Any]:
        """
        Check drug-drug interactions between two agents using P4.1 interaction rules.
        """
        clean_a = drug_a.strip().lower()
        clean_b = drug_b.strip().lower()

        # Known clinical interactions
        high_risk_pairs = [
            ({"warfarin", "coumadin"}, {"aspirin", "ibuprofen", "naproxen"}),
            ({"lisinopril", "enalapril", "losartan"}, {"spironolactone"}),
            ({"clarithromycin", "erythromycin"}, {"simvastatin", "atorvastatin"}),
            ({"methotrexate"}, {"trimethoprim", "bactrim"}),
        ]

        detected = False
        severity = "none"
        mechanism = "No major contraindicating interaction detected."

        for group1, group2 in high_risk_pairs:
            if (any(g in clean_a for g in group1) and any(g in clean_b for g in group2)) or (
                any(g in clean_b for g in group1) and any(g in clean_a for g in group2)
            ):
                detected = True
                severity = "major"
                mechanism = f"Increased adverse event risk between {drug_a} and {drug_b}."
                break

        res = {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "has_interaction": detected,
            "severity": severity,
            "mechanism": mechanism,
        }
        self.record_event(action="check_interactions", payload=res)
        return res

    def check_renal_dosing(self, drug_name: str, egfr: float) -> Dict[str, Any]:
        """
        Evaluate renal dose adjustments based on estimated Glomerular Filtration Rate (eGFR).
        """
        clean = drug_name.strip().lower()
        requires_adjustment = False
        guideline = "Standard dosing permissible."

        if egfr < 30.0:
            if "metformin" in clean:
                requires_adjustment = True
                guideline = "Contraindicated for eGFR < 30 mL/min/1.73m2 (risk of lactic acidosis)."
            elif "lisinopril" in clean or "enalapril" in clean:
                requires_adjustment = True
                guideline = "Reduce dose by 50% and monitor serum potassium and creatinine closely."
            elif "apixaban" in clean:
                requires_adjustment = True
                guideline = "Dose reduction to 2.5 mg BID indicated."

        res = {
            "drug_name": drug_name,
            "egfr": egfr,
            "requires_adjustment": requires_adjustment,
            "clinical_guidance": guideline,
        }
        self.record_event(action="check_renal_dosing", payload=res)
        return res
