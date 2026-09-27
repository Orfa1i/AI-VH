# STEP 09 of 54 | P1.3: Patient store and FHIR loader

- **Phase 1:** Synthetic Patients & Case Builder
- **Run after:** STEP 08 (P1.2) report shows Status: DONE.
- **Next:** STEP 10 (P1.4): `plan/prompts/phase-1-synthetic-patients/STEP-10_P1.4_case-spec-schema.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Generated patients need a queryable store the Case Builder can read from.

## Task
- Store per ADR-0001 (default: HAPI FHIR server in docker compose, or Postgres JSONB). Record the choice and reason in ADR-0002.
- Idempotent loader for Synthea bundles.
- Query layer `src/vh/cases/patient_repo.py`: get patient, encounters, and observations / conditions / medications / allergies within a time window.

## Acceptance criteria (write these as tests first)
- Resource counts after loading equal the counts in the bundles.
- Loading twice creates no duplicates.
- Query tests over fixture bundles return correct, time-ordered results.

## Deliverables
- Loader, repository, migrations or FHIR server config, ADR-0002
- `docs/steps/STEP-09.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-09.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
