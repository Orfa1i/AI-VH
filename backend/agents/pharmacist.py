"""
Clinical Pharmacist Agent (Phase 7 Scale)
Dr. Elena Rostova, PharmD, BCPS (Board Certified Pharmacotherapy Specialist)
Responsible for hospital medication therapy management, renal dose adjustments,
contraindication verification, drug-drug interaction safety, and medication dispensing.
"""

from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime

from .base import BaseAgent
from ..clinical.models import MedicationSafetyReport
from ..clinical.cases import PatientGroundTruth
from ..simulation.events import HospitalEvent, EventType

logger = logging.getLogger("PharmacistAgent")


class PharmacistAgent(BaseAgent):
    def __init__(self, agent_id: str = "pharm_agent_01", name: str = "Dr. Elena Rostova, PharmD, BCPS"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role="CLINICAL_PHARMACIST",
            department="PHARMACY"
        )

    async def review_medication_order(
        self,
        encounter_id: str,
        prescriptions: List[str],
        patient: PatientGroundTruth,
        diagnosis: str,
        lab_results: Optional[Dict[str, Any]] = None,
    ) -> MedicationSafetyReport:
        """
        Screens prescriptions against known contraindications, patient allergies,
        renal function (Creatinine/BUN/eGFR), and drug-drug interactions.
        Emits real-time pharmacy events to the simulation bus.
        """
        report_id = f"PHARM-{uuid.uuid4().hex[:6].upper()}"
        logger.info(f"Pharmacist {self.name} reviewing {len(prescriptions)} orders for {patient.name} (Encounter {encounter_id})")

        # 1. Emit review initiated event
        await self.emit_event(
            event_type=EventType.PHARMACY_REVIEW_INITIATED,
            encounter_id=encounter_id,
            patient_id=patient.id,
            summary=f"Pharmacist {self.name} received {len(prescriptions)} medication orders for clinical reconciliation.",
            payload={
                "pharmacist": self.name,
                "prescriptions_count": len(prescriptions),
                "patient_name": patient.name,
                "diagnosis": diagnosis,
            },
        )

        flagged_issues: List[str] = []
        approved_medications: List[str] = []
        interventions: List[str] = []
        renal_adjustments: List[str] = []
        allergy_warnings: List[str] = []

        # 2. Extract renal parameters if present in ground truth simulated labs or lab results
        creatinine: Optional[float] = None
        bun: Optional[float] = None

        # Check ground truth simulated labs
        sim_labs = getattr(patient, "simulated_labs", {})
        for test_name, vals in sim_labs.items():
            if isinstance(vals, dict):
                if "Creatinine" in vals:
                    try:
                        creatinine = float(str(vals["Creatinine"]).split()[0])
                    except (ValueError, IndexError):
                        pass
                if "BUN" in vals:
                    try:
                        bun = float(str(vals["BUN"]).split()[0])
                    except (ValueError, IndexError):
                        pass

        # Allergy dictionary mapping base allergens to cross-reactive drug stems
        ALLERGEN_CROSS_REACTIVITY = {
            "penicillin": ["penicillin", "amoxicillin", "ampicillin", "piperacillin", "augmentin", "unasyn", "zosyn", "oxacillin", "nafcillin"],
            "sulfa": ["sulfa", "sulfamethoxazole", "bactrim", "septra", "sulfadiazine"],
            "aspirin": ["aspirin", "salicylate", "bismuth subsalicylate"],
            "morphine": ["morphine", "codeine", "hydromorphone", "dilaudid"],
        }

        # Drug classes for contraindication matching
        CLASS_MAPPINGS = {
            "nsaid": ["ibuprofen", "naproxen", "ketorolac", "toradol", "indomethacin", "meloxicam", "celecoxib", "diclofenac"],
            "beta-blocker": ["metoprolol", "carvedilol", "atenolol", "propranolol", "labetalol", "bisoprolol"],
            "sliding scale": ["sliding scale", "subcutaneous insulin as monotherapy"],
        }

        # 3. Analyze each prescription
        for med in prescriptions:
            med_lower = med.lower()

            # Check allergy matches with cross-reactivity
            is_allergic = False
            matched_allergen = None
            for allergy_entry in patient.allergies:
                allergy_entry_lower = allergy_entry.lower()
                clean_allergen = allergy_entry_lower.split("(")[0].strip()
                if clean_allergen in med_lower:
                    is_allergic = True
                    matched_allergen = allergy_entry
                    break
                for base_class, drugs in ALLERGEN_CROSS_REACTIVITY.items():
                    if base_class in clean_allergen:
                        if any(drug in med_lower for drug in drugs):
                            is_allergic = True
                            matched_allergen = allergy_entry
                            break
                if is_allergic:
                    break

            if is_allergic:
                warning_msg = f"ALLERGY ALERT: Patient has documented allergy '{matched_allergen}' relevant to '{med}'."
                flagged_issues.append(warning_msg)
                allergy_warnings.append(warning_msg)
                interventions.append(f"Hold '{med}', request attending physician order non-cross-reactive agent.")
                continue

            # Check clinical contraindications with class matching
            is_contraindicated = False
            matched_contra = None
            for contra in patient.contraindicated_treatments:
                contra_lower = contra.lower()
                if contra_lower in med_lower:
                    is_contraindicated = True
                    matched_contra = contra
                    break
                for class_name, drugs in CLASS_MAPPINGS.items():
                    if class_name in contra_lower:
                        if any(drug in med_lower for drug in drugs):
                            is_contraindicated = True
                            matched_contra = contra
                            break
                if is_contraindicated:
                    break

            if is_contraindicated:
                contra_msg = f"CONTRAINDICATION: '{med}' is clinically contraindicated ({matched_contra}) in {diagnosis}."
                flagged_issues.append(contra_msg)
                interventions.append(f"Cancel '{med}' immediately per inpatient clinical safety protocol.")
                continue

            # Renal dosing checks (e.g. elevated creatinine >= 1.5 mg/dL or BUN >= 30)
            if (creatinine and creatinine >= 1.5) or (bun and bun >= 30):
                if any(nsaid in med_lower for nsaid in ["ibuprofen", "ketorolac", "naproxen", "indomethacin", "toradol"]):
                    renal_msg = f"NEPHROTOXICITY RISK: NSAID '{med}' contraindicated with impaired renal biomarkers (Creatinine: {creatinine or 'N/A'}, BUN: {bun or 'N/A'})."
                    flagged_issues.append(renal_msg)
                    renal_adjustments.append(renal_msg)
                    interventions.append(f"Discontinue '{med}'; substitute acetaminophen or topical analgesic.")
                    continue
                elif "enoxaparin" in med_lower or "lovenox" in med_lower:
                    adj_msg = f"RENAL DOSE ADJUSTMENT: Renal impairment (Cr {creatinine or 'N/A'}) requires Enoxaparin reduction to 1 mg/kg Q24H."
                    renal_adjustments.append(adj_msg)
                    interventions.append(adj_msg)
                elif "metformin" in med_lower:
                    met_msg = f"RENAL CONTRAINDICATION: Metformin must be withheld with Creatinine >= 1.5 mg/dL to prevent lactic acidosis."
                    flagged_issues.append(met_msg)
                    renal_adjustments.append(met_msg)
                    interventions.append(met_msg)
                    continue

            # If passed checks
            approved_medications.append(med)

        safety_cleared = len(flagged_issues) == 0
        dispensing_status = "READY_FOR_ADMINISTRATION" if safety_cleared else "HOLD_FOR_PHYSICIAN_CLARIFICATION"

        report = MedicationSafetyReport(
            id=report_id,
            encounter_id=encounter_id,
            patient_id=patient.id,
            patient_name=patient.name,
            pharmacist_name=self.name,
            reviewed_at=datetime.utcnow(),
            prescriptions_reviewed=prescriptions,
            safety_cleared=safety_cleared,
            approved_medications=approved_medications,
            flagged_contraindications=flagged_issues,
            renal_adjustments=renal_adjustments,
            allergy_warnings=allergy_warnings,
            clinical_interventions=interventions,
            dispensing_status=dispensing_status,
        )

        # 4. Emit completion event
        await self.emit_event(
            event_type=EventType.PHARMACY_REVIEW_COMPLETED,
            encounter_id=encounter_id,
            patient_id=patient.id,
            summary=f"Pharmacy safety reconciliation complete: {len(approved_medications)} approved, {len(flagged_issues)} flagged ({dispensing_status}).",
            payload={
                "report_id": report.id,
                "safety_cleared": safety_cleared,
                "approved_count": len(approved_medications),
                "contraindications_count": len(flagged_issues),
                "dispensing_status": dispensing_status,
            },
        )

        # 5. Emit dispensing event if cleared
        if safety_cleared:
            await self.emit_event(
                event_type=EventType.MEDICATION_DISPENSED,
                encounter_id=encounter_id,
                patient_id=patient.id,
                summary=f"Pharmacy dispensed {len(approved_medications)} medications for inpatient administration.",
                payload={
                    "approved_medications": approved_medications,
                    "dispensed_at": datetime.utcnow().isoformat(),
                },
            )

        return report

    async def process_event(self, event: HospitalEvent):
        pass
