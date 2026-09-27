# STEP 20 of 54 | P3.1: Clinical report schema with claim-evidence links

- **Phase 3:** Grounded Clinical Generation (MedGemma)
- **Run after:** STEP 19 (P2.G) = PASS in `docs/phase-reports/phase-2.md`.
- **Next:** STEP 21 (P3.2): `plan/prompts/phase-3-generation/STEP-21_P3.2_medgemma-adapter.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Every clinical statement must be traceable to evidence. The schema enforces this before any model is involved.

## Task
- `ClinicalReport` model:
  - `patient_summary`, `findings[]`
  - `differential[]` {dx, likelihood (high | moderate | low), claim_ids[]}
  - `recommendations[]` {text, claim_ids[]}
  - `claims[]` {claim_id, text, type (diagnostic | therapeutic | prognostic | factual), evidence_ids[]}
  - `abstentions[]` {question, reason}
  - `provenance` {run_id, model_id, prompt name@version, index version, case_id}
- Export the JSON Schema to `schemas/clinical_report.json` (used for constrained decoding).
- Validator: schema, plus referential integrity: every referenced claim_id exists; every evidence_id exists in this run's retrieval context; every recommendation and differential entry has at least one claim.

## Acceptance criteria (write these as tests first)
- A valid fixture passes; each type of integrity violation has a fixture that is detected.
- The exported schema matches the model.

## Deliverables
- `src/vh/generation/report.py`, `schemas/clinical_report.json`
- `docs/steps/STEP-20.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-20.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
