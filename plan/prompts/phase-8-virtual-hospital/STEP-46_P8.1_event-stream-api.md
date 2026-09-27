# STEP 46 of 54 | P8.1: Read-only event stream API

- **Phase 8:** Virtual Hospital Environment (2D then 3D)
- **Run after:** STEP 45 (P7.G) = PASS in `docs/phase-reports/phase-7.md`.
- **Next:** STEP 47 (P8.2): `plan/prompts/phase-8-virtual-hospital/STEP-47_P8.2_dashboard-2d.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The visual hospital is a view on top of the Phase 5 event log. It reads events; it never writes anything clinical.

## Task
- Read-only SSE (or WebSocket) endpoint streaming encounter events live.
- Replay mode for recorded runs at adjustable speed.
- Resume from the last event id after reconnect.

## Acceptance criteria (write these as tests first)
- Ordering guaranteed; resume works after a forced disconnect.
- No write endpoints exist on this service (test).

## Deliverables
- `src/vh/events/stream.py`
- `docs/steps/STEP-46.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-46.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
