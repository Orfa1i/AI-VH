# ADR-0019: Phase 3 Validation Layer, Fail-Safe and Parity Criteria

- **Status**: Accepted (Phase 3 only)
- **Date**: 2026-10-04
- **Deciders**: Project Owner (conditions) & 5-agent workflow (implementation)
- **Governing Documents**: `prompt FOR UPDATE/03_Phase3_*`, owner conditions 1–5
- **Owner**: AI Engineer (validator/wiring); Medical Expert (terminology/rules content); Software Engineer (fail-safe seam)

---

## 1. File ownership (exclusive)

| File | Owner | Change |
|---|---|---|
| `src/vh/verification/phase3.py` (new) | AI Engineer | V1–V12, statuses, retry feedback, failed-list writer |
| `configs/validation/phase3.yaml` (new) | AI Engineer | Validator tunables (owner promotes to thresholds.yaml) |
| `configs/validation/vague_diagnoses.yaml` (new) | Medical Expert | Vague-label list (draft pending review) |
| `configs/validation/completeness_rules.yaml` (new) | Medical Expert | 19 rules: 2 approved (CAP, sepsis — prompt examples), 17 draft audit-only |
| `scripts/import_icd10_cm.py` (new) | Medical Expert | Official CMS FY2027 import (content owner) |
| `configs/validation/icd10_cm_titles_FY2027.json` (new) | Medical Expert | 98,403 official titles (74,879 billable) |
| `src/vh/generation/pipeline.py` (validation loop) | AI Engineer | VALID/FAILED wiring, max 2 retries, failed logging |
| `src/vh/generation/medgemma.py` (retry_feedback, provenance stamp, settings forward, system/user split, extractor) | AI Engineer | Evidence-driven live-model fixes (§4) |
| `backend/clinical/models.py` (+`ungrounded`), `backend/clinical/tools.py` (passthrough) | Software Engineer | Fail-safe tagging |
| `backend/simulation/grounded_shim.py` (`GroundedFailedError`) | Software Engineer | Explicit failure, never silent |
| `backend/rl/dpo_generator.py` (corpus skip) | Software Engineer | Permanent RL exclusion of ungrounded |
| `tests/test_phase3_update_acceptance.py` (16 tests) | QA Engineer | Per-check + negative + pipeline + fail-safe tests |

## 2. Score scales and thresholds (all provisional; owner promotes)

- Cosine similarity [0,1] (retrieval threshold 0.01, UNTUNED, validation set pending review).
- Harrison-grounded fraction [0,1], minimum **0.6** (recomputed in code, never model-trusted).
- Quote fuzzy ratio [0,1], minimum **0.9** (normalized substring fast-path, sliding-window fallback).
- Verbatim span **12 words**; ROUGE-L F1 maximum **0.4** (dependency-free LCS).
- Case-findings minimum **3** (or fewer when the case provides fewer; vacuous pass at zero).
- Repetition: sentence ≥3× fails; 8-gram >2× fails.
- Regeneration: max **2 retries** with the error list + synthesis rewrite sentence.

## 3. ICD-10 provenance (condition 5)

- CMS "2027 Code Descriptions in Tabular Order (ZIP)",
  `https://www.cms.gov/files/zip/2027-code-descriptions-tabular-order.zip`
  (CDC NCHS mirror `https://ftp.cdc.gov/.../ICD10CM/2027/`, unreachable from this
  network at import time; CMS mirror used). Order file `icd10cm_order_2027.txt`
  parsed by `scripts/import_icd10_cm.py` → 98,403 titles. Spot check J18.9 =
  "Pneumonia, unspecified organism" matches the task prompt. Seed file retained
  as provenance record; V4 loads the full file. V4 excludes R/Z symptom chapters
  so symptom complaints (fever, cough, chest pain) are not flagged as diagnoses.

## 4. Live-model findings (condition 1, all outputs labelled live vs heuristic)

- Serving stack has NO constrained decoding (`guided_decoding_available() is False`,
  asserted); strict parse + retry only.
- Measured live behavior (MedGemma 4B, RTX 4060): the model emits a thinking
  preamble (`<unused94>thought` + markdown analysis) and only then the JSON
  assessment. Three evidence-driven fixes resulted: (1) the v2 JSON schema is now
  embedded in the prompt (it was absent — root cause of input-echoing); (2) Phase 2
  temperature/repetition/max-tokens are forwarded to live `generate()` (they were
  silently ignored); (3) system/user turn split per the chat template's design;
  (4) `max_new_tokens` 4096 → 8192 (thinking + JSON must fit — 4096 truncated a
  complete assessment mid-object); (5) extractor prefers the last balanced JSON
  object (preamble-safe); (6) provenance (`report_id`, `prompt_version`) is
  code-stamped, never model-trusted; (7) differential micro-call bounded to 1024
  tokens; (8) live timeout default 900s.
- Throughput (~35+ min/case end-to-end, high variance incl. 900s timeouts) bounds
  the 20-case run: resume-safe script `scripts/live_model_phase2_run.py` appends
  to `eval/reports/live_model_phase2.jsonl`. Early rows under the pre-fix prompt
  were archived to `live_model_phase2_prefixed_prompt.jsonl` (not counted).
  Final counts in the Phase 3 report; remainder (if any) continues as an
  unattended job — no threshold tuning until labels + metrics land.

## 5. Fail-safe semantics (condition 2)

- Grounded path outcomes are exactly VALID / INSUFFICIENT_GROUNDING / FAILED.
  Generation without retrieval is refused (`MissingRetrievalLogError`).
- Shim contract: flag=legacy → None (grandfathered pre-grounded behavior,
  quarantined by the Phase 5 VALID-only export). Flag=grounded + any grounded
  failure → `GroundedFailedError` (explicit, never silent) → caller falls back
  to legacy AND tags `ungrounded=true`.
- `ungrounded=true` reports: serialized in API responses (display wiring is
  Phase 4), permanently excluded from RL export (`compile_dpo_corpus` skips;
  test-proven), and never re-flagged (field persists in `raw_json`).

## 6. Parity criteria for flipping VH_PIPELINE to grounded (condition 3)

The default flips ONLY after ALL of the following are measured and the owner
approves them in writing. Proposed numbers (owner may tighten, never loosen
without a recorded reason):

1. **Validator pass rate**: ≥95% of the 20-case live set resolves VALID or
   correctly-classified INSUFFICIENT_GROUNDING (0 mishandled FAILED: every
   FAILED is stored with validation + raws and listed in `failed_generations`).
2. **Parse success rate** (strict parse, live model): ≥80% of generation calls
   succeed within the 2-retry budget.
3. **Zero post-retry defects**: 0 `box_2d`/coordinate/fence occurrences and
   0 repetition failures in final VALID reports.
4. **Endpoint contracts**: 100% of pre-existing routes respond (GET 200 or
   route-present for generative routes), verified on the flipped flag.
5. **Frontend regressions**: 0 failing vitest + production build green.
6. **Encounter parity**: grounded-mode `run_encounter_simulation` preserves the
   benchmark diagnosis on CASE-101 (NSTEMI) and shows no higher
   `generation_failed` rate than the legacy baseline on the same seeds.
7. **RL quarantine**: 0 ungrounded/failed/insufficient reports in any export
   (test-proven filter + manifest audit in Phase 5).
