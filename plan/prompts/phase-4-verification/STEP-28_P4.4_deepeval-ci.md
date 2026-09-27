# STEP 28 of 54 | P4.4: DeepEval metrics in CI

- **Phase 4:** Verification Layer
- **Run after:** STEP 27 (P4.3) report shows Status: DONE.
- **Next:** STEP 29 (P4.5): `plan/prompts/phase-4-verification/STEP-29_P4.5_fault-injection.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
DeepEval measures RAG quality over the golden set. It belongs in CI and offline evaluation, not in the request path.

## Task
- DeepEval metrics (faithfulness, contextual relevancy, answer relevancy) as harness scorers.
- CI job `eval-rag` on the golden set (nightly, and on PRs touching `rag/` or `generation/`), failing below thresholds.
- Pin the DeepEval version and the judge model.

## Acceptance criteria (write these as tests first)
- Scorers produce metrics in eval reports.
- Demonstrate a CI failure by temporarily raising a threshold above the current score on a throwaway branch, then delete the branch.

## Deliverables
- Scorers, CI job
- `docs/steps/STEP-28.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-28.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
