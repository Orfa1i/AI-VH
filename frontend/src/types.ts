export interface VitalSigns {
  timestamp: string;
  heart_rate: number;
  systolic_bp: number;
  diastolic_bp: number;
  respiratory_rate: number;
  temperature_c: number;
  spo2_percent: number;
  pain_score: number;
}

export interface LabResult {
  test_type: string;
  values: Record<string, any>;
  abnormal_flags: Record<string, boolean>;
  interpretation: string;
}

export interface DifferentialItem {
  condition: string;
  likelihood: number;
  supporting_points: string[];
  opposing_points: string[];
}

export interface MedicalCitation {
  id: string;
  book: string;
  chapter: string;
  topic: string;
  page: number;
  specialty: string;
  text: string;
  relevance_score?: number;
}

export interface ClinicalReport {
  id: string;
  encounter_id: string;
  patient_id: string;
  patient_name: string;
  patient_age: number;
  patient_sex: string;
  created_at: string;
  chief_complaint: string;
  history_of_present_illness: string;
  past_medical_history: string[];
  medications: string[];
  allergies: string[];
  vital_signs: VitalSigns;
  physical_exam_findings: Record<string, string>;
  investigations_ordered: string[];
  investigation_results: LabResult[];
  differential_diagnosis: DifferentialItem[];
  primary_diagnosis: string;
  diagnostic_confidence: number;
  clinical_reasoning: string;
  treatment_plan: string[];
  recommended_disposition: string;
  medical_knowledge_citations: MedicalCitation[];
}

export interface HospitalEvent {
  id: string;
  event_type: string;
  timestamp: string;
  encounter_id: string;
  patient_id: string;
  sender_agent_id: string;
  receiver_agent_id?: string;
  department: string;
  payload: Record<string, any>;
  summary: string;
}

export interface BenchmarkCase {
  id: string;
  name: string;
  age: number;
  sex: string;
  chief_complaint: string;
  acuity: string;
}

export interface SpecialistConsultResponse {
  specialist: string;
  specialty: string;
  domain: string;
  evidence_brief: {
    query: string;
    domain: string;
    clinical_summary: string;
    recommended_workup: string[];
    recommended_therapy: string[];
    contraindications: string[];
    citations: MedicalCitation[];
  };
  recommendations: {
    immediate_workup: string[];
    guideline_therapy: string[];
    contraindications: string[];
  };
  citations: MedicalCitation[];
}

export interface PhysicianReviewPayload {
  report_id: string;
  physician_name: string;
  diagnosis_grade: string;
  reasoning_grade: string;
  tests_grade: string;
  treatment_grade: string;
  overall_score: number;
  approved: boolean;
  notes: string;
  corrected_diagnosis?: string;
}
