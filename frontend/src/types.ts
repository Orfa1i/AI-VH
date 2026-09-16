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
  pharmacist_review?: MedicationSafetyReport;
}

export interface MedicationSafetyReport {
  id: string;
  encounter_id: string;
  patient_id: string;
  patient_name: string;
  pharmacist_name: string;
  reviewed_at: string;
  prescriptions_reviewed: string[];
  safety_cleared: boolean;
  approved_medications: string[];
  flagged_contraindications: string[];
  renal_adjustments: string[];
  allergy_warnings: string[];
  clinical_interventions: string[];
  dispensing_status: string;
}

export interface ProximityStation {
  id: string;
  name: string;
  role: string;
  position: [number, number, number];
  prompt: string;
  badge: string;
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

export interface DPOPreferencePair {
  id: string;
  encounter_id: string;
  case_id: string;
  source: string;
  prompt: string;
  chosen: string;
  rejected: string;
  reward_chosen: number;
  reward_rejected: number;
  reward_margin: number;
  is_safety_critical: boolean;
  harrison_citations: string[];
  metadata: Record<string, any>;
  created_at: string;
}

export interface DPOStatistics {
  total_pairs: number;
  human_reviews_count: number;
  benchmark_calibrations_count: number;
  safety_critical_count: number;
  average_reward_margin: number;
  average_chosen_reward: number;
  average_rejected_reward: number;
}

export interface DPOApiResponse {
  statistics: DPOStatistics;
  pairs: DPOPreferencePair[];
}

export interface PatientRecord {
  id: string;
  mrn: string;
  name: string;
  age: number;
  sex: string;
  triage_acuity: string;
  chief_complaint: string;
  history_of_present_illness?: string;
  past_medical_history?: string[];
  medications?: string[];
  allergies?: string[];
  baseline_vitals?: Record<string, any>;
  admission_status: 'ADMITTED' | 'IN_ENCOUNTER' | 'DISCHARGED';
  assigned_department: string;
  bed_number?: string;
  admitted_at: string;
  case_data?: Record<string, any>;
}

export interface HospitalStaffRecord {
  id: string;
  name: string;
  role: 'DOCTOR' | 'NURSE' | 'PHARMACIST' | 'RADIOLOGIST' | 'LAB_SCIENTIST' | 'RECEPTIONIST';
  specialty: string;
  title: string;
  department: string;
  status: 'ON_DUTY' | 'IN_CONSULT' | 'OFF_DUTY';
  credentials: string;
  bio: string;
  system_prompt?: string;
  avatar_url?: string;
  assigned_patients?: string[];
  total_encounters: number;
  created_at?: string;
}


