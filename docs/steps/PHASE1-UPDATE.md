# Phase 1 Update Report — Structured Case Extraction & Mandatory Harrison Retrieval

- **Status**: DONE (implementation + tests green). Phase 2 NOT started per owner instruction.
- **Scope**: `prompt FOR UPDATE/01_Phase1_*` only. No generation, validation-layer, UI-redesign or RL-export changes beyond the 503 safety latch.
- **Date**: 2026-10-04 (conditional-approval fixes applied same day)
- **ADR**: `docs/decisions/ADR-0017-phase1-case-extraction-retrieval.md`

---

## 1. What changed (files touched)

| File | Owner | Change |
|---|---|---|
| `src/vh/cases/structured_case.py` (new) | Software Engineer | `StructuredCase` + `extract_structured_case()` — never invents; absent → null + `missing_data` |
| `src/vh/cases/retrieval_log.py` (new) | Software Engineer | `RetrievalLog` (queries, chunk_ids, scores, full text) + `MissingRetrievalLogError` hard guard |
| `src/vh/rag/sources/base.py` | Software Engineer | `SourceDocument` += nullable `edition/chapter_number/chapter_title/section_heading/page`; new `SourceSearchHit` + `SourceAdapter.search()` |
| `src/vh/rag/sources/harrison.py` (new) | Software Engineer | Sole Harrison-specific logic; semantic-first `search()` over existing `harrison_embeddings.npy` (all-MiniLM-L6-v2, cosine [0,1]) + lexical rerank; lexical-only fallback tagged |
| `src/vh/rag/sources/__init__.py` | Software Engineer | Export Harrison adapter |
| `scripts/backfill_harrison_metadata.py` (new) | Software Engineer | JSON-only backfill; refuses without backup; verifies `.npy` untouched |
| `data/knowledge/harrison_full_collection.json` (gitignored artifact) | — | Enriched in place: +`edition/chapter_number/chapter_title/section_heading` (explicit nulls) |
| `data/knowledge/harrison_chunks.json`, `internal_medicine_collection.json` (tracked) | — | Same enrichment (20 entries each) |
| `data/knowledge/backup_phase1_20261004_002547/` (new, on disk) | — | Full pre-change backup of the 4 JSON files |
| `src/vh/rag/retrieval.py` (additive section) | AI Engineer | Two-pass queries (`build_pass1_query`, `build_pass2_queries`), `dedupe_and_cap`, `two_pass_retrieve`, `<harrison_chunk>` formatter; `top_k` default 6, threshold provisional 0.01 on cosine scale [0,1], UNTUNED |
| `src/vh/generation/pipeline.py` (additive) | AI Engineer | `require_retrieval_log`, `run_with_log`, `INSUFFICIENT_GROUNDING`; legacy `run()` untouched |
| `src/vh/common/artifacts.py` | Software Engineer (guardian) | FROZEN — no edits |
| `src/vh/generation/report.py` | Software Engineer (guardian) | FROZEN — no edits (Phase 2 owns schema) |
| `configs/validation/icd10_titles.json` (new) | Medical Expert | Seed: `J18.9` only, CMS/WHO cited; full import is owner-run in Phase 3 |
| `tests/fixtures/phase1/charles_brown_realistic.json` (new) | QA Engineer | Realistic CAP fixture, `is_synthetic=true` |
| `tests/test_phase1_update_acceptance.py` (new, 15 tests) | QA Engineer | Guard, two-pass, null-missing, metadata, adapter, 503 contract |
| `backend/api/router.py` (latch only) | Software Engineer | `POST /api/rl/train` → 503 until `VH_ALLOW_RL_TRAIN=true` (Phase 5) |
| `frontend/.../RLDatasetModal.tsx`, `.../ReviewedReportsSection.tsx` (503 message only) | Software Engineer | 503-specific disabled message + `data-testid="train-blocked-503"` |
| `frontend/src/components/rl/__tests__/RLTrainBlocked503.test.tsx` (new) | QA Engineer | 503 message + modal-usable test |

## 2. Test results

- New: `tests/test_phase1_update_acceptance.py` — **16/16 passed** (incl. semantic-embedding test).
- Full backend: **341 passed** (`tests` + `backend/tests`, slow/eval deselected) + **7 passed** (`test_step_23/28`) = **348 passed, 0 failed**. Secret scan: clean.
- Frontend: **10 files, 39/39 vitest passed** (incl. new 503 test).
- Endpoints (TestClient): `GET /api/health` 200, `GET /api/knowledge/search` 200, `GET /api/rl/train/status` 200, `POST /api/rl/train` **503** with Phase 5 detail.
- `.npy` untouched: `harrison_embeddings.npy` sha256 `57fb55…bfb2a59` identical before/after; script reports both `.npy` UNCHANGED.
- Semantic proof: `HarrisonAdapter.search()` returns `retrieval_mode=semantic-hybrid`, scores in [0,1]; embeddings verified `(31427, 384)` float32, rows L2-normalized, row *i* ↔ collection entry *i*; query model `all-MiniLM-L6-v2` loaded from local cache (same id + mean-pooling + 512 truncation as builder).

