# STEP 52 of 54 | P9.2: Knowledge graph experiment

- **Phase 9:** Advanced Intelligence
- **Run after:** STEP 51 (P9.1) report shows Status: DONE.
- **Next:** STEP 53 (P9.3): `plan/prompts/phase-9-advanced/STEP-53_P9.3_preference-optimization.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
A knowledge graph is adopted only if it measurably beats RAG-only.

## Task
- Build a graph from the existing normalised sources: drug, ingredient and class (RxNorm); interactions and contraindications (label sections); condition-to-guideline links. Every edge carries provenance.
- KG-augmented retrieval behind a feature flag.
- A/B on the golden set against RAG-only.
- ADR-0007 recording the result and decision either way.

## Acceptance criteria (write these as tests first)
- Every edge resolves to its source.
- Adopt only if primary metrics improve with no safety regression; otherwise leave the flag off.
- Full regression suite passes.

## Deliverables
- `src/vh/rag/kg/`, ADR-0007
- `docs/steps/STEP-52.md` including a mini-gate section

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.
8. Mini-gate: this item has no separate gate prompt. Add a "Mini-gate" section to the step report with PASS / FAIL for each acceptance criterion and the full-suite result. On PASS, tag the commit `step-52-pass`. On FAIL, follow `plan/prompts/_templates/FIX-LOOP.md` and re-run this step's checks.

## Step report: write to `docs/steps/STEP-52.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
