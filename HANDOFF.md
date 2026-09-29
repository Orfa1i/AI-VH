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
  - Authored `docs/steps/STEP-16.md` and checked off Step 16 in `plan/README.md`.

- **Acceptance Criteria & Regression Suite**:
  - Full verification test suite: **152 passed out of 152** (100% pass rate in 262.65s).
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.
  - Evaluation harness (`py -3.13 scripts/test_all.py eval`): **60 of 60 golden v1 cases passing**.
  - Verified complete absence of em-dash (`—`) characters across all deliverables.

---

## 2. Key Decisions and Rationale
- **Dual Embedding Candidates with Offline Projections**: Allows empirical comparison in Step 18 between general and biomedical embedding models without requiring live network access or brittle external dependencies during automated CI runs.
- **Cryptographic Provenance Manifests**: Every index artifact contains an immutable SHA-256 manifest hash linking retrieval results to specific source document versions and chunker configurations.
- **Superseded Chunk Lifecycle Tracking**: Prevents clinical guideline obsolescence by explicitly flagging and isolating superseded evidence versions while preserving full audit history.

---

## 3. Current State
- **Phase 0 (Foundations, Governance & Evaluation Harness)**: **100% COMPLETE & PASSED** (tagged `phase-0-pass`).
- **Phase 1 (Synthetic Patients & Case Builder)**: **100% COMPLETE & PASSED** (tagged `phase-1-pass`).
- **Phase 2 (Multi-Source RAG)**:
  - Step 14 (P2.1 Source Adapters): **DONE** (commit `f3c1c03`).
  - Step 15 (P2.2 Structure-aware chunking): **DONE** (commit `57aaa1f`).
  - Step 16 (P2.3 Dense + keyword indexing with versioned indexes): **DONE** (commit `63e39aa`).
  - Step 17 (P2.4 Unified hybrid retrieval API): **READY TO START**.
- **Test Suite**: 152 of 152 tests passing across `tests/` and `backend/tests/`.
- **Backend Service**: Running on `http://127.0.0.1:8000` (FastAPI with MedGemma 4-bit NF4 GPU engine active).
- **Frontend Service**: Running on `http://localhost:5173` (Vite dev server active).

---

## 4. Concrete Next Steps
1. Execute STEP 17: P2.4 Unified hybrid retrieval API in `plan/prompts/phase-2-rag/STEP-17_P2.4_retrieval-api.md`.
2. Write acceptance criteria tests in `tests/test_step_17_acceptance.py`:
   - Single retrieval endpoint accepting query, filters (source, date, evidence level), top_k, alpha weight (dense vs keyword).
   - Reciprocal Rank Fusion (RRF) and linear score combination.
   - P95 latency <= `retrieval.p95_latency_s` (1.5s).
   - Traceability: every returned chunk contains full provenance (source_id, doc_id, version, locator, offsets, licence).
   - Zero stale retrievals: superseded chunks excluded by default.
3. Implement `src/vh/rag/retrieval.py` and API router endpoint.
4. Run full regression suite (`scripts/test_all.py`), author `docs/steps/STEP-17.md`, and update `plan/README.md`.
