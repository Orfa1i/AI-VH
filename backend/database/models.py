"""
AI Virtual Hospital - Relational Database Record Models
Maps clinical models from docs/06-data-architecture.md into typed database representations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ClinicalReportRecord(BaseModel):
    id: str
    encounter_id: str
    case_id: str
    patient_name: str
    age: int
    sex: str
    primary_diagnosis: str
    differential_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    ordered_investigations: List[str] = Field(default_factory=list)
    investigation_results: List[Dict[str, Any]] = Field(default_factory=list)
    treatment_plan: List[str] = Field(default_factory=list)
    clinical_reasoning: str
    confidence_score: float = 0.85
    specialist_recommendations: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PhysicianReviewRecord(BaseModel):
    id: str
    report_id: str
    encounter_id: str
    physician_name: str
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    diagnosis_grade: str
    reasoning_grade: str
    tests_grade: str
    treatment_grade: str
    overall_score: int
    approved: bool
    corrected_diagnosis: Optional[str] = None
    corrected_treatment: Optional[List[str]] = None
    physician_feedback_notes: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DPOFeedbackRecord(BaseModel):
    id: str
    prompt: str
    chosen: str
    rejected: str
    reward_margin: float = 1.0
    is_safety_critical: bool = False
    citations: List[str] = Field(default_factory=list)
    source: str = "HUMAN_PHYSICIAN"
    encounter_id: Optional[str] = None
    case_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeChunkRecord(BaseModel):
    id: str
    specialty: str
    book_title: str
    chapter: str
    topic: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EncounterRecord(BaseModel):
    encounter_id: str
    case_id: str
    patient_name: str
    status: str
    current_department: str
    report_id: Optional[str] = None
    review_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PatientRecord(BaseModel):
    id: str
    mrn: str
    name: str
    age: int
    sex: str
    triage_acuity: str
    chief_complaint: str
    history_of_present_illness: str
    past_medical_history: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    baseline_vitals: Dict[str, Any] = Field(default_factory=dict)
    admission_status: str = "ADMITTED"  # ADMITTED, IN_ENCOUNTER, DISCHARGED
    assigned_department: str = "EMERGENCY"
    bed_number: Optional[str] = None
    admitted_at: datetime = Field(default_factory=datetime.utcnow)
    raw_case_data: Dict[str, Any] = Field(default_factory=dict)


class HospitalStaffRecord(BaseModel):
    id: str
    name: str
    role: str  # DOCTOR, NURSE, PHARMACIST, RADIOLOGIST, LAB_SCIENTIST, RECEPTIONIST
    specialty: str
    title: str
    department: str
    status: str = "ON_DUTY"  # ON_DUTY, IN_CONSULT, OFF_DUTY
    credentials: str
    bio: str
    system_prompt: Optional[str] = None
    assigned_patients: List[str] = Field(default_factory=list)
    total_encounters: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeSourceRecord(BaseModel):
    id: str
    name: str
    url: str
    description: str = ""
    status: str = "ACTIVE"  # ACTIVE, INACTIVE, SYNCING, ERROR
    source_type: str = "CUSTOM"  # PUBMED, OPENFDA, RXNORM, CUSTOM
    last_synced_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


