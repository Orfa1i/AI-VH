# STEP 08 of 54 | P1.2: Custom Synthea modules for target specialties

- **Phase 1:** Synthetic Patients & Case Builder
- **Run after:** STEP 07 (P1.1) report shows Status: DONE.
- **Next:** STEP 09 (P1.3): `plan/prompts/phase-1-synthetic-patients/STEP-09_P1.3_patient-store.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Built-in Synthea modules may not produce the presentations the golden-set specialties need (for example, acute chest pain with serial troponin). Custom modules use Synthea's Generic Module Framework (JSON state machines).

## Task
- For each golden-set specialty, first check whether built-in modules already produce suitable encounters. Write custom modules only for the gaps, in `synthea/modules/custom/`.
- Each module: realistic onset; observations coded in LOINC with UCUM units; medications in RxNorm; conditions in SNOMED CT; branching for severity.
- Document each module's clinical assumptions in `synthea/modules/custom/README.md` for physician review (part of checkpoint H1).

## Acceptance criteria (write these as tests first)
- Modules load without errors in the pinned Synthea version.
- In a 1,000-patient run, target conditions appear within the configured prevalence range (tolerance defined in the test).
- All observation codes are valid LOINC with UCUM units; medication codes are valid RxNorm (checked against recorded fixtures, no live network in CI).

## Deliverables
- `synthea/modules/custom/*.json` + README of clinical assumptions
- `docs/steps/STEP-08.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-08.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
