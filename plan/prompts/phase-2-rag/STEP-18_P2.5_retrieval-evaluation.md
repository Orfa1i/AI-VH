# STEP 18 of 54 | P2.5: Retrieval evaluation and configuration choice

- **Phase 2:** Multi-Source RAG
- **Run after:** STEP 17 (P2.4) report shows Status: DONE.
- **Next:** Human checkpoint(s) H2, then STEP 19 (P2.G): `plan/prompts/phase-2-rag/STEP-19_P2.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Retrieval quality is measured against the golden set's supporting references before any generation work begins.

## Task
- Map each golden case's `supporting_references` to chunk ids in the current index. Write the mapping to `eval/golden/v{N}-chunkmap.json` as a draft for human confirmation (checkpoint H2). List unmappable references.
- Build queries only from `AgentView` data plus fixed question templates (e.g., "diagnostic workup for <presentation>"), never from ground-truth text.
- Scorers: Recall@5, Recall@10, MRR, per-source recall, traceability rate, duplicate rate, stale-retrieval count, p95 latency.
- Experiments: both embedding candidates, reranker on and off. Record results and the chosen configuration in ADR-0003 and make it the default.
- Do not change thresholds. If nothing meets them, report it; the gate will fail and the fix loop applies.

## Acceptance criteria (write these as tests first)
- Every scorer is unit-tested on fixtures with known answers.
- Experiment results are reproducible from their run_ids.
- The chosen configuration's metrics are reported against `retrieval.*` thresholds.

## Deliverables
- Scorers in `eval/harness/scorers/`, chunk-map draft, ADR-0003
- `docs/steps/STEP-18.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-18.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
