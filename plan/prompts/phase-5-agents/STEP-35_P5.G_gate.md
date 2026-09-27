# STEP 35 of 54 | P5.G: Phase 5 GATE | Agents & Orchestration (headless)

- **Run after:** STEP 31, STEP 32, STEP 33, STEP 34 all show Status: DONE. Human checkpoint(s) H5 completed.
- **If PASS, next:** STEP 36 (P6.1): `plan/prompts/phase-6-feedback/STEP-36_P6.1_feedback-data-model.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 5 is complete. Phase 6 must not start until this gate reports PASS.

## Phase goals
- Environment releases hidden data only via orders; never invents data.
- Five specialised agents with tool-layer permissions.
- Orchestrator with budgets, loop detection and explicit termination states.
- Encounter scoring and exact replay.

## Metrics (compared with `configs/thresholds.yaml`)
- `agents.permission_violations`
- `agents.runaway_loops`
- `agents.replay_mismatch_count`
- `agents.encounter_score_min`

## Required sign-offs
- (none)

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 31, STEP 32, STEP 33, STEP 34. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 6. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-5-pass`.

## Gate report: write to `docs/phase-reports/phase-5.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
