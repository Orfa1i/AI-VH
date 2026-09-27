# STEP 07 of 54 | P1.1: Synthea runner (reproducible FHIR export)

- **Phase 1:** Synthetic Patients & Case Builder
- **Run after:** STEP 06 (P0.G) = PASS in `docs/phase-reports/phase-0.md`.
- **Next:** STEP 08 (P1.2): `plan/prompts/phase-1-synthetic-patients/STEP-08_P1.2_synthea-custom-modules.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Synthea generates the synthetic patient population. It must be fully reproducible so any case can be regenerated from its recorded configuration.

## Task
- Run the official Synthea release in a pinned Docker image; pin the Synthea version.
- Wrapper `vh synthea generate` with `--seed`, `--clinician-seed`, `--reference-date`, `--population`, location and `--modules` options. FHIR R4 bundle export only (disable other exporters unless needed).
- Register the output directory as a `dataset` artifact with the full generation config in its metadata.
- Validate every bundle (fhir.resources, or the HAPI validator in a container).

## Acceptance criteria (write these as tests first)
- Same seed + clinician seed + reference date + Synthea version gives an identical output hash.
- 100% of bundles validate.
- The generation can be reproduced from the artifact metadata alone.

## Deliverables
- `src/vh/synthea/`, Dockerfile, CLI
- `docs/steps/STEP-07.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-07.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
