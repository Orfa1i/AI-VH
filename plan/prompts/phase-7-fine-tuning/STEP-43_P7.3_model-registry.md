# STEP 43 of 54 | P7.3: Model registry, shadow mode and rollback

- **Phase 7:** Fine-Tuning & Model Lifecycle
- **Run after:** STEP 42 (P7.2) report shows Status: DONE.
- **Next:** STEP 44 (P7.4): `plan/prompts/phase-7-fine-tuning/STEP-44_P7.4_candidate-evaluation.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Production never changes because a doctor corrected a report. It changes only through a controlled promotion with evidence.

## Task
- Stages: candidate, shadow, production, retired. Promotion requires the id of a PASS evaluation report for that exact model; rollback restores the previous production model in one command.
- Shadow mode: the candidate runs on live encounters in parallel; its outputs are stored but never shown to users or reviewers as the primary report.

## Acceptance criteria (write these as tests first)
- Promotion without a passing report is refused.
- Rollback test passes.
- Shadow outputs never reach the review API or UI (test).

## Deliverables
- `src/vh/training/registry.py`, CLI
- `docs/steps/STEP-43.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-43.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
