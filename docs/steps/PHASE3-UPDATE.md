# Phase 3 Update Report — Automated Validation Layer (V1–V12)

- **Status**: DONE (validator + wiring + tests green). Phase 4 NOT started.
- **Scope**: `prompt FOR UPDATE/03_Phase3_*` + owner conditions 1–5 (live run PARTIAL, see §2).
- **Date**: 2026-10-04
- **ADRs**: `docs/decisions/ADR-0019-phase3-validation-failsafe.md` (validator, fail-safe, parity criteria)

---

## 1. What changed (files touched)

| File | Owner | Change |
|---|---|---|
| `src/vh/verification/phase3.py` (new) | AI Engineer | V1–V12, VALID/FAILED statuses, retry feedback, failed-list writer |
| `configs/validation/phase3.yaml` (new) | AI Engineer | Tunables (0.6/0.6/0.9/12-word/0.4/3-findings; owner promotes) |
| `configs/validation/vague_diagnoses.yaml` (new) | Medical Expert | 9 vague labels (draft pending review) |
| `configs/validation/completeness_rules.yaml` (new) | Medical Expert | 19 rules: CAP + sepsis approved, 17 draft audit-only |
| `configs/validation/icd10_cm_titles_FY2027.json` (new) | Medical Expert | 98,403 official CMS titles (74,879 billable) |
| `scripts/import_icd10_cm.py` (new) | Medical Expert | Official-file importer with provenance |
| `scripts/live_model_phase2_run.py` (new) | AI Engineer | Resume-safe live evidence runner (+ JSONL) |
| `src/vh/generation/pipeline.py` (validation loop) | AI Engineer | VALID/FAILED wiring, max 2 retries, failed logging |
| `src/vh/generation/medgemma.py` (live-driven fixes) | AI Engineer | retry_feedback, provenance stamp, settings forward, system/user split, 8192 budget, balanced-JSON extractor, timeout accounting |
| `backend/clinical/models.py` +`tools.py`, `grounded_shim.py`, `dpo_generator.py`, `internal_medicine.py` (fail-safe) | Software Engineer | `ungrounded` tag, `GroundedFailedError`, RL exclusion |
| `tests/test_phase3_update_acceptance.py` (new, 17 tests) | QA Engineer | Per-check + 5 negative + pipeline + fail-safe tests |
| `eval/retrieval_validation_v1/` | Medical Expert | Untouched (still pending your review; no tuning done) |

## 2. Test results

- New: **17/17 passed** (12 V-check incl. fake chunk_id/quote, repeated output, diagnosis-in-complaint, copied paragraph).
- Full backend: **384 + 7 = 391 passed, 0 failed**. Frontend **39/39**. Secret scan clean.
- Endpoint contracts re-verified (Phase 2 file, 15×200 + train 503).

## 3. Condition answers

1. **Live-model run — PARTIAL (throughput-blocked, 4/20 distinct cases).** All outputs below are **live-medgemma-4b** (model load verified True every run); the offline heuristic appears NOWHERE in live runs (unit tests only).
   - Full pipeline rows: Brown + ACU-000 + ACU-001 under pre-fix prompt (archived to `live_model_phase2_prefixed_prompt.jsonl`, NOT counted) and Brown once under near-final config (`live_model_phase2.jsonl`).
   - Parse-failure rate (full runs): **4/4 failed** — 3× JSON-decode (root causes found and fixed: schema absent from prompt; settings not forwarded), 1× 900s timeout (attempt accounting fixed after; that row shows att=0 artifact).
   - Single-attempt diagnostics (post-fix): echo-inputs → thinking+truncated-JSON (4096 budget) → **complete schema-shaped JSON** (8192 budget, rejected only for code fences — checker working as designed).
   - Retries: every failed run consumed the full 3-attempt budget. box_2d: **0 occurrences** in all live raws. Repetition: 0 sentence-repeat flags on completed JSONs.
   - Latency: full cases **1066–2113s** (mean ~1400s); single attempts 41s (early-stop echo) to 900s (timeout). Throughput ≈ **1 case/hour** → 20 cases ≈ 20h.
   - Resume-safe script + JSONL persist state; remainder runs unattended overnight on your go-ahead. No tuning performed on these outputs.
2. **Fail-safe**: grounded outcomes exactly VALID / INSUFFICIENT_GROUNDING / FAILED. Flag=grounded + any failure → `GroundedFailedError` → legacy fallback tagged `ungrounded=true` (persisted in `raw_json`, serialized in API). `compile_dpo_corpus` permanently skips ungrounded (test-proven). Flag=legacy behavior grandfathered (Phase 5 quarantines it via VALID-only export). No silent fallback exists.
3. **Parity criteria**: written with numbers in ADR-0019 §6 (validator ≥95%, parse ≥80%, 0 post-retry defects, 100% contracts, 0 frontend regressions, CASE-101 encounter parity, RL quarantine). **Not flipping until you approve.**
4. **Push + hygiene**: `phase2-medgemma-generation` + tag `phase2-done` pushed to private `mohamadorfali2006/AI-VH` (verified via ls-remote — see §5). Hygiene: no `.db`/weights/PDFs/full-collection in git; no secrets (scan clean); no real patient data (only synthetic Synthea bundles + fixtures); only Harrison text in git = two pre-existing 20-excerpt fixture JSONs (133KB each, short excerpts — flagged for your call: keep as fixtures or `git rm --cached`).
5. **ICD-10**: CMS FY2027 official zip (CDC mirror unreachable from this network; CMS mirror used), 98,403 titles; J18.9 verified against the task prompt. V4 excludes R/Z symptom chapters so symptom complaints are not flagged.

## 4. Live-model fixes applied (evidence-driven, all tested)

Schema embedded in prompt; temperature/repetition/budget forwarded to live `generate()`; system/user turn split; 8192-token budget; balanced-JSON extractor; code-stamped provenance; differential capped at 1024 tokens; 900s live timeout default; timeout attempts counted in stats.

## 5. Git state

- Pushed: `phase1-case-extraction-retrieval` + `phase1-done` (earlier), `phase2-medgemma-generation` + `phase2-done` (this phase, tag on accepted Phase-2 tip `62c16a0`; hardening fixes ride the Phase 3 commit below).
- To commit: Phase 3 work on new branch `phase3-validation-layer` (unpushed; push only on instruction).

## 6. How to test / resume / rollback

```powershell
py -3.13 -m pytest tests/test_phase3_update_acceptance.py -q
py -3.13 scripts/live_model_phase2_run.py --max-cases 5   # resume-safe; appends JSONL
$env:VH_PIPELINE="legacy"    # rollback (default); "grounded" opts in
```

## 7. Open issues for owner

1. Complete the 20-case live run (overnight job?) and review retrieval-validation labels — no tuning until both land.
2. Decide the two tracked 20-excerpt Harrison fixture JSONs (keep vs untrack).
3. Approve parity criteria (ADR-0019 §6) before any flag flip.
4. Phase 4 owns `compat.py` removal, FAILED-list UI, and `ungrounded` display.
