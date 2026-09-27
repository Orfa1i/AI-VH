# STEP 49 of 54 | P8.4: UI integration and no-side-effect proof

- **Phase 8:** Virtual Hospital Environment (2D then 3D)
- **Run after:** STEP 48 (P8.3) report shows Status: DONE.
- **Next:** STEP 50 (P8.G): `plan/prompts/phase-8-virtual-hospital/STEP-50_P8.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Proof that the visual layer changes nothing clinical.

## Task
- Run the same seeded encounters with recorded LLM outputs with the UI on and with the UI off; compare report hashes and event logs.
- Measure lag between event emission and render.

## Acceptance criteria (write these as tests first)
- Identical outputs (`ui.output_divergence_count` = 0).
- Lag at or below `ui.max_sync_lag_ms`.

## Deliverables
- Integration tests
- `docs/steps/STEP-49.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-49.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
