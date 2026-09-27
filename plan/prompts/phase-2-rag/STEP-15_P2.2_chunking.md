# STEP 15 of 54 | P2.2: Structure-aware chunking

- **Phase 2:** Multi-Source RAG
- **Run after:** STEP 14 (P2.1) report shows Status: DONE.
- **Next:** STEP 16 (P2.3): `plan/prompts/phase-2-rag/STEP-16_P2.3_indexing.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Chunk boundaries decide what evidence can be retrieved and cited. Every chunk must be traceable back to the exact source text.

## Task
- Split on document structure first (SPL sections, PMC sections, structured abstract parts, guideline headings), then by token budget with overlap. Keep tables and lists whole where possible.
- Each chunk: `chunk_id` (deterministic hash of source doc version + locator + offsets), text, token count, section_path, locator, character offsets into the normalised source, parent document metadata.
- Record the chunker version.

## Acceptance criteria (write these as tests first)
- No chunk crosses a section boundary.
- Property test: chunk text equals the normalised source text at its offsets.
- Chunk sizes stay within configured bounds (whole tables that exceed them are flagged).
- Chunk ids are deterministic.

## Deliverables
- `src/vh/rag/chunking.py`
- `docs/steps/STEP-15.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-15.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
