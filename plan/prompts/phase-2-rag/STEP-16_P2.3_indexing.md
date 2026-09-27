# STEP 16 of 54 | P2.3: Dense + keyword indexing with versioned indexes

- **Phase 2:** Multi-Source RAG
- **Run after:** STEP 15 (P2.2) report shows Status: DONE.
- **Next:** STEP 17 (P2.4): `plan/prompts/phase-2-rag/STEP-17_P2.4_retrieval-api.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Two embedding candidates are configured here; the final choice is made by measurement in STEP 18, not by preference.

## Task
- Embedding interface with two configured candidates: one general-purpose, one biomedical.
- Dense index in the vector store chosen in ADR-0001 (default pgvector or ChromaDB) plus a BM25 keyword index.
- Each index is a versioned artifact with a manifest: embedding model + version, chunker version, source document versions, counts.
- Incremental updates: new or changed documents re-indexed; superseded versions marked `superseded_by`.

## Acceptance criteria (write these as tests first)
- Manifest is complete and matches the actual index contents.
- A full rebuild from the same inputs gives identical chunk ids and counts.
- Query output records the index version used.
- Superseded marking tested.

## Deliverables
- `src/vh/rag/indexing.py`
- `docs/steps/STEP-16.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-16.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
