# STEP 24 of 54 | P3.G: Phase 3 GATE | Grounded Clinical Generation (MedGemma)

- **Run after:** STEP 20, STEP 21, STEP 22, STEP 23 all show Status: DONE. Human checkpoint(s) H3 completed.
- **If PASS, next:** STEP 25 (P4.1): `plan/prompts/phase-4-verification/STEP-25_P4.1_safety-rules-engine.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 3 is complete. Phase 4 must not start until this gate reports PASS.

## Phase goals
- Report schema enforces claim-evidence links and referential integrity.
- MedGemma adapter with constrained output and no partial reports.
- Grounded pipeline with working abstention and zero fabricated citations.
- RAG proven better than no-RAG; production variant chosen (ADR-0004).

## Metrics (compared with `configs/thresholds.yaml`)
- `generation.schema_valid_rate`
- `generation.fabricated_citation_rate`
- `generation.abstention_correct_rate`
- `generation.dx_top3_min`
- `generation.rag_beats_baseline`

## Required sign-offs
- (none)

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 20, STEP 21, STEP 22, STEP 23. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 4. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-3-pass`.

## Gate report: write to `docs/phase-reports/phase-3.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
