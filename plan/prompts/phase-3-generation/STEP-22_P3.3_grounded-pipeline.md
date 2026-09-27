# STEP 22 of 54 | P3.3: Grounded generation pipeline with abstention

- **Phase 3:** Grounded Clinical Generation (MedGemma)
- **Run after:** STEP 21 (P3.2) report shows Status: DONE.
- **Next:** STEP 23 (P3.4): `plan/prompts/phase-3-generation/STEP-23_P3.4_model-benchmark.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Core principle: retrieve evidence first, give it to MedGemma, generate one grounded answer. Do not ask several models to answer independently and merge their answers.

## Task
- Pipeline (implements the harness `Pipeline` protocol): AgentView, then query planner (sub-queries: presentation, differential candidates, workup, management), then retrieval, then context assembly (numbered evidence blocks carrying evidence_ids, within a token budget), then generation, then the P3.1 validator.
- Prompt template `clinical_report@1`: use only the supplied evidence; every claim cites evidence_ids; state an abstention when the evidence is insufficient.
- Pre-generation abstention: if retrieval for a sub-question returns nothing above the configured score, record an abstention for that section instead of generating it.
- Post-generation: nothing is dropped silently. Validation failure triggers the adapter retry; final failure sets report status `generation_failed`.

## Acceptance criteria (write these as tests first)
- On the golden set, `generation.schema_valid_rate` and `generation.fabricated_citation_rate` thresholds are met.
- Abstention test: filter out a case's key supporting chunks; the report contains an abstention and no claim on that point.
- Phase 1 leakage tests pass for all pipeline inputs.

## Deliverables
- `src/vh/generation/pipeline.py`, `src/vh/prompt_templates/clinical_report/1.md`
- `docs/steps/STEP-22.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-22.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
