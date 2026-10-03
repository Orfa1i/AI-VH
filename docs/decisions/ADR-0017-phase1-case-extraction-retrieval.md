# ADR-0017: Phase 1 Case Extraction & Mandatory Harrison Retrieval

- **Status**: Accepted (Phase 1 only)
- **Date**: 2026-10-04
- **Deciders**: Project Owner (amendments) & 5-agent workflow (implementation)
- **Governing Documents**: `prompt FOR UPDATE/01_Phase1_*`, `00_Background_Problems_Found.md`, owner amendments 1–6
- **Owner**: Medical Expert (clinical spec); implementation owners per §1

---

## 1. File ownership (amendment 3; no two agents edit the same file)

| File | Owner | Phase 1 rule |
|---|---|---|
| `src/vh/common/artifacts.py` | Software Engineer (guardian) | FROZEN — no edits. Retrieval logs use `register_artifact()` as-is |
| `src/vh/generation/report.py` | Software Engineer (guardian) | FROZEN — no edits. Phase 2 schema migration owns this file |
| `src/vh/rag/sources/base.py` (`SourceDocument` + `SourceAdapter`) | Software Engineer | Extended with nullable Harrison metadata + `SourceSearchHit` + `search()` |
| `src/vh/cases/structured_case.py` (new) | Software Engineer | StructuredCase extractor |
| `src/vh/cases/retrieval_log.py` (new) | Software Engineer | RetrievalLog + hard guard |
| `src/vh/rag/sources/harrison.py` (new) | Software Engineer | Sole Harrison-specific logic |
| `scripts/backfill_harrison_metadata.py` (new) | Software Engineer | JSON-only backfill |
| `src/vh/rag/retrieval.py` (two-pass section) | AI Engineer | Two-pass queries, dedup/cap, threshold |
| `src/vh/generation/pipeline.py` (guard section) | AI Engineer | `require_retrieval_log`, `run_with_log`, `INSUFFICIENT_GROUNDING` |
| `configs/rag.yaml` | AI Engineer | Provisional values only; threshold UNTUNED |
| `configs/validation/icd10_titles.json` (new seed) | Medical Expert | Official-source seed only (§4) |
| `tests/test_phase1_update_acceptance.py` + `tests/fixtures/phase1/*` | QA Engineer | All Phase 1 tests + fixtures |
| `backend/api/router.py` (train latch only) | Software Engineer | 503 latch; no other backend changes |
| `frontend/.../RLDatasetModal.tsx`, `.../ReviewedReportsSection.tsx` (503 message only) | Software Engineer | 503 message + testid; no other UI changes |
| This ADR + validation-set statement | Medical Expert | Clinical correctness |

## 2. Production stack (canonical decision)

- Serving today: `backend/main.py` → `backend/api/router.py` → `backend/simulation/*`, `backend/llm/medgemma_service.py`, `backend/rag/*`. Frontend calls these endpoints.
- Canonical: `src/vh/*` is the source of truth for all 6 update phases. `backend/*` becomes a thin adapter over time.
- Phase 1 backend change is limited to the `/api/rl/train` 503 latch. All existing endpoints keep their URLs and response shapes.

## 3. Backfill safety (amendment 1; CORRECTED census 2026-10-04)

- Full backup taken before any change: `data/knowledge/backup_phase1_20261004_002547/` (4 JSON files, kept on disk, excluded from git).
- `.npy` embedding files never touched: `harrison_embeddings.npy` sha256 `57fb55149523506e36e6a7cc33ae8edfd36401352be1e1c038beb50e2bfb2a59` verified UNCHANGED after backfill; `braunwald_embeddings.npy` likewise UNCHANGED.
- Metadata JSON only: added explicit nullable `edition`, `chapter_number`, `chapter_title`, `section_heading` to `harrison_full_collection.json` (31,427 entries), `harrison_chunks.json` (20) and `internal_medicine_collection.json` (20). `id` order and `text` byte-identical to backup.
- Never fabricated: `page` kept from source; null where not determinable.
- CORRECTED per-field census (`harrison_full_collection.json`, 31,427 entries) — the earlier "full 31,467 / partial 0" summary was wrong because it did not count `section_heading`:

| Field | Present | Null |
|---|---|---|
| `edition` | 31,427 | 0 |
| `chapter_number` | 31,193 | **234** (front-matter, explicit null) |
| `chapter_title` | 31,427 | 0 |
| `section_heading` | 0 | **31,427** (source carries no distinct section data: `topic == chapter` for every full-book chunk) |
| `page` | 31,427 | 0 |
| **Full (all five present)** | **0** | — |
| **Partial** | **31,427** | — |

- The 20-item `harrison_chunks.json` / `internal_medicine_collection.json` have distinct topics, so all 20 carry `section_heading` (but no parseable `chapter_number`).

## 4. Null-missing rule (amendment 2)

- `extract_structured_case()` copies only explicitly provided keys. Absent values become None/empty and their names are appended to `missing_data`. No default vitals, durations, labs or findings are ever invented.
- Proven by `test_structured_extractor_never_invents_values` (sparse input → all null + full missing_data list).

