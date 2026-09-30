-- Migration 0003: automated-reviewed case track (approved design + independence mandate).
-- Additive only: all human-review tables, triggers, and semantics untouched.
-- Automated rows live in their own tables and can never be mistaken for
-- human reviews; reviewer identities are namespaced `auto-*`.

-- Reviewer type discriminator (default preserves existing human rows).
ALTER TABLE reviewers ADD COLUMN reviewer_type TEXT NOT NULL DEFAULT 'human';

-- One row per automated evaluation of an original AI report.
CREATE TABLE IF NOT EXISTS automated_reviews (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    patient_ref TEXT NOT NULL,
    original_report_json TEXT NOT NULL,
    original_sha256 TEXT NOT NULL,
    ground_truth_source TEXT NOT NULL,
    ground_truth_version TEXT NOT NULL,
    validator_versions_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    decision TEXT NOT NULL,
    reasons_json TEXT NOT NULL DEFAULT '[]',
    sanitized_removed_json TEXT NOT NULL DEFAULT '[]',
    reviewer_id TEXT NOT NULL,
    evaluated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_auto_reviews_patient ON automated_reviews(patient_ref);
CREATE INDEX IF NOT EXISTS idx_auto_reviews_decision ON automated_reviews(decision);

-- Training target for approved/corrected reviews. Never named or typed as a
-- "final report": the SFT target of the automated track.
CREATE TABLE IF NOT EXISTS automated_targets (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL UNIQUE REFERENCES automated_reviews(id),
    target_json TEXT NOT NULL,
    derivation TEXT NOT NULL,
    repair_ops_json TEXT NOT NULL DEFAULT '[]',
    revalidation_pass INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
