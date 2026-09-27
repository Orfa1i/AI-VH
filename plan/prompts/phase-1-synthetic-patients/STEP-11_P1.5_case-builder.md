# STEP 11 of 54 | P1.5: Case Builder

- **Phase 1:** Synthetic Patients & Case Builder
- **Run after:** STEP 10 (P1.4) report shows Status: DONE.
- **Next:** STEP 12 (P1.6): `plan/prompts/phase-1-synthetic-patients/STEP-12_P1.6_case-validation-suite.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Synthea produces structured data but a thin clinical narrative. The Case Builder writes the presentation without leaking the diagnosis.

## Task
- Select encounters matching a specialty spec (condition codes, time window, severity).
- Build a `CaseSpec`: data available at presentation time goes to `visible`; later results go to `hidden`.
- Narrative: template-based by default. Optional LLM narrative through the P0.3 wrapper behind a config flag, followed by the same checks.
- Leakage guard: a per-condition term list (diagnosis name, abbreviations, common synonyms) in `configs/leakage_terms/`. Narrative and visible fields must contain none of them.
- Consistency check: every number in the narrative matches the structured record.
- Deterministic with a seed; each case registered with lineage to its Synthea dataset artifact.

## Acceptance criteria (write these as tests first)
- Zero leakage terms across a 500-case batch.
- 100% narrative-number consistency.
- Same seed gives identical cases.
- The LLM-narrative mode passes the same tests (integration marker).

## Deliverables
- `src/vh/cases/builder.py`, `configs/leakage_terms/`
- `docs/steps/STEP-11.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-11.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
