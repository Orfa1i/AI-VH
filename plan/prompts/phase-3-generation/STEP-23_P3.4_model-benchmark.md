# STEP 23 of 54 | P3.4: Model benchmark and no-RAG baseline

- **Phase 3:** Grounded Clinical Generation (MedGemma)
- **Run after:** STEP 22 (P3.3) report shows Status: DONE.
- **Next:** Human checkpoint(s) H3, then STEP 24 (P3.G): `plan/prompts/phase-3-generation/STEP-24_P3.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Retrieval must be shown to add value, and the production MedGemma variant is chosen by measurement.

## Task
- A no-RAG baseline pipeline (same prompt family, no evidence, no citation requirement).
- Run the model variants available to you (e.g., MedGemma 4B vs 27B, and newer releases if licensed and servable) through the grounded pipeline on the golden set.
- Metrics: top-1 and top-3 diagnostic accuracy against ground truth, citation validity, abstention correctness, stability (3 runs; agreement of top-3), latency, cost per case.
- Bootstrap 95% confidence intervals for accuracy differences.
- ADR-0004 selecting the production variant.
- Propose a value for `generation.dx_top3_min` in your step report. Do not write it into thresholds; the project owner sets it.

## Acceptance criteria (write these as tests first)
- The grounded pipeline's top-3 accuracy beats the no-RAG baseline with a CI that excludes zero; if not, report it honestly (the gate will fail).
- All numbers reproducible from their run_ids.

## Deliverables
- Baseline pipeline, benchmark report in `eval/reports/`, ADR-0004
- `docs/steps/STEP-23.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-23.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
