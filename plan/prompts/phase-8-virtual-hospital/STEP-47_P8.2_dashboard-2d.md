# STEP 47 of 54 | P8.2: 2D department dashboard

- **Phase 8:** Virtual Hospital Environment (2D then 3D)
- **Run after:** STEP 46 (P8.1) report shows Status: DONE.
- **Next:** STEP 48 (P8.3): `plan/prompts/phase-8-virtual-hospital/STEP-48_P8.3_scene-3d.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The 2D dashboard comes before 3D. It lives in the existing Clinical AI OS shell.

## Task
- Department board: ER, Reception, Lab, Radiology, Pharmacy, Wards, ICU, Clinics.
- Patient cards with status, encounter timeline, agent activity feed, links to the report and review.
- Driven only by the event stream; works in live and replay mode.

## Acceptance criteria (write these as tests first)
- Playwright: replaying a recorded encounter renders the expected sequence of states.
- Live and replay modes both tested.

## Deliverables
- Dashboard pages in `web/`
- `docs/steps/STEP-47.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-47.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
