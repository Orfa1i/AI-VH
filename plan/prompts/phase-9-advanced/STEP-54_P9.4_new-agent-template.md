# STEP 54 of 54 | P9.4: New agent / department scaffold

- **Phase 9:** Advanced Intelligence
- **Run after:** STEP 53 (P9.3) report shows Status: DONE.
- **Next:** None. This is the last step in the plan.

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
New agents and departments are added through the same build-test-gate cycle, never bolted on.

## Task
- `vh new-agent <role>` generates: agent class, versioned prompt, permission entry, tool stubs, tests (permission, leakage, scoring), a docs page and a checklist (implement, test, fix, gate).
- Use it to add one new department agent (e.g., ICU or an ophthalmology clinic) as proof.

## Acceptance criteria (write these as tests first)
- Generated tests fail before implementation and pass after.
- The new agent passes the Phase 5 test suites.
- Full regression suite passes.

## Deliverables
- Scaffold CLI, one new agent
- `docs/steps/STEP-54.md` including a mini-gate section

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.
8. Mini-gate: this item has no separate gate prompt. Add a "Mini-gate" section to the step report with PASS / FAIL for each acceptance criterion and the full-suite result. On PASS, tag the commit `step-54-pass`. On FAIL, follow `plan/prompts/_templates/FIX-LOOP.md` and re-run this step's checks.

## Step report: write to `docs/steps/STEP-54.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
