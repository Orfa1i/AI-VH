# STEP 14 of 54 | P2.1: Source adapters (refactor knowledge_sources.py)

- **Phase 2:** Multi-Source RAG
- **Run after:** STEP 13 (P1.G) = PASS in `docs/phase-reports/phase-1.md`.
- **Next:** STEP 15 (P2.2): `plan/prompts/phase-2-rag/STEP-15_P2.2_chunking.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The existing `knowledge_sources.py` already integrates RxNorm, DailyMed, openFDA and PubMed (see `docs/current-state.md`). Refactor it rather than rewriting, and keep the NABD feature working.

## Task
- `SourceAdapter` interface: fetch, parse, normalise to `SourceDocument` {source_id, doc_id, title, section_path, locator (URL / anchor / page), version, published_or_updated_date, evidence_level, licence, text}.
- Adapters: PubMed (abstracts); PMC Open Access (full text, licence recorded per article); DailyMed (SPL, section-aware); openFDA (label endpoints as needed); local guidelines placed in `data/sources/guidelines/` with a sidecar metadata file.
- RxNorm is terminology: expose it as a normalisation / lookup service (names to RxCUI, ingredients, classes), not as chunked text.
- Licence enforcement: documents whose licence is unknown or does not permit this use are rejected and logged.
- Caching, rate limiting and retries within each API's published limits; NCBI API key from config.
- Tests use recorded fixtures only.

## Acceptance criteria (write these as tests first)
- Each adapter passes fixture tests and its output validates.
- A licence-unknown document is rejected.
- NABD regression tests pass (write them first if none exist).
- No live network calls during `make test-all` (enforced by a network-blocking fixture).

## Deliverables
- `src/vh/rag/sources/`
- `docs/steps/STEP-14.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-14.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
