# STEP 12 of 54 | P1.6: Case validation suite and spot-check packet

- **Phase 1:** Synthetic Patients & Case Builder
- **Run after:** STEP 11 (P1.5) report shows Status: DONE.
- **Next:** Human checkpoint(s) H1, then STEP 13 (P1.G): `plan/prompts/phase-1-synthetic-patients/STEP-13_P1.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The phase gate needs measurable evidence that the cases are plausible and leak-free.

## Task
- Plausibility rules in `src/vh/cases/validation.py`: vitals within physiological ranges; UCUM units; lab values consistent with the ground-truth diagnosis (e.g., DKA: glucose, ketones, pH/bicarbonate pattern); medications consistent with conditions; correct temporal ordering.
- Leakage suite run over every builder output.
- Batch report with pass rates per rule.
- `vh cases spotcheck --n 50` exports a random reviewer packet to `docs/signoffs/phase-1-spotcheck-packet.md` with a defect checklist per case (record the random seed).

## Acceptance criteria (write these as tests first)
- Every rule has positive and negative unit tests.
- A 500-case batch meets the `cases.*` thresholds.
- Spot-check packet generated with its seed recorded.

## Deliverables
- Validation module and batch report in `eval/reports/`
- Spot-check packet
- `docs/steps/STEP-12.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-12.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
