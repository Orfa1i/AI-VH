"""
Fault generation engine for AI Virtual Hospital (AI-VH).
Synthesizes verified clean baseline reports and generates labelled corrupted variants
covering all 9 required verification fault types.
"""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from vh.common.artifacts import ArtifactKind, ArtifactRecord, ArtifactRegistry, get_artifact_registry
from vh.generation.report import (
    ClaimItem,
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ReportProvenance,
)
from .config import load_fault_classification
from .models import (
    CleanCase,
    CorruptedCase,
    FaultClassificationConfig,
    FaultSeverity,
    FaultSet,
    FaultType,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class FaultGenerator:
    """
    Generates clean clinical reports and labelled corrupted variants for fault injection testing.
    Produces at least 20 instances for every fault type.
    """

    def __init__(self, classification_config: Optional[FaultClassificationConfig] = None):
        self.classification_config = classification_config or load_fault_classification()

    def generate_fault_set(
        self,
        instances_per_fault: int = 25,
        version: str = "v1.0.0",
        seed: int = 42,
    ) -> FaultSet:
        """
        Generates a complete fault set containing clean cases and corrupted variants.
        Guarantees that every fault type appears at least instances_per_fault times.
        """
        clean_prototypes = self._build_clean_prototypes()
        clean_cases: List[CleanCase] = []

        # Generate clean baseline cases
        for i in range(instances_per_fault):
            proto = clean_prototypes[i % len(clean_prototypes)]
            case_id = f"CASE-CLEAN-{i+1:03d}"
            case_clean_report = deepcopy(proto["report"])
            case_clean_report.provenance.case_id = case_id
            clean_cases.append(
                CleanCase(
                    case_id=case_id,
                    report=case_clean_report,
                    patient_record=deepcopy(proto["patient_record"]),
                    retrieved_chunks=deepcopy(proto["retrieved_chunks"]),
                )
            )

        corrupted_cases: List[CorruptedCase] = []

        # Generate corrupted variants for all 9 fault types
        for ft in FaultType:
            info = self.classification_config.classifications[ft]
            severity = info.severity

            for i in range(instances_per_fault):
                proto = clean_prototypes[i % len(clean_prototypes)]
                corrupt_case = self._mutate_case(
                    prototype=proto,
                    fault_type=ft,
                    severity=severity,
                    index=i + 1,
                )
                corrupted_cases.append(corrupt_case)

        now_iso = datetime.now(timezone.utc).isoformat()
        return FaultSet(
            version=version,
            created_at=now_iso,
            clean_cases=clean_cases,
            corrupted_cases=corrupted_cases,
        )

    def register_as_artifact(
        self,
        fault_set: FaultSet,
        registry: Optional[ArtifactRegistry] = None,
        version: Optional[str] = None,
    ) -> ArtifactRecord:
        """
        Persists and registers the fault set as a versioned fault_set artifact.
        """
        reg = registry or get_artifact_registry()
        v = version or fault_set.version
        raw_json = fault_set.model_dump_json(indent=2)

        counts_by_type = {}
        for c in fault_set.corrupted_cases:
            counts_by_type[c.fault_type.value] = counts_by_type.get(c.fault_type.value, 0) + 1

        metadata = {
            "total_clean": len(fault_set.clean_cases),
            "total_corrupted": len(fault_set.corrupted_cases),
            "counts_by_fault_type": counts_by_type,
            "version": v,
            "created_at": fault_set.created_at,
        }

        record = reg.register_artifact(
            kind=ArtifactKind.FAULT_SET,
            name="verification_fault_set",
            version=v,
            content=raw_json,
            metadata=metadata,
        )
        return record

    def _build_clean_prototypes(self) -> List[Dict[str, Any]]:
        """
        Constructs verified clean clinical encounters with high entailment and zero safety hazards.
        """
        # Prototype 1: Acute Coronary Syndrome (ACS)
        acs_chunks = {
            "CHUNK-ACC-ACS-01": (
                "For acute coronary syndrome, administer Aspirin 325 mg orally immediately to inhibit platelet aggregation. "
                "Obtain urgent 12-lead electrocardiogram and serial high-sensitivity cardiac troponin I measurements. "
                "Initiate continuous cardiac rhythm monitoring and place dual peripheral intravenous catheters."
            ),
        }
        acs_claims = [
            ClaimItem(
                claim_id="CLM-ACS-01",
                text="Aspirin 325 mg orally should be administered immediately for acute coronary syndrome.",
                type="therapeutic",
                evidence_ids=["CHUNK-ACC-ACS-01"],
            ),
            ClaimItem(
                claim_id="CLM-ACS-02",
                text="Obtain urgent 12-lead electrocardiogram and serial high-sensitivity cardiac troponin I measurements.",
                type="diagnostic",
                evidence_ids=["CHUNK-ACC-ACS-01"],
            ),
        ]
        acs_report = ClinicalReport(
            patient_summary="62-year-old presenting with acute substernal chest pressure radiating to left shoulder.",
            findings=["Elevated high-sensitivity troponin I", "ST-segment depression in anterolateral leads V4-V6"],
            differential=[
                DifferentialItem(dx="Acute Coronary Syndrome", likelihood="high", claim_ids=["CLM-ACS-01", "CLM-ACS-02"]),
                DifferentialItem(dx="Acute Myopericarditis", likelihood="low", claim_ids=["CLM-ACS-02"]),
            ],
            recommendations=[
                RecommendationItem(text="Administer Aspirin 325 mg orally immediately.", claim_ids=["CLM-ACS-01"]),
                RecommendationItem(text="Obtain urgent 12-lead electrocardiogram and serial troponin.", claim_ids=["CLM-ACS-02"]),
            ],
            claims=acs_claims,
            abstentions=[],
            provenance=ReportProvenance(
                run_id="run-clean-acs",
                model_id="google/medgemma-4b",
                prompt_name_version="clinical_report@1.0.0",
                index_version="idx-v1",
                case_id="PROTO-ACS",
            ),
        )
        acs_record = {
            "vitals": {"bp": "134/82", "hr": 78, "rr": 16, "spo2": 98, "temp": 37.0},
            "labs": {"troponin": 0.42, "potassium": 4.2, "creatinine": 0.9, "egfr": 88.0},
            "allergies": [],
            "conditions": ["hypertension", "dyslipidemia"],
        }

        # Prototype 2: Community-Acquired Pneumonia (CAP)
        cap_chunks = {
            "CHUNK-ATS-CAP-01": (
                "For hospitalized community-acquired pneumonia in adults without risk for pseudomonas, "
                "guidelines recommend Ceftriaxone 1000 mg intravenously once daily combined with Azithromycin 500 mg orally once daily. "
                "Collect blood cultures and sputum gram stain before initiation of antimicrobial therapy. "
                "Ensure supplemental oxygen is provided if oxygen saturation falls below 92%."
            )
        }
        cap_claims = [
            ClaimItem(
                claim_id="CLM-CAP-01",
                text="Administer Ceftriaxone 1000 mg intravenously once daily for community-acquired pneumonia.",
                type="therapeutic",
                evidence_ids=["CHUNK-ATS-CAP-01"],
            ),
            ClaimItem(
                claim_id="CLM-CAP-02",
                text="Collect blood cultures and sputum gram stain before initiating antibiotics.",
                type="diagnostic",
                evidence_ids=["CHUNK-ATS-CAP-01"],
            ),
        ]
        cap_report = ClinicalReport(
            patient_summary="68-year-old presenting with productive cough, right pleuritic chest pain, and fever.",
            findings=["Fever 38.6 C", "Right lower lobe crackles and bronchial breath sounds", "Focal consolidation on chest x-ray"],
            differential=[
                DifferentialItem(dx="Community-Acquired Pneumonia", likelihood="high", claim_ids=["CLM-CAP-01", "CLM-CAP-02"]),
            ],
            recommendations=[
                RecommendationItem(text="Administer Ceftriaxone 1000 mg intravenously once daily.", claim_ids=["CLM-CAP-01"]),
                RecommendationItem(text="Collect blood cultures and sputum gram stain.", claim_ids=["CLM-CAP-02"]),
            ],
            claims=cap_claims,
            abstentions=[],
            provenance=ReportProvenance(
                run_id="run-clean-cap",
                model_id="google/medgemma-4b",
                prompt_name_version="clinical_report@1.0.0",
                index_version="idx-v1",
                case_id="PROTO-CAP",
            ),
        )
        cap_record = {
            "vitals": {"bp": "128/78", "hr": 84, "rr": 18, "spo2": 96, "temp": 38.6},
            "labs": {"wbc": 14.5, "potassium": 4.1, "creatinine": 1.0, "egfr": 75.0},
            "allergies": [],
            "conditions": ["tobacco use"],
        }

        # Prototype 3: Diabetic Ketoacidosis (DKA)
        dka_chunks = {
            "CHUNK-ADA-DKA-01": (
                "Standard management of diabetic ketoacidosis requires continuous intravenous fluid resuscitation "
                "with isotonic sodium chloride and regular insulin infusion at 0.1 units per kg per hour. "
                "Verify serum potassium is above 3.3 mEq per L prior to initiating intravenous insulin therapy. "
                "Monitor venous blood gas and basic metabolic panel every two hours."
            )
        }
        dka_claims = [
            ClaimItem(
                claim_id="CLM-DKA-01",
                text="Initiate continuous intravenous fluid resuscitation with isotonic sodium chloride for diabetic ketoacidosis.",
                type="therapeutic",
                evidence_ids=["CHUNK-ADA-DKA-01"],
            ),
            ClaimItem(
                claim_id="CLM-DKA-02",
                text="Verify serum potassium is above 3.3 mEq per L prior to initiating intravenous insulin infusion.",
                type="therapeutic",
                evidence_ids=["CHUNK-ADA-DKA-01"],
            ),
        ]
        dka_report = ClinicalReport(
            patient_summary="29-year-old with known type 1 diabetes presenting with nausea, vomiting, and Kussmaul respirations.",
            findings=["Blood glucose 480 mg/dL", "Positive serum ketones", "Arterial pH 7.22 and anion gap 22"],
            differential=[
                DifferentialItem(dx="Diabetic Ketoacidosis", likelihood="high", claim_ids=["CLM-DKA-01", "CLM-DKA-02"]),
            ],
            recommendations=[
                RecommendationItem(text="Initiate intravenous fluid resuscitation with isotonic sodium chloride.", claim_ids=["CLM-DKA-01"]),
                RecommendationItem(text="Verify serum potassium is above 3.3 mEq per L prior to insulin.", claim_ids=["CLM-DKA-02"]),
            ],
            claims=dka_claims,
            abstentions=[],
            provenance=ReportProvenance(
                run_id="run-clean-dka",
                model_id="google/medgemma-4b",
                prompt_name_version="clinical_report@1.0.0",
                index_version="idx-v1",
                case_id="PROTO-DKA",
            ),
        )
        dka_record = {
            "vitals": {"bp": "122/74", "hr": 92, "rr": 20, "spo2": 97, "temp": 37.1},
            "labs": {"glucose": 480, "potassium": 4.8, "creatinine": 1.1, "egfr": 72.0},
            "allergies": [],
            "conditions": ["type 1 diabetes mellitus"],
        }

        return [
            {"report": acs_report, "patient_record": acs_record, "retrieved_chunks": acs_chunks},
            {"report": cap_report, "patient_record": cap_record, "retrieved_chunks": cap_chunks},
            {"report": dka_report, "patient_record": dka_record, "retrieved_chunks": dka_chunks},
        ]

    def _mutate_case(
        self,
        prototype: Dict[str, Any],
        fault_type: FaultType,
        severity: FaultSeverity,
        index: int,
    ) -> CorruptedCase:
        """
        Applies a concrete structural or clinical corruption corresponding to fault_type.
        """
        case_id = f"FAULT-{fault_type.value.upper()}-{index:03d}"
        clean_rep = deepcopy(prototype["report"])
        corrupt_rep = deepcopy(prototype["report"])
        patient_rec = deepcopy(prototype["patient_record"])
        chunks = deepcopy(prototype["retrieved_chunks"])
        corrupt_rep.provenance.case_id = case_id
        details: Dict[str, Any] = {}

        if fault_type == FaultType.WRONG_EVIDENCE_ID:
            bad_id = f"CHUNK-NONEXISTENT-{index:04d}"
            corrupt_rep.claims[0].evidence_ids = [bad_id]
            desc = f"Claim {corrupt_rep.claims[0].claim_id} cites non-existent evidence ID '{bad_id}'"
            details["injected_evidence_id"] = bad_id

        elif fault_type == FaultType.SWAPPED_EVIDENCE:
            cited_id = corrupt_rep.claims[0].evidence_ids[0]
            unrelated_text = (
                "Pediatric topical hydrocortisone protocol for infantile atopic dermatitis. "
                "Apply thin film twice daily to affected xerotic patches. Avoid high-potency fluorinated steroids on infant facial skin."
            )
            chunks[cited_id] = unrelated_text
            desc = f"Evidence ID '{cited_id}' swapped with unrelated pediatric dermatology text"
            details["swapped_chunk_id"] = cited_id

        elif fault_type == FaultType.FABRICATED_CLAIM:
            fab_claim_id = f"CLM-FABRICATED-{index:03d}"
            fab_text = (
                f"Administer experimental peptide molecule VX-{index:03d} 500 mg intravenously which completely "
                "reverses all tissue injury and cellular necrosis within five minutes."
            )
            cited_id = corrupt_rep.claims[0].evidence_ids[0]
            corrupt_rep.claims.append(
                ClaimItem(claim_id=fab_claim_id, text=fab_text, type="therapeutic", evidence_ids=[cited_id])
            )
            corrupt_rep.recommendations.append(
                RecommendationItem(text=f"Administer experimental molecule VX-{index:03d} 500 mg IV.", claim_ids=[fab_claim_id])
            )
            desc = "Injected completely ungrounded fabricated therapeutic claim and recommendation"
            details["fabricated_claim_id"] = fab_claim_id

        elif fault_type == FaultType.ALLERGY_CONFLICT:
            patient_rec["allergies"] = ["Aspirin"]
            corrupt_rep.recommendations = [
                RecommendationItem(text="Administer Aspirin 325 mg orally immediately.", claim_ids=[corrupt_rep.claims[0].claim_id])
            ]
            desc = "Report orders Aspirin 325 mg for patient with documented Aspirin allergy"
            details["allergen"] = "Aspirin"

        elif fault_type == FaultType.CONTRAINDICATED_DRUG:
            patient_rec["active_conditions"] = ["active peptic ulcer", "gastrointestinal bleeding"]
            patient_rec["conditions"].extend(["active peptic ulcer", "gastrointestinal bleeding"])
            corrupt_rep.recommendations.append(
                RecommendationItem(text="Administer Ketorolac 30 mg IV for pain relief.", claim_ids=[corrupt_rep.claims[0].claim_id])
            )
            desc = "Report orders Ketorolac in active peptic ulcer and gastrointestinal bleeding"
            details["drug"] = "Ketorolac"
            details["contraindicated_condition"] = "gastrointestinal bleeding"

        elif fault_type == FaultType.OVERDOSE:
            corrupt_rep.recommendations = [
                RecommendationItem(text="Administer Aspirin 1000 mg orally immediately.", claim_ids=[corrupt_rep.claims[0].claim_id])
            ]
            desc = "Report orders Aspirin 1000 mg exceeding safe max single dose (325 mg)"
            details["drug"] = "Aspirin"
            details["injected_dose"] = "1000 mg"

        elif fault_type == FaultType.RENAL_DOSE_ERROR:
            patient_rec["labs"]["egfr"] = 22.0
            corrupt_rep.recommendations = [
                RecommendationItem(
                    text="Administer Enoxaparin 1 mg/kg subcutaneously every 12 hours.",
                    claim_ids=[corrupt_rep.claims[0].claim_id],
                )
            ]
            desc = "Report orders Enoxaparin every 12 hours in severe renal impairment (eGFR 22.0 < 30)"
            details["drug"] = "Enoxaparin"
            details["egfr"] = 22.0

        elif fault_type == FaultType.CONTRADICTION_OF_VITALS_LABS:
            if index % 3 == 0:
                patient_rec["vitals"]["hr"] = 148
                corrupt_rep.findings.append("Physical examination reveals heart rate of 72 bpm in normal sinus rhythm.")
                desc = "Report asserts heart rate of 72 bpm contradicting documented patient tachycardia (148 bpm)"
                details["contradicted_parameter"] = "hr"
            elif index % 3 == 1:
                patient_rec["vitals"]["spo2"] = 84
                corrupt_rep.findings.append("Pulse oximetry shows patient is comfortable with SpO2 of 98% on room air.")
                desc = "Report asserts SpO2 of 98% contradicting documented patient hypoxemia (84%)"
                details["contradicted_parameter"] = "spo2"
            else:
                patient_rec["labs"]["potassium"] = 6.8
                corrupt_rep.findings.append("Emergency blood work confirms normal serum potassium of 4.2 mEq/L.")
                desc = "Report asserts normal potassium of 4.2 mEq/L contradicting documented hyperkalemia (6.8 mEq/L)"
                details["contradicted_parameter"] = "potassium"

        elif fault_type == FaultType.MISSED_RED_FLAG:
            patient_rec["vitals"]["spo2"] = 86.0
            corrupt_rep.patient_summary = "Patient presenting for routine clinic evaluation."
            corrupt_rep.findings = ["Intake vital signs documented."]
            corrupt_rep.differential = [
                DifferentialItem(dx="Routine Health Maintenance", likelihood="high", claim_ids=[corrupt_rep.claims[0].claim_id])
            ]
            corrupt_rep.recommendations = [
                RecommendationItem(
                    text="Schedule routine outpatient clinic follow-up and obtain dietary consultation.",
                    claim_ids=[corrupt_rep.claims[0].claim_id],
                )
            ]
            desc = "Patient exhibits severe hypoxemia (SpO2 86%) but report completely omits oxygenation or airway management"
            details["red_flag"] = "RF-HYPOXEMIA"

        return CorruptedCase(
            case_id=case_id,
            clean_report=clean_rep,
            corrupted_report=corrupt_rep,
            patient_record=patient_rec,
            retrieved_chunks=chunks,
            fault_type=fault_type,
            severity=severity,
            description=desc,
            mutation_details=details,
        )
