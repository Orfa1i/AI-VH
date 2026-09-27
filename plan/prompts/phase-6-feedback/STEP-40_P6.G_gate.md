# STEP 40 of 54 | P6.G: Phase 6 GATE | Doctor Review & Feedback Store

- **Run after:** STEP 36, STEP 37, STEP 38, STEP 39 all show Status: DONE. Human checkpoint(s) H6 completed.
- **If PASS, next:** STEP 41 (P7.1): `plan/prompts/phase-7-fine-tuning/STEP-41_P7.1_dataset-curation.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 6 is complete. Phase 7 must not start until this gate reports PASS.

## Phase goals
- Original AI reports provably immutable; edits reconstruct finals exactly.
- Review API with authorisation and independent overlap reviews.
- Review UI in the existing shell, tested end-to-end.
- Agreement measured; versioned snapshots are the only training input.
- Doctor usability test passed.

## Metrics (compared with `configs/thresholds.yaml`)
- `review.kappa_min`
- `review.overlap_fraction`

## Required sign-offs
- `docs/signoffs/H6-usability.md`

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 36, STEP 37, STEP 38, STEP 39. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 7. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-6-pass`.

## Gate report: write to `docs/phase-reports/phase-6.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
