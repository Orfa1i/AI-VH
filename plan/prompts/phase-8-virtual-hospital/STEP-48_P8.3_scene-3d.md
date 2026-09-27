# STEP 48 of 54 | P8.3: 3D hospital scene

- **Phase 8:** Virtual Hospital Environment (2D then 3D)
- **Run after:** STEP 47 (P8.2) report shows Status: DONE.
- **Next:** STEP 49 (P8.4): `plan/prompts/phase-8-virtual-hospital/STEP-49_P8.4_ui-integration-tests.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The 3D layer is presentation only. It consumes events and emits nothing clinical.

## Task
- 3D hospital (Three.js; React Three Fiber if the shell is React) with departments as rooms; agents and patients as simple avatars that move between rooms in response to events.
- Clicking an avatar opens the matching 2D detail view.
- Asset budget, level of detail, loading screen.
- Document the reference machine used for performance targets.

## Acceptance criteria (write these as tests first)
- `ui.min_fps` and `ui.max_load_s` met on the reference machine.
- Scene state matches the event log at checkpoints.

## Deliverables
- 3D scene in `web/`
- `docs/steps/STEP-48.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-48.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
