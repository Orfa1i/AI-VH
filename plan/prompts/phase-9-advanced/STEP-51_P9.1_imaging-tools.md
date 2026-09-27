# STEP 51 of 54 | P9.1: Imaging models as Radiology agent tools

- **Phase 9:** Advanced Intelligence
- **Run after:** STEP 50 (P8.G) = PASS in `docs/phase-reports/phase-8.md`.
- **Next:** STEP 52 (P9.2): `plan/prompts/phase-9-advanced/STEP-52_P9.2_knowledge-graph.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The existing fracture-localisation and knee-OA grading models become tools for the Radiology agent. Synthea does not produce images, so images come from a separate open, de-identified dataset with a confirmed licence. Never real identifiable images.

## Task
- Wrap each model as a tool with typed output: finding, location, grade/probability, model version.
- Keep the models' existing validation baselines as regression tests.
- Outputs are labelled as model output with confidence, never as ground truth.
- Verification: imaging claims must cite the tool-output id as evidence (extend P3.1 validator and P4.1 rules).
- Replace the `not_implemented` stubs from P5.2.

## Acceptance criteria (write these as tests first)
- Existing baselines reproduced within tolerance.
- Imaging claims without a tool-output citation are flagged.
- Full regression suite of all phases passes.

## Deliverables
- `src/vh/agents/tools/imaging.py`
- `docs/steps/STEP-51.md` including a mini-gate section (PASS / FAIL)

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.
8. Mini-gate: this item has no separate gate prompt. Add a "Mini-gate" section to the step report with PASS / FAIL for each acceptance criterion and the full-suite result. On PASS, tag the commit `step-51-pass`. On FAIL, follow `plan/prompts/_templates/FIX-LOOP.md` and re-run this step's checks.

## Step report: write to `docs/steps/STEP-51.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