## 5. ICD-10 titles (amendment 4)

- Official sources only: CMS ICD-10-CM FY2026 (`https://www.cms.gov/medicare/coding-billing/icd-10-codes`) and WHO ICD-10 2019 browser (`https://icd.who.int/browse10/2019/en`), both cited in `configs/validation/icd10_titles.json`.
- Seed contains solely `J18.9` (“Pneumonia, unspecified organism”) because that mapping is explicitly stated in the approved task prompt (`06_Phase6`). No titles were generated from model memory.
- Full tabular import is an owner-run step in Phase 3 (V4 diagnosis-term check). A placeholder importer note is recorded in the Phase 1 report.

## 6. Threshold validation set (amendment 5)

- No dedicated retrieval-threshold validation set exists. `eval/golden/v1` holds 60 cases (20 ACS / 20 CAP / 20 DKA) but its chunkmap marks all Harrison references `unmappable` (McGraw-Hill copyright, H0.1) and maps only open-access guideline chunks — unsuitable for tuning a Harrison similarity threshold.
- Decision: threshold stays PROVISIONAL and UNTUNED (`TwoPassRetrievalConfig.similarity_threshold = 0.01`, `top_k_per_query = 6`, `max_total_chunks = 24`). Nothing was tuned on test fixtures.
- Proposal (owner approval required): build `eval/retrieval_validation_v1/` with 30–50 adjudicated query→chunk relevance labels (including the realistic Charles Brown CAP queries), report precision@k/recall@k across thresholds {0.0, 0.01, 0.05, 0.1}, and set the threshold from that measurement in Phase 3.

## 8. Conditional-approval fixes (2026-10-04)

### 8.1 Semantic retrieval (BLOCKER resolved)

- `HarrisonAdapter.search()` is now semantic-first: cosine similarity against the
  EXISTING `harrison_embeddings.npy` (verified shape `(31427, 384)`, float32,
  rows L2-normalized, row *i* ↔ collection entry *i*), queried with the SAME
  embedding model + pooling that built them:
  `sentence-transformers/all-MiniLM-L6-v2`, mean pooling, truncation 512
  (`backend/rag/vector_embedder.py` at build time; `vh.rag.indexing.GeneralEmbeddingModel` at query time).
- Hybrid: top semantic candidates are reranked by lexical token overlap; the
  reported `score` is always cosine similarity.
- **Score scale**: cosine similarity clipped to **[0, 1]**. The provisional
  `similarity_threshold = 0.01` applies to this scale and remains UNTUNED.
- Pure lexical search runs ONLY as a fallback (embeddings/model unavailable,
  e.g. unit tests on mini-collections), tagged `retrieval_mode=lexical-fallback`
  vs `semantic-hybrid`. The query side refuses the deterministic-projector
  fallback (different vector space) and falls back to lexical instead.
- Proven by `test_harrison_semantic_search_uses_embeddings` (16/16 Phase 1 tests green with semantic search).

### 8.2 Production path statement

- **Production today uses NEITHER `run()` NOR `run_with_log()`.**
  The serving path is `backend/main.py` → `backend/simulation/orchestrator.py`
  → `backend/llm/medgemma_service.py` directly; it never enters
  `src/vh/generation/pipeline.py` (legacy `run()` serves only the eval harness).
  Production generation therefore currently has NO retrieval guard.
- **Confirmed for Phase 2**: backend generation will be rewired through
  `src/vh` `run_with_log()` with a mandatory `retrieval_log`. After Phase 2,
  no production path may generate without retrieval.

### 8.3 Retrieval validation set

- Approved set `eval/retrieval_validation_v1/` (40 labelled query→chunk pairs)
  prepared in Phase 1; every label carries `"label_status": "pending physician
  review"`. No threshold tuning until the owner reviews the labels.

## 7. RL export block (amendments 5–6)

- `POST /api/rl/train` returns 503 (`RL training export is temporarily disabled until Phase 5…`) unless `VH_ALLOW_RL_TRAIN=true`. `GET /api/rl/train/status` stays 200.
- Both frontend training consoles show the 503 message verbatim, keep the modal open and functional (`data-testid="train-blocked-503"`), and re-enable the button. Covered by backend contract tests and a frontend 503 unit test.
- Review-record audit (2026-10-04, `data/aivh.db`, read-only): 16 reports (Charles Brown ×3 dup with `chief_complaint='Pneumonia'` → `Undifferentiated Acute Medical Illness` @0.70; Robert Miller/CASE-101 ×12 dup NSTEMI @0.94; Concurrent ×1), 9 reviews (3× `Dr. Marcus Vance, MD, FACP`, 6× `Dr. Sarah Attending, MD`; contradictory pairs: 3/5-approved-with-top-grades ×1, 1/5-rejected-with-top-grades ×1), 32 patients (1 Brown, 6 Gerald Montgomery dup, 25 `Concurrent Patient` stress-test mocks), 0 DPO pairs. Flagging (`is_synthetic`) and dedup are Phase 5 work; nothing was deleted or re-flagged in Phase 1. The new Charles Brown fixture carries `is_synthetic=true`.
