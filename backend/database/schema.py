"""
AI Virtual Hospital - Database Schema & DDL
Defines table schemas for both PostgreSQL (with pgvector / JSONB) and SQLite.
Includes support for Encounters, Reports, Reviews, DPO Pairs, Knowledge Chunks,
Admitted Patients, and Hospital Staff Management.
"""

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    status TEXT NOT NULL,
    current_department TEXT NOT NULL,
    report_id TEXT,
    review_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clinical_reports (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    primary_diagnosis TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    created_at TIMESTAMP NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
);

CREATE TABLE IF NOT EXISTS physician_reviews (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    encounter_id TEXT NOT NULL,
    physician_name TEXT NOT NULL,
    overall_score INTEGER NOT NULL,
    approved BOOLEAN NOT NULL,
    reviewed_at TIMESTAMP NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES clinical_reports(id)
);

CREATE TABLE IF NOT EXISTS dpo_feedback_pairs (
    id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    chosen TEXT NOT NULL,
    rejected TEXT NOT NULL,
    reward_margin REAL NOT NULL,
    is_safety_critical BOOLEAN DEFAULT FALSE,
    source TEXT NOT NULL,
    encounter_id TEXT,
    case_id TEXT,
    raw_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id TEXT PRIMARY KEY,
    specialty TEXT NOT NULL,
    book_title TEXT NOT NULL,
    chapter TEXT NOT NULL,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    mrn TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    triage_acuity TEXT NOT NULL,
    chief_complaint TEXT NOT NULL,
    admission_status TEXT NOT NULL DEFAULT 'ADMITTED',
    assigned_department TEXT NOT NULL DEFAULT 'EMERGENCY',
    bed_number TEXT,
    admitted_at TIMESTAMP NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hospital_staff (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    specialty TEXT NOT NULL,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ON_DUTY',
    credentials TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_pool (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    triage_acuity TEXT NOT NULL,
    chief_complaint TEXT NOT NULL,
    specialty_category TEXT NOT NULL DEFAULT 'INTERNAL_MEDICINE',
    source TEXT NOT NULL DEFAULT 'SYNTHEA',
    difficulty_level INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'UNADMITTED',
    raw_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_case ON clinical_reports(case_id);
CREATE INDEX IF NOT EXISTS idx_reports_encounter ON clinical_reports(encounter_id);
CREATE INDEX IF NOT EXISTS idx_reviews_report ON physician_reviews(report_id);
CREATE INDEX IF NOT EXISTS idx_reviews_encounter ON physician_reviews(encounter_id);
CREATE INDEX IF NOT EXISTS idx_dpo_prompt ON dpo_feedback_pairs(prompt);
CREATE INDEX IF NOT EXISTS idx_knowledge_specialty ON knowledge_chunks(specialty);
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(admission_status);
CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(mrn);
CREATE INDEX IF NOT EXISTS idx_staff_role ON hospital_staff(role);
CREATE INDEX IF NOT EXISTS idx_staff_dept ON hospital_staff(department);
CREATE INDEX IF NOT EXISTS idx_pool_status ON case_pool(status);
CREATE INDEX IF NOT EXISTS idx_pool_specialty ON case_pool(specialty_category);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id VARCHAR(64) PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL,
    patient_name VARCHAR(128) NOT NULL,
    status VARCHAR(64) NOT NULL,
    current_department VARCHAR(64) NOT NULL,
    report_id VARCHAR(64),
    review_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clinical_reports (
    id VARCHAR(64) PRIMARY KEY,
    encounter_id VARCHAR(64) NOT NULL,
    case_id VARCHAR(64) NOT NULL,
    patient_name VARCHAR(128) NOT NULL,
    primary_diagnosis TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS physician_reviews (
    id VARCHAR(64) PRIMARY KEY,
    report_id VARCHAR(64) NOT NULL,
    encounter_id VARCHAR(64) NOT NULL,
    physician_name VARCHAR(128) NOT NULL,
    overall_score INTEGER NOT NULL,
    approved BOOLEAN NOT NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS dpo_feedback_pairs (
    id VARCHAR(64) PRIMARY KEY,
    prompt TEXT NOT NULL,
    chosen TEXT NOT NULL,
    rejected TEXT NOT NULL,
    reward_margin DOUBLE PRECISION NOT NULL,
    is_safety_critical BOOLEAN DEFAULT FALSE,
    source VARCHAR(64) NOT NULL,
    encounter_id VARCHAR(64),
    case_id VARCHAR(64),
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id VARCHAR(64) PRIMARY KEY,
    specialty VARCHAR(64) NOT NULL,
    book_title VARCHAR(256) NOT NULL,
    chapter VARCHAR(256) NOT NULL,
    topic VARCHAR(256) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR(64) PRIMARY KEY,
    mrn VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    age INTEGER NOT NULL,
    sex VARCHAR(16) NOT NULL,
    triage_acuity VARCHAR(32) NOT NULL,
    chief_complaint TEXT NOT NULL,
    admission_status VARCHAR(32) NOT NULL DEFAULT 'ADMITTED',
    assigned_department VARCHAR(64) NOT NULL DEFAULT 'EMERGENCY',
    bed_number VARCHAR(32),
    admitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS hospital_staff (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL,
    specialty VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,
    department VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ON_DUTY',
    credentials VARCHAR(64) NOT NULL,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_pool (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    age INTEGER NOT NULL,
    sex VARCHAR(16) NOT NULL,
    triage_acuity VARCHAR(32) NOT NULL,
    chief_complaint TEXT NOT NULL,
    specialty_category VARCHAR(64) NOT NULL DEFAULT 'INTERNAL_MEDICINE',
    source VARCHAR(64) NOT NULL DEFAULT 'SYNTHEA',
    difficulty_level INTEGER DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'UNADMITTED',
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_case ON clinical_reports(case_id);
CREATE INDEX IF NOT EXISTS idx_reports_encounter ON clinical_reports(encounter_id);
CREATE INDEX IF NOT EXISTS idx_reviews_report ON physician_reviews(report_id);
CREATE INDEX IF NOT EXISTS idx_reviews_encounter ON physician_reviews(encounter_id);
CREATE INDEX IF NOT EXISTS idx_dpo_prompt ON dpo_feedback_pairs(prompt);
CREATE INDEX IF NOT EXISTS idx_knowledge_specialty ON knowledge_chunks(specialty);
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(admission_status);
CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(mrn);
CREATE INDEX IF NOT EXISTS idx_staff_role ON hospital_staff(role);
CREATE INDEX IF NOT EXISTS idx_staff_dept ON hospital_staff(department);
CREATE INDEX IF NOT EXISTS idx_pool_status ON case_pool(status);
CREATE INDEX IF NOT EXISTS idx_pool_specialty ON case_pool(specialty_category);
"""
