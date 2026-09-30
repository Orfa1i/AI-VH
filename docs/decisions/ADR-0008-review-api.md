# ADR-0008: Review API Auth, Queue, and Overlap Design

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-6-feedback/STEP-37_P6.2_review-api.md`

---

## 1. Context

P6.2 needs reviewer authentication, a flagged-first queue, double-reviewer
overlap sampling at `review.overlap_fraction` (0.15), and strict blindness
between overlap reviewers. `docs/current-state.md` shows no reusable auth in
`src/vh`, so the feedback service carries its own minimal token auth.

## 2. Decision

- **Tokens, not passwords**: `register_reviewer` issues `secrets.token_urlsafe`
  tokens; only sha256 hashes are stored (migration 0002). Requests carry
  `X-Reviewer-Token`. Unknown/missing token -> 401; valid token with a
  non-reviewer role -> 403. Reviewer roles: attending, reviewer, resident,
  fellow.
- **Claim-on-sight queue**: `GET /reviews/queue` lists the caller's open
  assignments (flagged first, then oldest) and creates at most one assignment
  per newly visible eligible original. Assignment creation is therefore
  auditable and idempotent; pure-read listing would have left claiming to a
  second race-prone call.
- **Deterministic overlap**: `selected_for_overlap` hashes
  `overlap-v1:{original_id}` (sha256 % 10000) instead of RNG so sampling is
  stable across restarts and exactly reproducible in tests; quota is 2 for
  selected reports, 1 otherwise. Measured 0.15 +/- tolerance over 1,000 reports.
- **Blindness by 404**: any session/assignment owned by another reviewer reads
  as nonexistent (404, never 403) so overlap reviewers cannot even confirm a
  second review exists. Report views expose only the original + verification
  flags, never another session's edits/ratings/comments.
- **Decisions close the loop**: approve/correct finalize (correct applies
  inline edits first); reject records the decision with an optional comment
  and produces no final report. One final per session (UNIQUE, from STEP 36).

## 3. Consequences

- Token revocation/rotation is out of scope for P6.2 (recorded; needed before
  any production use with real doctors).
- Evidence text in report views is the report's own claims plus stored
  verification flags; live RAG re-resolution stays in the RAG layer.
