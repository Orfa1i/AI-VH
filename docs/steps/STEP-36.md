# Step Report: STEP-36 (P6.1 Feedback Data Model, Append-Only)

- **Phase:** Phase 6: Doctor Review & Feedback Store
- **Step:** STEP 36 of 54 (P6.1)
- **Status:** DONE
- **Timestamp:** 2026-09-30T12:30:00Z
- **Tag:** `step-36-pass`

---

## 1. Built: Files Created or Changed

1. `src/vh/feedback/models.py` (new):
   - Pydantic row models (`Reviewer`, `OriginalReport`, `EditOperation`,
     `ClaimRating`, `AuditEntry`).
   - `apply_edits`: pure-function structured edit application
     (`replace`/`add`/`remove` over key/index paths), deepcopy-based, fail-closed.
   - `FeedbackStore`: SQLite-backed append-only store (originals, assignments,
     sessions, edits, claim ratings with taxonomy validation, finals, comments);
     every mutating method appends exactly one `audit_log` row.
2. `src/vh/feedback/migrations/0001_initial.sql` (new): all nine tables
   (`reports_original`, `review_assignments`, `review_sessions`, `edits`,
   `claim_ratings`, `final_reports`, `comments`, `reviewers`, `audit_log`)
   plus four immutability triggers (`RAISE(ABORT, ...)` on UPDATE/DELETE of
   `reports_original` and `audit_log`).
3. `src/vh/feedback/migrations/__init__.py` (new): versioned runner with
   `schema_migrations` tracking; idempotent re-runs.
4. `configs/feedback/taxonomy.yaml` (new): versioned error taxonomy, all nine
   required codes (wrong/missed diagnosis, missed red flag, bad citation,
   unsupported claim, unsafe recommendation, dosing error, formatting, other).
5. `tests/test_step_36_acceptance.py` (new): 8 acceptance tests.
6. `docs/decisions/ADR-0007-feedback-store.md` (new).

---

## 2. Tests Added and Full Regression Results

### New Tests (`tests/test_step_36_acceptance.py`, 8 tests):
- `test_direct_sql_update_of_original_fails`: raw UPDATE/DELETE on
  `reports_original` and `audit_log` raise `sqlite3.IntegrityError`; row intact.
- `test_edits_reproduce_final_exactly`: hand-built edits reproduce the final
  exactly at both pure-function and stored levels; original pristine.
- `test_edits_property_based`: hypothesis over arbitrary JSON docs; replace-ops
  match an independent reference application, deterministically, without
  mutating inputs.
- `test_invalid_edit_raises_without_partial_application`: bad paths fail closed.
- `test_every_write_produces_audit_row`: each of the 8 writes appends exactly
  one audit row with the expected action sequence.
- `test_taxonomy_has_required_codes`: all 9 codes present + version set.
- `test_claim_rating_rejects_unknown_taxonomy`: unknown codes refused.
- `test_migrations_apply_cleanly`: all tables + triggers exist; re-run idempotent.

### Test Suite Execution:
- `tests/test_step_36_acceptance.py`: 8 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **268 of 268
  tests passed (100% green)** in 285.08s (260 pre-existing + 8 new Step 36).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Property-test reference setter too permissive:** symptom: hypothesis
   falsified with `TypeError: Cannot replace at path: [0, 0]` on `[[None]]`
   (an earlier op reshaped the doc, invalidating a later path). Root cause: the
   test-side setter silently accepted dict-with-int-key writes instead of
   enforcing dict-str/list-int discipline. Fix: strict test-side path walk
   validates each op against the current expected doc before applying to either
   code path (implementation behavior was correct). No production code changed.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Tables/migrations for all 9 entities | `migrations/0001_initial.sql`, `test_migrations_apply_cleanly` | PASS |
| Error taxonomy with all 9 codes | `configs/feedback/taxonomy.yaml`, `test_taxonomy_has_required_codes` | PASS |
| DB-level immutability (triggers, not app code) | 4 triggers in `0001_initial.sql`, `test_direct_sql_update_of_original_fails` | PASS |
| Direct SQL update of original fails | Same test (UPDATE + DELETE on both immutable tables) | PASS |
| Stored edits reproduce final exactly (property test) | `apply_edits` + `finalize_report`; hand-built + hypothesis tests | PASS |
| Every write produces an audit row | `FeedbackStore._audit` in all 8 mutators; audit sequence test | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- Migration SQL is Postgres-compatible by inspection except triggers, which need
  a `plpgsql` port at deployment (recorded in ADR-0007). No clinical content
  affected. No other open questions.
