# STEP 19 of 54 | P2.G: Phase 2 GATE | Multi-Source RAG

- **Run after:** STEP 14, STEP 15, STEP 16, STEP 17, STEP 18 all show Status: DONE. Human checkpoint(s) H2 completed.
- **If PASS, next:** STEP 20 (P3.1): `plan/prompts/phase-3-generation/STEP-20_P3.1_report-schema.md`
- **If FAIL:** `plan/prompts/_templates/FIX-LOOP.md`, then run this gate again.

> Read `CLAUDE.md`. This step builds nothing new. It decides whether Phase 2 is complete. Phase 3 must not start until this gate reports PASS.

## Phase goals
- All sources ingested through licence-checked adapters; NABD still works.
- Structure-aware chunks, each traceable to exact source text.
- Versioned dense + keyword indexes; superseded content excluded.
- Unified hybrid retrieval API with diversity and filters.
- Retrieval configuration chosen by measurement (ADR-0003).

## Metrics (compared with `configs/thresholds.yaml`)
- `retrieval.recall_at_10`
- `retrieval.mrr_min`
- `retrieval.traceability_rate`
- `retrieval.stale_retrieval_count`
- `retrieval.p95_latency_s`

## Required sign-offs
- `docs/signoffs/H2-chunkmap.md`

## Procedure
1. Confirm `docs/steps/STEP-NN.md` exists with Status: DONE for each of: STEP 14, STEP 15, STEP 16, STEP 17, STEP 18. Any missing or BLOCKED report means FAIL.
2. Confirm each required sign-off file exists, is dated, names the reviewer and states PASS. You may read sign-offs; you may never write or edit them.
3. Run `make test-all` (full regression across all phases so far) and `make eval` on the latest frozen golden set with the current default configuration.
4. Compare every metric above with `configs/thresholds.yaml`. A NOT SET (`null`) threshold is FAIL. Never edit the thresholds.
5. Gap review: for each phase goal, cite the evidence (file, test, or eval report run_id). A goal without evidence is FAIL.
6. Decide:
   - **FAIL:** do not start Phase 3. Write the gate report listing every failure with its root cause, then follow `plan/prompts/_templates/FIX-LOOP.md`. After the fixes, run this gate again from step 1.
   - **PASS:** write the gate report and tag the commit `phase-2-pass`.

## Gate report: write to `docs/phase-reports/phase-2.md`
- **Result:** PASS | FAIL
- Commit hash; golden set version; artifact versions (index, prompt templates, model)
- Each metric: value vs threshold, PASS / FAIL
- Each phase goal: evidence
- Sign-offs checked
- If FAIL: every failure with root cause and the planned fix
