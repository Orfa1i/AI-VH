-- Migration 0002: reviewer auth + verification flags + session decisions (STEP 37).
-- Additive only: earlier tables and triggers untouched.

-- Reviewer authentication token (sha256 hex of the issued token).
ALTER TABLE reviewers ADD COLUMN auth_token_hash TEXT;

-- Verification outcome attached to an original report; flagged reports
-- head the review queue.
ALTER TABLE reports_original ADD COLUMN verification_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE reports_original ADD COLUMN flagged INTEGER NOT NULL DEFAULT 0;

-- Reviewer decision closing a session (approve | correct | reject).
ALTER TABLE review_sessions ADD COLUMN decision TEXT;
