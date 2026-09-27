# STEP 03 of 54 | P0.3: Observability and artifact versioning

- **Phase 0:** Foundations, Governance & Evaluation Harness
- **Run after:** STEP 02 (P0.2) report shows Status: DONE.
- **Next:** STEP 04 (P0.4): `plan/prompts/phase-0-foundations/STEP-04_P0.4_evaluation-harness.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Every later gate depends on being able to trace a result back to the exact data, index, prompt and model that produced it.

## Task
- Structured JSON logging across all services, with `run_id` and `step` fields.
- OpenTelemetry tracing with `run_id` propagated across service calls; optional Langfuse exporter behind a config flag.
- Artifact registry `src/vh/common/artifacts.py`: register and load versioned artifacts of kinds `dataset`, `index`, `prompt_template`, `model`, `golden_set`, `fault_set`. Record sha256 content hash, version, created_at, parent artifact ids (lineage) and metadata. Storage: Postgres table + files on disk.
- LLM prompt templates live in `src/vh/prompt_templates/<name>/<version>.md` and are loaded only by `name@version`.
- One LLM-call wrapper (a stub for now) that refuses any call without a prompt `name@version`, and logs model id, prompt version, input hash, output hash, latency and token counts.

## Acceptance criteria (write these as tests first)
- A sample request produces one trace whose spans all share the same `run_id`.
- Artifact hash is identical for identical content and changes when content changes; lineage is retrievable.
- Loading `name@version` returns the exact bytes; an unknown version raises.
- The LLM wrapper raises without a prompt version; with one, the log record contains every listed field.

## Deliverables
- `src/vh/common/{logging,tracing,artifacts,llm}.py` and migrations
- `src/vh/prompt_templates/` structure
- `docs/steps/STEP-03.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-03.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
