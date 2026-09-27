# STEP 21 of 54 | P3.2: MedGemma adapter

- **Phase 3:** Grounded Clinical Generation (MedGemma)
- **Run after:** STEP 20 (P3.1) report shows Status: DONE.
- **Next:** STEP 22 (P3.3): `plan/prompts/phase-3-generation/STEP-22_P3.3_grounded-pipeline.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
MedGemma is already deployed (see `docs/current-state.md` for the variant and serving stack). Wrap it; do not redeploy unless the audit found a blocker.

## Task
- Adapter implementing the P0.3 LLM wrapper: `generate(prompt name@version, inputs, response_schema)`.
- Use constrained / guided JSON decoding if the serving stack supports it; otherwise parse, validate, and retry up to N times feeding back the validation error.
- After N failures raise `GenerationFailed`. Never return a partial report.
- Timeouts, a concurrency limit, and configurable model variant and sampling parameters.

## Acceptance criteria (write these as tests first)
- Retry logic tested with a mocked model (invalid then valid; invalid N times raises `GenerationFailed`).
- An integration test (marker) against the real endpoint returns a schema-valid report for one fixture case.
- Every call is logged with its prompt version.

## Deliverables
- `src/vh/generation/medgemma.py`
- `docs/steps/STEP-21.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-21.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
