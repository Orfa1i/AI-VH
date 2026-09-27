# STEP 41 of 54 | P7.1: Training dataset curation

- **Phase 7:** Fine-Tuning & Model Lifecycle
- **Run after:** STEP 40 (P6.G) = PASS in `docs/phase-reports/phase-6.md`.
- **Next:** STEP 42 (P7.2): `plan/prompts/phase-7-fine-tuning/STEP-42_P7.2_lora-training.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Requires a feedback snapshot with at least `training.min_reviewed_cases` reviewed cases. If there are fewer, stop with Status: BLOCKED (waiting for data is not a test failure).

## Task
- Filters: exclude cases whose overlap reviews disagree; exclude rejected-without-correction reports from SFT (keep them for preference data later); remove near-duplicates.
- SFT format: input = AgentView + evidence blocks in exactly the production prompt format; target = the doctor-final report JSON.
- Split by `patient_ref` (train / val / test), never by case.
- Contamination check against every golden-set version: id match plus near-duplicate text similarity above a threshold means excluded.
- Dataset card: counts, filters applied, distributions, known gaps.

## Acceptance criteria (write these as tests first)
- Zero patient overlap across splits.
- Zero golden-set contamination.
- Dataset reproducible from the snapshot version + config.

## Deliverables
- `src/vh/training/curation.py`, dataset artifact, dataset card
- `docs/steps/STEP-41.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-41.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
