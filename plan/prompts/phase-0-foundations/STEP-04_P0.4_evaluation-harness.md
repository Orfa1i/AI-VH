# STEP 04 of 54 | P0.4: Evaluation harness and frozen golden-set mechanism

- **Phase 0:** Foundations, Governance & Evaluation Harness
- **Run after:** STEP 03 (P0.3) report shows Status: DONE.
- **Next:** STEP 05 (P0.5): `plan/prompts/phase-0-foundations/STEP-05_P0.5_golden-set-authoring.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
The golden set is the fixed yardstick every gate is measured against. The harness must make it impossible to pass a gate by accident or by quietly changing the test data.

## Task
- Golden case schema (pydantic, exported to `eval/schema/golden_case.json`) with fields: `case_id`, `specialty`, `patient_ref`, `visible_presentation`, `hidden_results[]`, `ground_truth` {`primary_dx`, `acceptable_differential[]`, `expected_workup[]`, `red_flags[]`}, `supporting_references[]` {source, locator, note}, `status` (draft | verified), `reviewer`, `reviewed_at`, `version`.
- Golden set releases live in `eval/golden/v{N}/` with a `manifest.json` holding each file's sha256. A released version is frozen: the harness checks the manifest and refuses to run on any mismatch. New content means a new version.
- `Pipeline` protocol: `run(case_view) -> result`. Scorer plug-in interface: `score(results, golden) -> dict[str, float]`.
- `make eval GOLDEN=vN PIPELINE=<name>` runs the pipeline on every verified case, runs the registered scorers, compares each metric to `configs/thresholds.yaml`, and writes `eval/reports/<run_id>/report.json` and `report.md` with PASS / FAIL per metric.
- A dummy pipeline and dummy scorer used only to test the harness.
- The harness passes only the case view to the pipeline, never ground truth.

## Acceptance criteria (write these as tests first)
- The dummy pipeline is scored end-to-end and a report is written.
- Modifying any file in a frozen version makes the harness refuse, with a clear error.
- A metric with no threshold, or a `null` threshold, is reported FAIL (never a silent PASS).
- The same inputs give an identical report (ignoring timestamps).
- A test proves the pipeline never receives `ground_truth` fields.

## Deliverables
- `eval/schema/`, `eval/harness/`, Makefile `eval` target
- `docs/steps/STEP-04.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-04.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
