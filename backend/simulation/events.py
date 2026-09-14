"""
Hospital Simulation Events
Defines all event types, payloads, and timestamps used across the hospital simulation bus.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EventType(str, Enum):
    # Lifecycle & Patient Entry
    PATIENT_ARRIVED = "PATIENT_ARRIVED"
    NURSE_TRIAGE_STARTED = "NURSE_TRIAGE_STARTED"
    VITALS_RECORDED = "VITALS_RECORDED"
    TRIAGE_COMPLETED = "TRIAGE_COMPLETED"
    
    # Doctor Encounter & Clinical Reasoning
    DOCTOR_ASSIGNED = "DOCTOR_ASSIGNED"
    EXAMINATION_STARTED = "EXAMINATION_STARTED"
    PATIENT_INTERVIEWED = "PATIENT_INTERVIEWED"
    DIFFERENTIAL_UPDATED = "DIFFERENTIAL_UPDATED"
    
    # Knowledge & RAG
    RAG_QUERY_INITIATED = "RAG_QUERY_INITIATED"
    RAG_KNOWLEDGE_RETRIEVED = "RAG_KNOWLEDGE_RETRIEVED"
    
    # Investigations
    LAB_ORDERED = "LAB_ORDERED"
    LAB_SAMPLE_COLLECTED = "LAB_SAMPLE_COLLECTED"
    LAB_RESULT_READY = "LAB_RESULT_READY"
    IMAGING_ORDERED = "IMAGING_ORDERED"
    IMAGING_RESULT_READY = "IMAGING_RESULT_READY"
    
    # Synthesis & Disposition
    DIAGNOSIS_MADE = "DIAGNOSIS_MADE"
    TREATMENT_ORDERED = "TREATMENT_ORDERED"
    CLINICAL_REPORT_GENERATED = "CLINICAL_REPORT_GENERATED"
    
    # Physician Review & Feedback
    PHYSICIAN_REVIEW_SUBMITTED = "PHYSICIAN_REVIEW_SUBMITTED"
    ENCOUNTER_CLOSED = "ENCOUNTER_CLOSED"
    
    # Pharmacy & Medication Safety
    PHARMACY_REVIEW_INITIATED = "PHARMACY_REVIEW_INITIATED"
    PHARMACY_REVIEW_COMPLETED = "PHARMACY_REVIEW_COMPLETED"
    MEDICATION_DISPENSED = "MEDICATION_DISPENSED"
    
    # 3D Spatial & Movement Events
    AGENT_MOVED = "AGENT_MOVED"
    DEPARTMENT_STATUS_CHANGED = "DEPARTMENT_STATUS_CHANGED"


class HospitalEvent(BaseModel):
    id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    encounter_id: str
    patient_id: str
    sender_agent_id: str
    receiver_agent_id: Optional[str] = None
    department: str = "EMERGENCY_DEPARTMENT"
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "sender_agent_id": self.sender_agent_id,
            "receiver_agent_id": self.receiver_agent_id,
            "department": self.department,
            "payload": self.payload,
            "summary": self.summary,
        }
