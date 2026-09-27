# STEP 27 of 54 | P4.3: Runtime guardrails and verified/flagged routing

- **Phase 4:** Verification Layer
- **Run after:** STEP 26 (P4.2) report shows Status: DONE.
- **Next:** STEP 28 (P4.4): `plan/prompts/phase-4-verification/STEP-28_P4.4_deepeval-ci.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
NeMo Guardrails runs on every live request. DeepEval is for CI/offline evaluation only (next step). Verification must fail closed.

## Task
- NeMo Guardrails configuration: input rails (scope limited to clinical-case processing); output rails invoking the rules engine and grounding checker.
- Router: `verified` only if there are no critical or major rule findings and all claims are supported (partial means flagged). Otherwise `flagged`, with the list of reasons attached to the report.
- Fail closed: any checker error or timeout means `flagged` with reason `verification_error`.
- The verification result is stored immutably with the report.

## Acceptance criteria (write these as tests first)
- Fail-closed test: a checker that raises produces `flagged`.
- Routing matrix tests cover every finding type.
- p95 verification latency measured and compared to `verification.p95_latency_s`.

## Deliverables
- `src/vh/verification/guardrails/`, `router.py`
- `docs/steps/STEP-27.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-27.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
