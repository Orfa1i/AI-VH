# STEP 50 of 54 | P8.G: Phase 8 GATE | Virtual Hospital Environment (2D then 3D)

- **Run after:** STEP 46, STEP 47, STEP 48, STEP 49 all show Status: DONE.
- **If PASS, next:** STEP 51 (P9.1): `plan/prompts/phase-9-advanced/STEP-51_P9.1_imaging-tools.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 8 is complete. Phase 9 must not start until this gate reports PASS.

## Phase goals
- Read-only event stream with replay and resume.
- 2D dashboard driven only by events.
- 3D scene meeting performance targets.
- Proven zero clinical side effects from the UI.

## Metrics (compared with `configs/thresholds.yaml`)
- `ui.min_fps`
- `ui.max_load_s`
- `ui.max_sync_lag_ms`
- `ui.output_divergence_count`

## Required sign-offs
- (none)

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 46, STEP 47, STEP 48, STEP 49. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 9. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-8-pass`.

## Gate report: write to `docs/phase-reports/phase-8.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
