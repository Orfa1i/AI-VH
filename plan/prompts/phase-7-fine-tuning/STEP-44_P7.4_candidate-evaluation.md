# STEP 44 of 54 | P7.4: Candidate evaluation and blinded review packet

- **Phase 7:** Fine-Tuning & Model Lifecycle
- **Run after:** STEP 43 (P7.3) report shows Status: DONE.
- **Next:** Human checkpoint(s) H7, then STEP 45 (P7.G): `plan/prompts/phase-7-fine-tuning/STEP-45_P7.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
A candidate is compared against production on everything built so far, plus a blinded physician comparison.

## Task
- Run candidate and production on: the frozen golden set, the fault-injection set, all phase regression suites, and the held-out test split.
- Comparison report with bootstrap CIs per metric; list safety regressions explicitly.
- Blinded packet: 50 cases, candidate and production reports randomly labelled A/B. Store the key in a separate file that is not part of the packet.

## Acceptance criteria (write these as tests first)
- `training.safety_regressions` = 0, otherwise FAIL.
- Report and packet generated; a test confirms the key is not in the packet.

## Deliverables
- Comparison report, blinded packet, key file
- `docs/steps/STEP-44.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-44.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
