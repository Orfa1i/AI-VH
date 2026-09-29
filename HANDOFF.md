# AI Virtual Hospital (AI-VH) : Session Handoff

## 1. What Was Accomplished
- **Phase 2: Multi-Source RAG - Step 14 (P2.1 Source Adapters & NABD Regression) COMPLETED**:
  - Implemented modular, licence-enforced source adapters in `src/vh/rag/sources/` (PubMed, PMC, DailyMed, openFDA, local guidelines).
  - Built licence policy engine, isolated RxNorm terminology service, and refactored NABD drug search engine.
  - Implemented global network-blocking fixture in `tests/conftest.py` guaranteeing zero live external network calls.
  - Tested with 11 acceptance tests in `tests/test_step_14_acceptance.py`.

- **Phase 2: Multi-Source RAG - Step 15 (P2.2 Structure-Aware Chunking) COMPLETED**:
  - Built `StructureAwareChunker`, `Chunk`, and `ChunkerConfig` in `src/vh/rag/chunking.py`.
  - Enforced structural splitting first (SPL, PMC, guidelines, structured abstracts) without crossing section boundaries.
  - Preserved tables and lists whole, flagging oversized tables with `exceeds_bounds=True` to eliminate tabular truncation.
  - Verified property test: `doc.text[start_char_offset:end_char_offset] == chunk.text` with 100% precision.
  - Guaranteed deterministic SHA-256 chunk IDs combining source document version, locator, and character offsets.
  - Tested with 5 unit/property tests in `tests/test_step_15_acceptance.py`.

- **Phase 2: Multi-Source RAG - Step 16 (P2.3 Dense + Keyword Indexing with Versioned Indexes) COMPLETED**:
  - Built `VersionedHybridIndex`, `DenseVectorIndex`, `BM25Index`, and `IndexManifest` in `src/vh/rag/indexing.py`.
  - Configured two embedding candidates: General (`all-MiniLM-L6-v2`, 384-dim) and Biomedical (`PubMedBERT`, 768-dim), with deterministic offline projections.
  - Built Okapi BM25 keyword index and combined dense cosine similarity with normalized hybrid fusion.
  - Implemented cryptographically hashed manifest recording embedding candidate, chunker version, source document versions, and counts.
  - Verified bit-for-bit deterministic full rebuilds from identical inputs.
  - Built incremental index update mechanism marking previous document chunks with `superseded_by = new_index_version`.
  - Recorded exact `index_version` in every `QueryResult`.
  - Tested with 5 unit/acceptance tests in `tests/test_step_16_acceptance.py`.

- **Phase 2: Multi-Source RAG - Step 17 (P2.4 Unified Hybrid Retrieval API) COMPLETED**:
  - Built `UnifiedRetrievalService`, `RetrievalRequest`, `RetrievalResponse`, `EvidenceItem`, and `RetrievalFilters` in `src/vh/rag/retrieval.py`.
  - Implemented Reciprocal Rank Fusion (RRF, `k=60`) combining dense vector and BM25 sparse keyword indices.
  - Integrated optional cross-encoder reranker stage (`CrossEncoderReranker`).
  - Added source diversity capping (`source_diversity_cap`) to prevent single-source domination.
  - Enforced default exclusion of superseded documents.
  - Implemented multi-attribute filtering (source, date range, evidence level, tags).
  - Built canonical locator resolver (`resolve_locator`) verifying that every retrieved chunk locator resolves directly to the exact source text slice.
  - Built OpenTelemetry-compatible tracing spans recording per-stage latency and candidate counts.
  - Built FastAPI router (`POST /retrieve`) in `src/vh/rag/router.py` and mounted in `backend/main.py`.
  - Built lightweight Python client (`RetrievalClient`).
  - Tested with 7 unit/acceptance tests in `tests/test_step_17_acceptance.py`.
  - Authored `docs/steps/STEP-17.md` and checked off Step 17 in `plan/README.md`.

- **Acceptance Criteria & Regression Suite**:
  - Full verification test suite: **159 passed out of 159** (100% pass rate in 263.28s).
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.
  - Evaluation harness (`py -3.13 scripts/test_all.py eval`): **60 of 60 golden v1 cases passing**.
  - Verified complete absence of em-dash (`—`) characters across all deliverables.

---

## 2. Key Decisions and Rationale
- **Reciprocal Rank Fusion (RRF)**: RRF provides robust rank combination without requiring fragile cross-modal score calibration between dense cosine similarities and BM25 unbounded scores.
- **Source Diversity Capping**: Enforces balanced multi-source evidence synthesis by preventing high-frequency sources (e.g., guidelines) from crowding out FDA warnings, drug monographs, or trial literature.
- **Direct Locator Resolution Invariance**: Every returned chunk embeds a locator string that deterministically resolves back to the exact physical character slice of the source document in the corpus.

---

## 3. Current State
- **Phase 0 (Foundations, Governance & Evaluation Harness)**: **100% COMPLETE & PASSED** (tagged `phase-0-pass`).
- **Phase 1 (Synthetic Patients & Case Builder)**: **100% COMPLETE & PASSED** (tagged `phase-1-pass`).
- **Phase 2 (Multi-Source RAG)**:
  - Step 14 (P2.1 Source Adapters): **DONE** (commit `f3c1c03`).
  - Step 15 (P2.2 Structure-aware chunking): **DONE** (commit `57aaa1f`).
  - Step 16 (P2.3 Dense + keyword indexing with versioned indexes): **DONE** (commit `63e39aa`).
  - Step 17 (P2.4 Unified hybrid retrieval API): **DONE** (commit `6818712`).
  - Step 18 (P2.5 Retrieval evaluation and configuration choice): **READY TO START**.
- **Test Suite**: 159 of 159 tests passing across `tests/` and `backend/tests/`.
- **Backend Service**: Running on `http://127.0.0.1:8000` (FastAPI with MedGemma 4-bit NF4 GPU engine active).
- **Frontend Service**: Running on `http://localhost:5173` (Vite dev server active).

---

## 4. Concrete Next Steps
1. Execute STEP 18: P2.5 Retrieval evaluation and configuration choice in `plan/prompts/phase-2-rag/STEP-18_P2.5_retrieval-evaluation.md`.
2. Evaluate dense vs keyword vs hybrid retrieval against golden queries.
3. Measure Recall@10, MRR, latency, and source balance.
4. Record configuration decision in `docs/decisions/ADR-0003-retrieval-configuration.md`.
5. Execute Human Checkpoint H2 (Confirm golden-set chunk mapping in `docs/signoffs/H2-chunkmap.md`).
6. Execute Step 19: P2.G Phase 2 GATE.
