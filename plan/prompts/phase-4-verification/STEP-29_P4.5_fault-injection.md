# STEP 29 of 54 | P4.5: Fault-injection suite

- **Phase 4:** Verification Layer
- **Run after:** STEP 28 (P4.4) report shows Status: DONE.
- **Next:** Human checkpoint(s) H4, then STEP 30 (P4.G): `plan/prompts/phase-4-verification/STEP-30_P4.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The verification layer is only proven by showing it catches deliberately broken reports without over-flagging clean ones.

## Task
- Generator that takes clean pipeline reports and creates labelled corrupted variants: wrong evidence_id, swapped evidence, fabricated claim, allergy conflict, contraindicated drug, overdose, renal-dose error, contradiction of vitals/labs, missed red flag.
- Classify each fault type as critical or non-critical in config.
- Scorer: detection rate per fault type, overall critical and non-critical detection, and false-flag rate on the clean originals.
- Register the fault set as a versioned `fault_set` artifact.

## Acceptance criteria (write these as tests first)
- Every fault type appears at least 20 times.
- Metrics computed and compared to `verification.*` thresholds.

## Deliverables
- `eval/faults/`, scorer
- `docs/steps/STEP-29.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-29.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
