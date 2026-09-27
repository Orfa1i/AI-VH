# STEP 10 of 54 | P1.4: Case spec schema and AgentView isolation

- **Phase 1:** Synthetic Patients & Case Builder
- **Run after:** STEP 09 (P1.3) report shows Status: DONE.
- **Next:** STEP 11 (P1.5): `plan/prompts/phase-1-synthetic-patients/STEP-11_P1.5_case-builder.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The single most important safety property of the simulator: agents must never see the answer. This step makes leakage structurally impossible, not just discouraged.

## Task
- `CaseSpec` with three parts:
  - `visible`: presentation, demographics, history, current medications, allergies, initial vitals.
  - `hidden`: results released only on request, each with an order code and turnaround time.
  - `ground_truth`: primary_dx, acceptable_differential, expected_workup, red_flags.
- `AgentView`: the only object agents or pipelines ever receive. It has no field, method or reference that reaches `hidden` or `ground_truth`. Hidden results arrive only through the environment (Phase 5) or an explicit logged `release(order)` call.
- A golden case must convert to a `CaseSpec` and back without loss.

## Acceptance criteria (write these as tests first)
- Serialising an `AgentView` contains no hidden or ground-truth keys (recursive test).
- Any attempt to reach hidden data from an `AgentView` raises.
- Golden case to CaseSpec round-trip is lossless.

## Deliverables
- `src/vh/cases/spec.py`
- `docs/steps/STEP-10.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-10.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
