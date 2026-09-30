# STEP 53 of 54 | P9.3: Preference optimisation (DPO)

- **Phase 9:** Advanced Intelligence
- **Run after:** STEP 52 (P9.2) report shows Status: DONE.
- **Next:** STEP 54 (P9.4): `plan/prompts/phase-9-advanced/STEP-54_P9.4_new-agent-template.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Prerequisites: at least `training.min_preference_pairs` preference pairs (the project owner sets this value; while it is null, stop with Status: BLOCKED) and `review.kappa_min` met. If either is not met, stop with Status: BLOCKED.

## Task
- Preference pairs: doctor-final (chosen) vs original AI report (rejected) where the doctor corrected it.
- DPO with TRL on top of the current production adapter; register as candidate.
- Evaluate exactly as in P7.4; promote only through the P7.3 registry.

## Acceptance criteria (write these as tests first)
- Zero safety regressions; candidate beats production.
- Blinded physician comparison recorded (same format as H7).
- Full regression suite passes.

## Deliverables
- `src/vh/training/dpo.py`
- `docs/steps/STEP-53.md` including a mini-gate section

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.
8. Mini-gate: this item has no separate gate prompt. Add a "Mini-gate" section to the step report with PASS / FAIL for each acceptance criterion and the full-suite result. On PASS, tag the commit `step-53-pass`. On FAIL, follow `plan/prompts/_templates/FIX-LOOP.md` and re-run this step's checks.

## Step report: write to `docs/steps/STEP-53.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
