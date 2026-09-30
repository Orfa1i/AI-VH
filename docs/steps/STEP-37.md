# Step Report: STEP-37 (P6.2 Review API with Overlap Sampling)

- **Phase:** Phase 6: Doctor Review & Feedback Store
- **Step:** STEP 37 of 54 (P6.2)
- **Status:** DONE
- **Timestamp:** 2026-09-30T13:30:00Z
- **Tag:** `step-37-pass`

---

## 1. Built: Files Created or Changed

1. `src/vh/feedback/api.py` (new):
   - FastAPI app factory `create_app(db_path, overlap_fraction=0.15)` with
     token auth dependency (401 unknown/missing, 403 non-reviewer role).
   - Endpoints: reviewer registration; review queue (flagged first,
     claim-on-sight); assignment start; report view (claims + verification
     flags, assignment-gated); session/edits/comments reads (owner-only, else
     404); edit/rating/comment submission; approve/correct/reject decisions.
   - `selected_for_overlap` (deterministic hash sampling),
     `simulate_overlap_assignments` (distribution harness).
2. `src/vh/feedback/migrations/0002_review_api.sql` (new, additive):
   reviewer `auth_token_hash`; original `verification_json` + `flagged`;
   session `decision`.
3. `src/vh/feedback/models.py` (extended, backward compatible):
   `store_original(..., verification=None)`, `set_report_verification`,
   `register_reviewer`/`authenticate`, `record_decision`,
   `finalize_report(..., decision=None)` (single audit row, unchanged default),
   session/assignment/rating/comment getters; thread-safe via RLock +
   `check_same_thread=False` (TestClient serves from worker threads).
4. `tests/test_step_37_acceptance.py` (new): 6 acceptance tests.
5. `docs/decisions/ADR-0008-review-api.md` (new).

---

## 2. Tests Added and Full Regression Results

### New Tests (`tests/test_step_37_acceptance.py`, 6 tests):
- `test_non_reviewers_blocked`: 401/401/403/403 contract.
- `test_overlap_reviewer_cannot_see_other_review`: cross-reviewer session,
  edits, and comments reads 404; report view leak-free; own session visible.
- `test_overlap_fraction_within_tolerance`: 1,000 simulated reports, measured
  fraction within 0.05 of 0.15; both single and double assignments present.
- `test_flagged_reports_first`: flagged original heads the queue.
- `test_review_lifecycle_approve_correct_reject`: approve finalizes as-is;
  correct applies inline edits; reject closes with no final.
- `test_taxonomy_validation_on_ratings`: unknown code / bad rating -> 422;
  valid rating -> 200.

### Test Suite Execution:
- `tests/test_step_37_acceptance.py`: 6 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **274 of 274
  tests passed (100% green)** in 469.90s (268 pre-existing + 6 new Step 37).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Cross-thread SQLite access:** symptom `sqlite3.ProgrammingError` on every
   HTTP test. Root cause: TestClient serves requests from worker threads while
   the store connection was created (default `check_same_thread=True`) in the
   test thread. Fix: `check_same_thread=False` + RLock serialization of all
   store methods. Regression: the HTTP tests themselves.
2. **Queue contract mismatch:** symptom `KeyError: 'assignment_id'`; the queue
   returned raw assignment rows (`id`). Root cause: no explicit response
   contract. Fix: queue projects `{assignment_id, original_id, case_id,
   flagged, status}`.
3. **Single-original overlap draw:** symptom `assert qa and qb` failed when the
   deterministic draw did not select the lone test original (correct behavior).
   Root cause: test assumed overlap rather than handling both draws. Fix: test
   branches explicitly (direct assignment fallback), documenting the behavior.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Reviewer-role authentication (no reusable auth in tree) | `api.py` token dependency; `test_non_reviewers_blocked` | PASS |
| Endpoints: queue, report + evidence + flags, approve/correct/reject/comment, per-claim ratings | `api.py` routes; lifecycle + rating tests | PASS |
| Flagged-first assignment | `flagged` column + queue ordering; `test_flagged_reports_first` | PASS |
| Overlap sampling at `review.overlap_fraction`, blinded reviewers | hash sampling + 404 blindness; overlap + blindness tests | PASS |
| Taxonomy input validation | pydantic Literal + taxonomy validator; 422 test | PASS |
| Contract/authorisation tests | First two tests | PASS |
| Overlap fraction within tolerance over 1,000 assignments | `simulate_overlap_assignments`; tolerance test | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- Token revocation/rotation deferred (recorded in ADR-0008; required before
  production use with real doctors). No other open questions.
