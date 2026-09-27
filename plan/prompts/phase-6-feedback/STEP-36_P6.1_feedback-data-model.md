# STEP 36 of 54 | P6.1: Feedback data model (append-only)

- **Phase 6:** Doctor Review & Feedback Store
- **Run after:** STEP 35 (P5.G) = PASS in `docs/phase-reports/phase-5.md`.
- **Next:** STEP 37 (P6.2): `plan/prompts/phase-6-feedback/STEP-37_P6.2_review-api.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The difference between the AI's original report and the doctor's final version is the most valuable training signal in the project. The original must never be overwritten.

## Task
- Tables / migrations: `reports_original` (immutable), `review_assignments`, `review_sessions`, `edits` (structured diff operations against the original), `claim_ratings` (per claim: correct | partially correct | incorrect + taxonomy code), `final_reports`, `comments`, `reviewers`, `audit_log`.
- Error taxonomy in `configs/feedback/taxonomy.yaml`: wrong diagnosis, missed diagnosis, missed red flag, bad citation, unsupported claim, unsafe recommendation, dosing error, formatting, other.
- Immutability enforced at database level: UPDATE and DELETE on `reports_original` and `audit_log` are denied by trigger / permissions, not only in application code.

## Acceptance criteria (write these as tests first)
- A direct SQL update of an original report fails.
- Applying the stored edits to the original reproduces the final report exactly (property test).
- Every write produces an `audit_log` row.

## Deliverables
- `src/vh/feedback/models.py`, migrations, taxonomy config
- `docs/steps/STEP-36.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-36.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
