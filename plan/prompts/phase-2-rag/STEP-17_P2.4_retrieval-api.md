# STEP 17 of 54 | P2.4: Unified hybrid retrieval API

- **Phase 2:** Multi-Source RAG
- **Run after:** STEP 16 (P2.3) report shows Status: DONE.
- **Next:** STEP 18 (P2.5): `plan/prompts/phase-2-rag/STEP-18_P2.5_retrieval-evaluation.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
All agents and pipelines retrieve through this one API, whatever the underlying sources.

## Task
- `retrieve(query, filters, k) -> list[EvidenceItem]` where `EvidenceItem` has evidence_id (stable per chunk per index version), text, source, locator and scores.
- Hybrid retrieval: dense + BM25 fused with reciprocal rank fusion; cross-encoder reranker (configurable, can be disabled).
- Source diversity cap (maximum share per source, configurable).
- Superseded documents excluded by default.
- Filters: source, date range, evidence level.
- FastAPI endpoint + Python client; a tracing span per stage.

## Acceptance criteria (write these as tests first)
- Unit tests for fusion, diversity cap, superseded exclusion and each filter.
- API contract tests.
- Every returned EvidenceItem resolves through its locator to the source text.

## Deliverables
- `src/vh/rag/retrieval.py`, API route, client
- `docs/steps/STEP-17.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-17.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
