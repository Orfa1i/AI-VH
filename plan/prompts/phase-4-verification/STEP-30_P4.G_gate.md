# STEP 30 of 54 | P4.G: Phase 4 GATE | Verification Layer

- **Run after:** STEP 25, STEP 26, STEP 27, STEP 28, STEP 29 all show Status: DONE. Human checkpoint(s) H4 completed.
- **If PASS, next:** STEP 31 (P5.1): `plan/prompts/phase-5-agents/STEP-31_P5.1_environment-simulator.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 4 is complete. Phase 5 must not start until this gate reports PASS.

## Phase goals
- Deterministic safety rules with physician-reviewed tables.
- Grounding judge calibrated against physician labels.
- Runtime guardrails that fail closed; verified/flagged routing with reasons.
- DeepEval metrics enforced in CI.
- Fault-injection suite proves detection without excessive false flags.

## Metrics (compared with `configs/thresholds.yaml`)
- `verification.critical_fault_detection`
- `verification.noncritical_fault_detection`
- `verification.false_flag_rate_max`
- `verification.judge_kappa_min`
- `verification.faithfulness_min`
- `verification.contextual_relevancy_min`
- `verification.p95_latency_s`

## Required sign-offs
- `docs/signoffs/H4-safety-and-judge.md`

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 25, STEP 26, STEP 27, STEP 28, STEP 29. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 5. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-4-pass`.

## Gate report: write to `docs/phase-reports/phase-4.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
