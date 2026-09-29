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
  - Exported chunking API in `src/vh/rag/__init__.py`.
  - Tested with 5 unit/property tests in `tests/test_step_15_acceptance.py`.
  - Authored `docs/steps/STEP-15.md` and checked off Step 15 in `plan/README.md`.

- **Acceptance Criteria & Regression Suite**:
  - Full verification test suite: **147 passed out of 147** (100% pass rate in 256.81s).
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.
  - Evaluation harness (`py -3.13 scripts/test_all.py eval`): **60 of 60 golden v1 cases passing**.
  - Verified complete absence of em-dash (`—`) characters across all deliverables.

---

## 2. Key Decisions and Rationale
- **Exact Offset Invariance**: Chunks never undergo irreversible transformations or whitespace loss that would desynchronize character offsets from source texts. This guarantees 100% traceable citations during downstream generation and verification.
- **Atomic Table Preservation**: Tables are kept intact as single evidence units even when exceeding standard token targets, preventing fragmented clinical dosage charts.
- **Deterministic Chunk IDs**: Provenance hashing enables bit-for-bit index reconstruction and delta indexing in Step 16.

---

## 3. Current State
- **Phase 0 (Foundations, Governance & Evaluation Harness)**: **100% COMPLETE & PASSED** (tagged `phase-0-pass`).
- **Phase 1 (Synthetic Patients & Case Builder)**: **100% COMPLETE & PASSED** (tagged `phase-1-pass`).
- **Phase 2 (Multi-Source RAG)**:
  - Step 14 (P2.1 Source Adapters): **DONE** (commit `f3c1c03`).
  - Step 15 (P2.2 Structure-aware chunking): **DONE** (commit `57aaa1f`).
  - Step 16 (P2.3 Dense + keyword indexing with versioned indexes): **READY TO START**.
- **Test Suite**: 147 of 147 tests passing across `tests/` and `backend/tests/`.
- **Backend Service**: Running on `http://127.0.0.1:8000` (FastAPI with MedGemma 4-bit NF4 GPU engine active).
- **Frontend Service**: Running on `http://localhost:5173` (Vite dev server active).

---

## 4. Concrete Next Steps
1. Execute STEP 16: P2.3 Dense + keyword indexing with versioned indexes in `plan/prompts/phase-2-rag/STEP-16_P2.3_indexing.md`.
2. Write acceptance criteria tests in `tests/test_step_16_acceptance.py`:
   - Embedding interface with two configured candidates (general-purpose e.g. sentence-transformers, biomedical e.g. MedEmbed / PubMedBERT).
   - Dense vector index (ChromaDB / SQLite vector) + BM25 keyword index.
   - Versioned index artifact with manifest: embedding model + version, chunker version, source document versions, counts.
   - Incremental updates with superseded marking (`superseded_by`).
   - Query output records index version used.
3. Implement `src/vh/rag/indexing.py`.
4. Run full regression suite (`scripts/test_all.py`), author `docs/steps/STEP-16.md`, and update `plan/README.md`.
