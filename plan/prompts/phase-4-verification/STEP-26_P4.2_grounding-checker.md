# STEP 26 of 54 | P4.2: Claim grounding and citation checker

- **Phase 4:** Verification Layer
- **Run after:** STEP 25 (P4.1) report shows Status: DONE.
- **Next:** STEP 27 (P4.3): `plan/prompts/phase-4-verification/STEP-27_P4.3_guardrails-routing.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
An LLM judge can only be trusted after it is calibrated against physician labels. This step builds both the checker and the calibration kit.

## Task
- For each claim, judge whether its cited evidence supports it: supported | partial | unsupported, with a short rationale. Implement with an NLI model or an LLM judge through the adapter, using its own versioned prompt `grounding_judge@1`.
- The judge sees only the claim and its cited evidence: never ground truth, never other claims.
- Citation check: the evidence_id exists and was retrieved in this run.
- Calibration kit:
  - `vh verify calibration-export --n 100` produces a stratified labelling sheet of claim-evidence pairs for a physician.
  - `vh verify calibration-score` computes Cohen's kappa and a confusion matrix once labels exist in `docs/signoffs/H4-judge-labels.csv`.

## Acceptance criteria (write these as tests first)
- Tests on synthetic pairs with known labels (clearly supported, contradicted, unrelated).
- Deterministic settings (temperature 0, fixed prompt version).
- Calibration scoring is correct on a fixture with a known kappa.

## Deliverables
- `src/vh/verification/grounding.py`, judge prompt, calibration CLI, labelling sheet
- `docs/steps/STEP-26.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-26.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
