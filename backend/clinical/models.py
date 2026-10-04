"""
Clinical Data Models & Schemas
Contains all patient, vital, investigation, diagnosis, report, and physician feedback models.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TriageAcuity(str, Enum):
    RESUSCITATION = "LEVEL_1_RESUSCITATION"
    EMERGENT = "LEVEL_2_EMERGENT"
    URGENT = "LEVEL_3_URGENT"
    LESS_URGENT = "LEVEL_4_LESS_URGENT"
    NON_URGENT = "LEVEL_5_NON_URGENT"


class VitalSigns(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    heart_rate: int = Field(..., description="Beats per minute (bpm)")
    systolic_bp: int = Field(..., description="Systolic blood pressure (mmHg)")
    diastolic_bp: int = Field(..., description="Diastolic blood pressure (mmHg)")
    respiratory_rate: int = Field(..., description="Breaths per minute")
    temperature_c: float = Field(..., description="Core body temperature in Celsius")
    spo2_percent: float = Field(..., description="Oxygen saturation percentage (%)")
    pain_score: int = Field(0, ge=0, le=10, description="Pain score (0-10)")

    def summary(self) -> str:
        return f"BP {self.systolic_bp}/{self.diastolic_bp} mmHg, HR {self.heart_rate} bpm, RR {self.respiratory_rate}/min, Temp {self.temperature_c:.1f}°C, SpO2 {self.spo2_percent}%, Pain {self.pain_score}/10"


class LabTestType(str, Enum):
    CBC = "Complete Blood Count (CBC)"
    BMP = "Basic Metabolic Panel (BMP)"
    CMP = "Comprehensive Metabolic Panel (CMP)"
    TROPONIN_I = "High-Sensitivity Troponin I"
    CK_MB = "Creatine Kinase-MB"
    ECG_12_LEAD = "12-Lead Electrocardiogram"
    D_DIMER = "D-Dimer"
    BNP = "B-type Natriuretic Peptide (BNP)"
    LIPID_PANEL = "Lipid Panel"
    LFT = "Liver Function Tests"
    ABG = "Arterial Blood Gas (ABG)"
    LACTATE = "Serum Lactate"
    URINALYSIS = "Urinalysis"
    CXR = "Chest X-Ray (PA & Lateral)"
    CT_CHEST = "CT Chest Angiography"


class LabResult(BaseModel):
    test_type: LabTestType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    values: Dict[str, Any]
    reference_ranges: Dict[str, str] = Field(default_factory=dict)
    abnormal_flags: Dict[str, bool] = Field(default_factory=dict)
    interpretation: str = ""


class DifferentialItem(BaseModel):
    condition: str
    likelihood: float = Field(..., ge=0.0, le=1.0)
    supporting_points: List[str] = Field(default_factory=list)
    opposing_points: List[str] = Field(default_factory=list)


class ClinicalReport(BaseModel):
    id: str
    encounter_id: str
    patient_id: str
    patient_name: str
    patient_age: int
    patient_sex: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Subjective
    chief_complaint: str
    history_of_present_illness: str
    past_medical_history: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    
    # Objective
    vital_signs: VitalSigns
    physical_exam_findings: Dict[str, str] = Field(default_factory=dict)
    investigations_ordered: List[LabTestType] = Field(default_factory=list)
    investigation_results: List[LabResult] = Field(default_factory=list)
    
    # Assessment & Plan
    differential_diagnosis: List[DifferentialItem] = Field(default_factory=list)
    primary_diagnosis: str
    diagnostic_confidence: float = Field(..., ge=0.0, le=1.0)
    clinical_reasoning: str
    treatment_plan: List[str] = Field(default_factory=list)
    recommended_disposition: str = "Admit to Internal Medicine / Observation"
    
    # Evidence & Citations
    medical_knowledge_citations: List[Dict[str, Any]] = Field(default_factory=list)

    # Grounding provenance (Phase 2 fail-safe): True when this report fell back
    # to a legacy/ungrounded path after a grounded attempt failed. Ungrounded
    # reports are displayed as such and permanently excluded from RL export.
    ungrounded: bool = False

    # Pharmacy & Medication Safety Review (Phase 7)
    pharmacist_review: Optional['MedicationSafetyReport'] = None


class MedicationSafetyReport(BaseModel):
    id: str
    encounter_id: str
    patient_id: str
    patient_name: str
    pharmacist_name: str = "Dr. Elena Rostova, PharmD, BCPS"
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    prescriptions_reviewed: List[str] = Field(default_factory=list)
    safety_cleared: bool = True
    approved_medications: List[str] = Field(default_factory=list)
    flagged_contraindications: List[str] = Field(default_factory=list)
    renal_adjustments: List[str] = Field(default_factory=list)
    allergy_warnings: List[str] = Field(default_factory=list)
    clinical_interventions: List[str] = Field(default_factory=list)
    dispensing_status: str = "READY_FOR_ADMINISTRATION"



class DiagnosisFeedback(str, Enum):
    CORRECT = "CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"


class ReasoningFeedback(str, Enum):
    SOUND = "SOUND"
    MISSING_CRITICAL_EVIDENCE = "MISSING_CRITICAL_EVIDENCE"
    FAULTY_LOGIC = "FAULTY_LOGIC"
    UNSUPPORTED_CONCLUSION = "UNSUPPORTED_CONCLUSION"


class TestAppropriatenessFeedback(str, Enum):
    APPROPRIATE = "APPROPRIATE"
    OVER_ORDERING = "OVER_ORDERING"
    MISSING_ESSENTIAL_TEST = "MISSING_ESSENTIAL_TEST"
    INAPPROPRIATE_TEST = "INAPPROPRIATE_TEST"

TestAppropriatenessFeedback.__test__ = False  # type: ignore[attr-defined]


class TreatmentSafetyFeedback(str, Enum):
    SAFE_AND_OPTIMAL = "SAFE_AND_OPTIMAL"
    SUBOPTIMAL = "SUBOPTIMAL"
    CONTRAINDICATED_OR_HARMFUL = "CONTRAINDICATED_OR_HARMFUL"


class PhysicianReview(BaseModel):
    id: str
    report_id: str
    encounter_id: str
    physician_name: str = "Attending Physician, MD"
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Structured ratings
    diagnosis_grade: DiagnosisFeedback
    reasoning_grade: ReasoningFeedback
    tests_grade: TestAppropriatenessFeedback
    treatment_grade: TreatmentSafetyFeedback
    overall_score: int = Field(..., ge=1, le=5, description="1 (Dangerous) to 5 (Exemplary)")
    
    # Corrective annotations
    approved: bool
    corrected_diagnosis: Optional[str] = None
    corrected_treatment: Optional[List[str]] = None
    physician_feedback_notes: str
