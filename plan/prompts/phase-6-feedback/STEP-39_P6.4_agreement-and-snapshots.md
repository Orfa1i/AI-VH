# STEP 39 of 54 | P6.4: Reviewer agreement and feedback snapshots

- **Phase 6:** Doctor Review & Feedback Store
- **Run after:** STEP 38 (P6.3) report shows Status: DONE.
- **Next:** Human checkpoint(s) H6, then STEP 40 (P6.G): `plan/prompts/phase-6-feedback/STEP-40_P6.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Phase 7 may only train on versioned snapshots produced here, never on the live database.

## Task
- Cohen's kappa on overlap pairs (per-claim ratings and report-level decision); per-taxonomy error rates; reviewer throughput.
- `vh feedback snapshot` exports a versioned `dataset` artifact: originals, evidence, edits, finals, ratings, agreement flags.

## Acceptance criteria (write these as tests first)
- Kappa is correct on a fixture with a known value.
- Snapshots are reproducible and their lineage recorded.

## Deliverables
- `src/vh/feedback/agreement.py`, snapshot CLI
- `docs/steps/STEP-39.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-39.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
