# STEP 31 of 54 | P5.1: Hospital environment simulator and event log

- **Phase 5:** Agents & Orchestration (headless)
- **Run after:** STEP 30 (P4.G) = PASS in `docs/phase-reports/phase-4.md`.
- **Next:** STEP 32 (P5.2): `plan/prompts/phase-5-agents/STEP-32_P5.2_agents-permissions.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Agents are built headless first: a text-and-event simulation with no graphics. The environment is the only way hidden case data is ever released.

## Task
- `HospitalEnvironment(case_spec, seed)` owns the AgentView, hidden results, a simulation clock and the event log.
- Typed actions: `request_vitals`, `order_lab(code)`, `order_imaging(code)`, `request_medication_info`, `consult(role)`, `submit_report`. Each is validated against the case; results are released only once their turnaround time has elapsed on the simulation clock.
- Orders with no data in the case return `result_unavailable`. Never invent data.
- Append-only event log: {event_id, run_id, sim_time, wall_time, actor, action, payload, result_ref}, persisted.

## Acceptance criteria (write these as tests first)
- Ground truth is unreachable through any action (fuzz test over the action space).
- Turnaround times respected.
- Unavailable orders return `result_unavailable`.
- Every action produces exactly one event; events are never updated or deleted.

## Deliverables
- `src/vh/agents/environment.py`, event store
- `docs/steps/STEP-31.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-31.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
