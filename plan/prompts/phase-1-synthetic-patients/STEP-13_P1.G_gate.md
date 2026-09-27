# STEP 13 of 54 | P1.G: Phase 1 GATE | Synthetic Patients & Case Builder

- **Run after:** STEP 07, STEP 08, STEP 09, STEP 10, STEP 11, STEP 12 all show Status: DONE. Human checkpoint(s) H1 completed.
- **If PASS, next:** STEP 14 (P2.1): `plan/prompts/phase-2-rag/STEP-14_P2.1_source-adapters.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 1 is complete. Phase 2 must not start until this gate reports PASS.

## Phase goals
- Reproducible Synthea generation with valid FHIR output.
- Custom modules only where built-ins were insufficient, clinically documented.
- Patient store loaded idempotently and queryable.
- AgentView isolation proven; zero leakage.
- Case Builder deterministic, consistent and plausible; physician spot-check passed.

## Metrics (compared with `configs/thresholds.yaml`)
- `cases.fhir_valid_rate`
- `cases.leakage_count`
- `cases.plausibility_pass_rate`
- `cases.spotcheck_defect_rate_max`

## Required sign-offs
- `docs/signoffs/H1-spotcheck.md`

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 07, STEP 08, STEP 09, STEP 10, STEP 11, STEP 12. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 2. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-1-pass`.

## Gate report: write to `docs/phase-reports/phase-1.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