## 3. Backfill census — CORRECTED (amendment 1 + condition 3)

The first report's "full 31,467 / partial 0" summary was wrong (it did not count `section_heading`). Corrected per-field counts for `harrison_full_collection.json` (31,427 entries):

| Field | Present | Null |
|---|---|---|
| `edition` | 31,427 | 0 |
| `chapter_number` | 31,193 | **234** (front-matter, explicit null → counts as partial) |
| `chapter_title` | 31,427 | 0 |
| `section_heading` | 0 | **31,427** (source has no distinct section data: `topic == chapter` on every full-book chunk) |
| `page` | 31,427 | 0 |
| **Full (all five)** | **0** | — |
| **Partial** | **31,427** | — |

`id` order and `text` byte-identical to `data/knowledge/backup_phase1_20261004_002547/` (kept on disk, excluded from git). The 20-item collections carry `section_heading` (distinct topics) but no parseable `chapter_number`.

## 3b. Production path (condition 2)

- **Production today uses NEITHER `run()` NOR `run_with_log()`.** Serving path is `backend/main.py` → `backend/simulation/orchestrator.py` → `backend/llm/medgemma_service.py`; it never enters `src/vh/generation/pipeline.py` (`run()` serves only the eval harness). Production generation currently has NO retrieval guard.
- **Confirmed for Phase 2**: backend generation will be rewired through `run_with_log()` with mandatory `retrieval_log`; after Phase 2, no production path may generate without retrieval.

## 4. Review-record audit (amendment: audit ALL, read-only, no re-flagging in Phase 1)

Source: `data/aivh.db` (2026-10-04). Nothing modified.

| Finding | Count |
|---|---|
| `clinical_reports` total | 16 |
| Charles Brown ×3 dup (`CASE-SYNTH-pat-101-0001`, `chief_complaint='Pneumonia'` → `Undifferentiated Acute Medical Illness` @0.70) | 3 |
| Robert Miller/CASE-101 ×12 dup (identical NSTEMI @0.94) | 12 |
| Concurrent-patient report ×1 | 1 |
| `physician_reviews` total (3× `Dr. Marcus Vance, MD, FACP`, 6× `Dr. Sarah Attending, MD`) | 9 |
| Contradictory: 3/5-approved-with-top-grades ×1; 1/5-rejected-with-top-grades ×1 | 2 |
| `patients` total (1 Brown, 6 Gerald Montgomery dup, 25 `Concurrent Patient` stress-test mocks) | 32 |
| `dpo_feedback_pairs` | 0 (nothing exported — good) |

Flagging (`is_synthetic`), dedup and manifest are Phase 5 work. New Charles Brown fixture is `is_synthetic=true` and reserved as a Phase 6 negative fixture.

## 5. Validation set & threshold (amendment 5; condition 5)

- No dedicated retrieval-threshold validation set existed: `eval/golden/v1` (60 cases) marks all Harrison refs `unmappable` (copyright) and maps only guideline chunks — unsuitable for Harrison threshold tuning.
- Threshold stays **PROVISIONAL / UNTUNED**: `similarity_threshold=0.01` on the **cosine-similarity scale [0, 1]**, `top_k_per_query=6`, `max_total_chunks=24`. Nothing tuned on fixtures.
- Approved set prepared: `eval/retrieval_validation_v1/labels.jsonl` — **40 pairs** (10 queries × top-4 across CAP/ACS/DKA), **40/40 `pending physician review`**, all `semantic-hybrid`, `is_synthetic=true`, plus `README.md` with review instructions and metric plan (precision@k/recall@k over {0.0, 0.01, 0.05, 0.1}). Generated by `scripts/prepare_retrieval_validation_set.py`. **No tuning until the owner approves the labels.**

## 6. How to test

```powershell
py -3.13 -m pytest tests/test_phase1_update_acceptance.py -q
py -3.13 scripts/backfill_harrison_metadata.py   # idempotent; verifies .npy UNCHANGED
$env:PYTHONPATH='src;.'; py -3.13 ..\Temp\opencode\check_endpoints.py
pnpm vitest run src/components/rl/__tests__/RLTrainBlocked503.test.tsx   # inside frontend/
```

## 7. Open issues / decisions for owner

1. Approve `eval/retrieval_validation_v1` proposal (§5) before any threshold tuning.
2. Owner-run full CMS ICD-10-CM tabular import in Phase 3 (seed has J18.9 only).
3. Phase 5: `is_synthetic` flagging + dedup + manifest; then set `VH_ALLOW_RL_TRAIN=true`.
4. Phase 2 will deprecate legacy `GroundedGenerationPipeline.run()` in favour of `run_with_log()` and rewire generation to the Phase 2 schema — needs owner go-ahead (STOPPED here as instructed).
