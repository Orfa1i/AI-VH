# STEP 40 of 54 | P6.G: Phase 6 GATE | Doctor Review & Feedback Store

- **Run after:** STEP 36, STEP 37, STEP 38, STEP 39 all show Status: DONE.
- **H6 note (owner policy):** real-physician usability validation (H6) is an
  OPTIONAL external milestone. It is NOT a prerequisite for implementation or
  for this gate, and it is never evaluated here. Do NOT create, reference, or
  imply any `docs/signoffs/H6-usability.md` content.
- **If PASS, next:** STEP 41 (P7.1): `plan/prompts/phase-7-fine-tuning/STEP-41_P7.1_dataset-curation.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 6 is complete. Phase 7 must not start until this gate reports PASS.

## Phase goals
- Original AI reports provably immutable; edits reconstruct finals exactly.
- Review API with authorisation and independent overlap reviews.
- Review UI in the existing shell, tested end-to-end.
- Agreement measured; versioned snapshots are the only training input.
- Automated clinical validation substitute passes (in place of H6): AI-generated
  reports evaluated against synthetic-case Ground Truth and the certified
  clinical validation rules. Real-physician usability remains future/external
  work and is NOT claimed by this gate.

## Validation tiers (do not conflate)
1. **Automated system validation** (evaluated by this gate): code, tests,
   harness eval, overlap mechanism, agreement-pipeline correctness.
2. **Synthetic-case evaluation** (evaluated by this gate): encounter scoring
   of AI reports against golden Ground Truth; explicitly not physician judgment.
3. **Future real-physician usability validation** (H6, OPTIONAL external):
   NOT performed and NOT claimed here. Tracked separately by the owner.

## Metrics (compared with `configs/thresholds.yaml`)
- `review.overlap_fraction` (mechanism target; proven by simulation)
- `agents.encounter_score_min` (synthetic-case evaluation mean; re-measured here)
- `review.kappa_min`: agreement PIPELINE correctness is proven by unit tests on
  known-value fixtures; kappa itself is UNMEASURED (no overlap review data
  exists) and is recorded as such -- never as a pass on physician agreement.

## Required sign-offs
- (none for implementation; H6, when/if ever performed externally, lives at
  `docs/signoffs/H6-usability.md` and is never a gate input)

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 36, STEP 37, STEP 38, STEP 39. Any missing or BLOCKED report means FAIL.
2. Required sign-offs: none. Confirm no `docs/signoffs/H6-usability.md` is being
   implied or fabricated: the file must either not exist (normal) or, if the
   owner later adds it externally, be left untouched and unread for gating.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Re-measure the synthetic-case evaluation: run the encounter pipeline over all
   verified golden cases (seed 42), score against Ground Truth, and compare the
   mean encounter score with `agents.encounter_score_min`. Compare the overlap
   mechanism target with `review.overlap_fraction`. A NOT SET (`null`) threshold
   is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 7. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-6-pass`.

## Gate report: write to `docs/phase-reports/phase-6.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL / UNMEASURED (with reason)
- Each phase goal: evidence
- Validation tiers stated separately; explicit non-claim on physician usability
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
