# STEP 25 of 54 | P4.1: Deterministic safety rules engine

- **Phase 4:** Verification Layer
- **Run after:** STEP 24 (P3.G) = PASS in `docs/phase-reports/phase-3.md`.
- **Next:** STEP 26 (P4.2): `plan/prompts/phase-4-verification/STEP-26_P4.2_grounding-checker.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Deterministic rules are the last line of defence and must not depend on an LLM. Note: NLM retired the RxNav drug-drug interaction API in January 2024, so interaction data must come from another source, such as parsed DailyMed "Drug Interactions" label sections or a licensed database. Record the choice in ADR-0005.

## Task
- Rule interface: pure function (report, patient_record, knowledge) returning `list[Finding]` {rule_id, severity: critical | major | minor, claim_ids, message, evidence}.
- Rules:
  - Allergy vs recommended drug (ingredient and class via RxNorm).
  - Contraindication vs active conditions.
  - Drug-drug interaction vs current medications.
  - Dose range per indication; renal adjustment using eGFR from the record.
  - Patient-data contradiction (report states a value that differs from the record).
  - Red-flag coverage: if visible data meets red-flag criteria (configurable table, e.g., SpO2 < 90%, SBP < 90 mmHg), the report must address it.
- Curated tables in `configs/safety/` (dose ranges, contraindications, red-flag criteria) for drugs and conditions in the golden-set specialties. Each row has a source reference and `status: draft` until physician-reviewed (checkpoint H4).

## Acceptance criteria (write these as tests first)
- Every rule has at least one positive and one negative unit test.
- Rules are deterministic (property test: same input, same output).
- The engine refuses to run with a draft table in `production` mode (allowed in dev with a warning).

## Deliverables
- `src/vh/verification/rules/`, `configs/safety/`, ADR-0005
- `docs/steps/STEP-25.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-25.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
