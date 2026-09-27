# STEP 06 of 54 | P0.G: Phase 0 GATE | Foundations, Governance & Evaluation Harness

- **Run after:** STEP 01, STEP 02, STEP 03, STEP 04, STEP 05 all show Status: DONE. Human checkpoint(s) H0.1, H0.2 completed.
- **If PASS, next:** STEP 07 (P1.1): `plan/prompts/phase-1-synthetic-patients/STEP-07_P1.1_synthea-runner.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 0 is complete. Phase 1 must not start until this gate reports PASS.

## Phase goals
- Repository layout applied; CI blocks merges on any failure.
- Secrets scanning active locally and in CI.
- Tracing with run_id and versioned artifacts working.
- Evaluation harness working; golden set v1 released and frozen.
- Governance sign-off recorded.

## Metrics (compared with `configs/thresholds.yaml`)
- `golden.min_verified_cases`

## Required sign-offs
- `docs/signoffs/H0.1-governance.md`
- `docs/signoffs/golden-v1.md`

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 01, STEP 02, STEP 03, STEP 04, STEP 05. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 1. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-0-pass`.

## Gate report: write to `docs/phase-reports/phase-0.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
