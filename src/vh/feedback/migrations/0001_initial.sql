-- Migration 0001: initial append-only doctor-review feedback store (STEP 36).
-- Immutability of reports_original and audit_log is enforced by triggers
-- (database level), never only in application code.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviewers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports_original (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    report_json TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_assignments (
    id TEXT PRIMARY KEY,
    original_id TEXT NOT NULL REFERENCES reports_original(id),
    reviewer_id TEXT NOT NULL REFERENCES reviewers(id),
    status TEXT NOT NULL DEFAULT 'assigned',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_sessions (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL REFERENCES review_assignments(id),
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS edits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES review_sessions(id),
    seq INTEGER NOT NULL,
    op TEXT NOT NULL,
    path_json TEXT NOT NULL,
    value_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edits_session_seq ON edits(session_id, seq);

CREATE TABLE IF NOT EXISTS claim_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES review_sessions(id),
    claim_id TEXT NOT NULL,
    rating TEXT NOT NULL,
    taxonomy_code TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_claim_ratings_session ON claim_ratings(session_id);

CREATE TABLE IF NOT EXISTS final_reports (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES review_sessions(id),
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES review_sessions(id),
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity, entity_id);

-- Immutability triggers: originals and audit rows can only be appended.
CREATE TRIGGER IF NOT EXISTS trg_reports_original_no_update
BEFORE UPDATE ON reports_original
BEGIN
    SELECT RAISE(ABORT, 'reports_original is immutable: UPDATE denied');
END;

CREATE TRIGGER IF NOT EXISTS trg_reports_original_no_delete
BEFORE DELETE ON reports_original
BEGIN
    SELECT RAISE(ABORT, 'reports_original is immutable: DELETE denied');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is immutable: UPDATE denied');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is immutable: DELETE denied');
END;
