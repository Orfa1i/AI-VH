# STEP 45 of 54 | P7.G: Phase 7 GATE | Fine-Tuning & Model Lifecycle

- **Run after:** STEP 41, STEP 42, STEP 43, STEP 44 all show Status: DONE. Human checkpoint(s) H7 completed.
- **If PASS, next:** STEP 46 (P8.1): `plan/prompts/phase-8-virtual-hospital/STEP-46_P8.1_event-stream-api.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 7 is complete. Phase 8 must not start until this gate reports PASS.

## Phase goals
- Curated dataset split by patient, zero contamination.
- Reproducible LoRA fine-tuning with full lineage.
- Registry with evidence-gated promotion, shadow mode and rollback.
- Candidate beats production with zero safety regressions and blinded physician preference.

## Metrics (compared with `configs/thresholds.yaml`)
- `training.min_reviewed_cases`
- `training.safety_regressions`
- `training.must_beat_production`

## Required sign-offs
- `docs/signoffs/H7-blinded-review.md`

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 41, STEP 42, STEP 43, STEP 44. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 8. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-7-pass`.

## Gate report: write to `docs/phase-reports/phase-7.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
