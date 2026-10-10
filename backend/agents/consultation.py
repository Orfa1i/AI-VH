"""
Dynamic Multi-Agent Consultation Engine for AI Virtual Hospital (AI-VH).
Coordinates secondary specialist consultations with safety guardrails:
- Configurable maximum specialist limit
- Circular referral prevention (DAG cycle breaker)
- Duplicate-consultation protection
- Per-consult async timeout enforcement
- Explicit clinical disagreement identification
- Immutable Emergency Red Flag escalation (never suppressible)
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger("ConsultationEngine")


class ConsultationFinding(BaseModel):
    specialty: str
    specialist_name: str
    primary_diagnosis: str
    confidence: float
    differential: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_reasoning: str = ""
    treatment_recommendations: List[str] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    is_emergency: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ClinicalDisagreement(BaseModel):
    issue_type: str  # "DIAGNOSTIC_DISAGREEMENT", "TREATMENT_CONFLICT", "PRIORITY_DISPUTE"
    primary_view: str
    consultant_view: str
    clinical_impact: str
    resolution_guidance: str


class MultiAgentConsultationRecord(BaseModel):
    encounter_id: str
    primary_specialty: str
    consulted_specialties: List[str] = Field(default_factory=list)
    consultation_findings: Dict[str, ConsultationFinding] = Field(default_factory=dict)
    disagreements: List[ClinicalDisagreement] = Field(default_factory=list)
    emergency_red_flags: List[str] = Field(default_factory=list)
    is_emergency_escalated: bool = False
    blocked_circular_referrals: List[str] = Field(default_factory=list)
    total_consultations: int = 0
    status: str = "COMPLETED"


class ConsultationEngine:
    """
    Controlled Dynamic Multi-Agent Consultation Engine.
    Executes and reconciles secondary specialist consultations safely.
    """

    # Clinical triggers mapping findings to relevant secondary specialties
    CONSULTATION_TRIGGERS = {
        "SURGERY": [
            "acute abdomen", "appendicitis", "rebound tenderness", "guarding", "peritonitis",
            "perforation", "cholecystitis", "bowel obstruction", "hematoma", "surgical", "hernia"
        ],
        "CARDIOLOGY": [
            "troponin", "stemi", "nstemi", "chest pain", "ecg", "st elevation", "cardiogenic",
            "arrhythmia", "heart failure", "chf", "bnp", "impella", "cath lab"
        ],
        "NEUROLOGY": [
            "stroke", "facial droop", "aphasia", "hemiparesis", "seizure", "pres",
            "headache with visual", "scotoma", "nihss", "thrombectomy", "tenecteplase"
        ],
        "GYNECOLOGY": [
            "adnexal mass", "pelvic mass", "ovarian torsion", "abnormal uterine bleeding",
            "aub", "pelvic pain", "ectopic", "ovarian cyst"
        ],
        "OBSTETRICS": [
            "pregnancy", "pregnant", "gestational", "preeclampsia", "hellp", "fetal",
            "eclampsia", "postpartum", "amniotic", "placenta"
        ],
        "INFECTIOUS_DISEASES": [
            "bacteremia", "mrsa", "endocarditis", "septic shock", "fever of unknown origin",
            "vancomycin", "refractory fever", "blood cultures positive"
        ],
        "EMERGENCY": [
            "resuscitation", "shock", "hypotension", "anaphylaxis", "airway", "intubation",
            "stridor", "rapid sequence", "pressors", "map < 65"
        ],
    }

    EMERGENCY_KEYWORDS = [
        "stemi", "cardiogenic shock", "large vessel occlusion", "stroke within window",
        "nihss > 15", "septic shock", "eclampsia", "severe hellp", "aortic dissection",
        "acute abdomen with peritonitis", "anaphylactic shock", "cardiac arrest"
    ]

    def __init__(self, max_consultations: int = 2, timeout: float = 30.0):
        self.max_consultations = max_consultations
        self.timeout = timeout

    def determine_indicated_consultations(
        self,
        primary_specialty: str,
        patient_data: Dict[str, Any],
        initial_diagnosis: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Determines which secondary specialties are clinically justified.
        Never invokes every specialist for every case; strictly clinically indicated.
        """
        indicated: List[str] = []
        text = (
            f"{patient_data.get('chief_complaint', '')} "
            f"{patient_data.get('history_of_present_illness', '')} "
            f"{initial_diagnosis} "
            f"{' '.join(abnormal_labs or [])}"
        ).lower()

        primary_norm = primary_specialty.upper().replace(" ", "_")

        for specialty, keywords in self.CONSULTATION_TRIGGERS.items():
            if specialty == primary_norm:
                continue
            if any(k in text for k in keywords):
                indicated.append(specialty)

        # Cap candidates to max_consultations
        return indicated[:self.max_consultations]

    def check_circular_referral(
        self,
        requested_specialty: str,
        consultation_path: List[str],
    ) -> bool:
        """
        Prevents circular referrals: if specialty was already in the path, block it.
        E.g. A -> B -> A is rejected.
        """
        req_norm = requested_specialty.upper().replace(" ", "_")
        return req_norm in [s.upper().replace(" ", "_") for s in consultation_path]

    def scan_emergency_red_flags(self, text: str) -> List[str]:
        """Detects critical emergency red flags."""
        flags = []
        t_low = text.lower()
        for kw in self.EMERGENCY_KEYWORDS:
            if kw in t_low:
                flags.append(f"CRITICAL RED FLAG: {kw.upper()}")
        return flags

    def identify_disagreements(
        self,
        primary_finding: Dict[str, Any],
        consultant_finding: Dict[str, Any],
    ) -> List[ClinicalDisagreement]:
        """Compares primary and consultant assessments to extract diagnostic disagreements."""
        disagreements = []
        prim_dx = str(primary_finding.get("primary_diagnosis", "")).lower()
        cons_dx = str(consultant_finding.get("primary_diagnosis", "")).lower()

        # Check for diagnostic divergence
        if prim_dx and cons_dx and prim_dx != cons_dx:
            stopwords = {"with", "of", "and", "in", "the", "a", "an", "or", "for", "due", "to", "at", "by", "from"}
            prim_tokens = {t.strip(".,;:()") for t in prim_dx.split()} - stopwords
            cons_tokens = {t.strip(".,;:()") for t in cons_dx.split()} - stopwords
            overlap = prim_tokens.intersection(cons_tokens)
            
            # If the primary medical tokens diverge (no substantive clinical overlap)
            if len(overlap) == 0 or len(overlap) / max(1, len(prim_tokens)) < 0.5:
                disagreements.append(ClinicalDisagreement(
                    issue_type="DIAGNOSTIC_DISAGREEMENT",
                    primary_view=primary_finding.get("primary_diagnosis", ""),
                    consultant_view=consultant_finding.get("primary_diagnosis", ""),
                    clinical_impact="Divergent diagnostic hypotheses require multi-disciplinary reconciliation prior to definitive treatment.",
                    resolution_guidance="Review shared objective laboratory and imaging markers with the Clinical Synthesis Engine."
                ))

        return disagreements


    async def execute_consultation(
        self,
        specialist_agent: Any,
        encounter_id: str,
        patient_id: str,
        clinical_scenario: str,
        abnormal_labs: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Executes a single specialist consultation with strict timeout protection."""
        try:
            return await asyncio.wait_for(
                specialist_agent.conduct_specialist_consultation(
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    clinical_scenario=clinical_scenario,
                    abnormal_labs=abnormal_labs,
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"Consultation timed out after {self.timeout}s for specialist {getattr(specialist_agent, 'name', 'Specialist')}")
            return None
        except Exception as e:
            logger.error(f"Consultation execution error for {getattr(specialist_agent, 'name', 'Specialist')}: {e}", exc_info=True)
            return None

    async def coordinate_consultations(
        self,
        encounter_id: str,
        primary_specialty: str,
        patient_data: Dict[str, Any],
        primary_finding: Dict[str, Any],
        specialist_registry: Dict[str, Any],
        abnormal_labs: Optional[List[str]] = None,
    ) -> MultiAgentConsultationRecord:
        """
        Coordinates multi-specialist consultation workflow:
        1. Checks for emergency red flags in patient presentation & primary assessment.
        2. Detects clinically indicated secondary specialties.
        3. Enforces circular referral checks, duplicate prevention, and maximum consultation limits.
        4. Invokes secondary specialists with timeouts.
        5. Identifies clinical disagreements between primary specialist and consultants.
        6. Locks emergency safety escalation if any consultant or primary flag detected.
        """
        record = MultiAgentConsultationRecord(
            encounter_id=encounter_id,
            primary_specialty=primary_specialty,
        )

        # 1. Scan primary text & data for emergency red flags
        combined_text = (
            f"{patient_data.get('chief_complaint', '')} "
            f"{patient_data.get('history_of_present_illness', '')} "
            f"{primary_finding.get('primary_diagnosis', '')} "
            f"{' '.join(abnormal_labs or [])}"
        )
        record.emergency_red_flags.extend(self.scan_emergency_red_flags(combined_text))
        if record.emergency_red_flags:
            record.is_emergency_escalated = True

        # 2. Determine indicated specialties
        indicated = self.determine_indicated_consultations(
            primary_specialty=primary_specialty,
            patient_data=patient_data,
            initial_diagnosis=primary_finding.get("primary_diagnosis", ""),
            abnormal_labs=abnormal_labs,
        )

        consultation_path = [primary_specialty]

        # 3. Controlled consultation loop
        for candidate in indicated:
            if len(record.consulted_specialties) >= self.max_consultations:
                logger.info(f"Reached max consultations limit ({self.max_consultations}). Stopping additional referrals.")
                break

            # Circular referral check
            if self.check_circular_referral(candidate, consultation_path):
                logger.warning(f"Circular referral detected and blocked: {consultation_path} -> {candidate}")
                record.blocked_circular_referrals.append(candidate)
                continue

            # Duplicate consult check
            if candidate in record.consulted_specialties:
                logger.info(f"Duplicate consultation ignored for specialty: {candidate}")
                continue

            # Resolve specialist agent from registry
            norm_key = candidate.upper().replace(" ", "_")
            agent = specialist_registry.get(norm_key) or specialist_registry.get(candidate.lower())
            if not agent:
                logger.warning(f"Specialist agent not found in registry for specialty: {candidate}")
                continue

            # Execute consultation with timeout
            clinical_scenario = (
                f"Secondary Specialist Consultation requested by {primary_specialty}. "
                f"Patient: {patient_data.get('name', 'Patient')}, {patient_data.get('age', 'Unknown')}yo {patient_data.get('sex', 'Unknown')}. "
                f"Chief Complaint: {patient_data.get('chief_complaint', 'Unspecified')}. "
                f"HPI: {patient_data.get('history_of_present_illness', 'None documented')}. "
                f"Primary Diagnosis by {primary_specialty}: {primary_finding.get('primary_diagnosis', 'None')}."
            )

            result = await self.execute_consultation(
                specialist_agent=agent,
                encounter_id=encounter_id,
                patient_id=patient_data.get("id", "PAT-CONSULT"),
                clinical_scenario=clinical_scenario,
                abnormal_labs=abnormal_labs,
            )

            if result:
                finding = ConsultationFinding(
                    specialty=candidate,
                    specialist_name=result.get("specialist_name") or getattr(agent, "name", f"{candidate} Specialist"),
                    primary_diagnosis=result.get("primary_diagnosis", "Consultation Assessment Pending"),
                    confidence=float(result.get("confidence", 0.7)),
                    differential=result.get("differential", []),
                    clinical_reasoning=result.get("clinical_reasoning", ""),
                    treatment_recommendations=result.get("treatment_recommendations", []),
                    citations=result.get("citations", []),
                    red_flags=result.get("red_flags", []),
                    is_emergency=bool(result.get("is_emergency", False)),
                )

                # Scan for emergency red flags in consultant assessment
                cons_flags = self.scan_emergency_red_flags(
                    f"{finding.primary_diagnosis} {finding.clinical_reasoning} {' '.join(finding.red_flags)}"
                )
                if cons_flags:
                    finding.is_emergency = True
                    for cf in cons_flags:
                        if cf not in record.emergency_red_flags:
                            record.emergency_red_flags.append(cf)
                    record.is_emergency_escalated = True

                # Identify clinical disagreements
                disagreements = self.identify_disagreements(
                    primary_finding=primary_finding,
                    consultant_finding=finding.model_dump(),
                )
                record.disagreements.extend(disagreements)

                record.consultation_findings[candidate] = finding
                record.consulted_specialties.append(candidate)
                consultation_path.append(candidate)
                record.total_consultations += 1

        return record


# Global singleton instance
consultation_engine = ConsultationEngine()

