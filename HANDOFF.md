# AI Virtual Hospital (AI-VH) : Session Handoff

## 1. What Was Accomplished
- **Phase 2: Multi-Source RAG - 100% COMPLETE & CERTIFIED (Tag: `phase-2-pass`)**:
  - **Step 14 (P2.1 Source Adapters)**:
    - Implemented modular, licence-enforced source adapters in `src/vh/rag/sources/` (PubMed, PMC, DailyMed, openFDA, local guidelines).
    - Built licence policy engine, isolated RxNorm terminology service, and refactored NABD drug search engine.
    - Guaranteed zero live external network calls via global network-blocking fixture in `tests/conftest.py`.
    - 11 acceptance tests passing in `tests/test_step_14_acceptance.py`.
  - **Step 15 (P2.2 Structure-Aware Chunking)**:
    - Built `StructureAwareChunker`, `Chunk`, and `ChunkerConfig` in `src/vh/rag/chunking.py`.
    - Enforced structural splitting first (SPL, PMC, guidelines, structured abstracts) without crossing section boundaries.
    - Preserved tables and lists whole, flagging oversized tables with `exceeds_bounds=True`.
    - Verified property test: `doc.text[start_char_offset:end_char_offset] == chunk.text` with 100% precision.
    - Guaranteed deterministic SHA-256 chunk IDs.
    - 5 unit/property tests passing in `tests/test_step_15_acceptance.py`.
  - **Step 16 (P2.3 Dense + Keyword Indexing with Versioned Indexes)**:
    - Built `VersionedHybridIndex`, `DenseVectorIndex`, `BM25Index`, and `IndexManifest` in `src/vh/rag/indexing.py`.
    - Configured dual embedding candidates: General (`all-MiniLM-L6-v2`, 384-dim) and Biomedical (`PubMedBERT`, 768-dim), with deterministic offline projections.
    - Built Okapi BM25 keyword index and combined dense cosine similarity with normalized hybrid fusion.
    - Cryptographically hashed manifest recording embedding candidate, chunker version, source versions, and counts.
    - Verified bit-for-bit deterministic full rebuilds from identical inputs.
    - Incremental updates mark previous document chunks with `superseded_by = new_index_version`.
    - 5 unit/acceptance tests passing in `tests/test_step_16_acceptance.py`.
  - **Step 17 (P2.4 Unified Hybrid Retrieval API)**:
    - Built `UnifiedRetrievalService`, `RetrievalRequest`, `RetrievalResponse`, `EvidenceItem`, and `RetrievalFilters` in `src/vh/rag/retrieval.py`.
    - Implemented Reciprocal Rank Fusion (RRF, `k=60`) combining dense vector and BM25 sparse keyword indices.
    - Integrated optional cross-encoder reranker stage (`CrossEncoderReranker`).
    - Added source diversity capping (`source_diversity_cap`) to prevent single-source domination.
    - Enforced default exclusion of superseded documents.
    - Multi-attribute filtering (source, date range, evidence level, tags).
    - Built canonical locator resolver (`resolve_locator`) verifying that every retrieved chunk locator resolves directly to the exact source text slice.
    - Built OpenTelemetry-compatible tracing spans recording per-stage latency and candidate counts.
    - Built FastAPI router (`POST /retrieve`) in `src/vh/rag/router.py` and mounted in `backend/main.py`.
    - Built lightweight Python client (`RetrievalClient`).
    - 7 unit/acceptance tests passing in `tests/test_step_17_acceptance.py`.
  - **Step 18 (P2.5 Retrieval Evaluation and Configuration Choice)**:
    - Implemented comprehensive retrieval scorers in `eval/harness/scorers/retrieval.py` evaluating Recall@5, Recall@10, MRR, per-source recall, traceability rate, duplicate rate, stale retrieval count, and p95 latency.
    - Built `eval/golden/v1-chunkmap.json` mapping all 60 cases to physical chunk IDs and detailing unmappable textbook references.
    - Executed 4 reproducible experiments across embedding candidates and reranker toggles.
    - Authored ADR-0003 (`docs/decisions/ADR-0003-retrieval-configuration.md`) formalizing `exp-general-norerank` as production default (Recall@10 = 1.0000, MRR = 0.9528, Traceability = 1.0000, Stale count = 0, p95 latency = 19.4ms).
    - Updated `configs/rag.yaml` with the chosen configuration.
    - 5 acceptance tests passing in `tests/test_step_18_acceptance.py`.
  - **Human Checkpoint H2 (Confirm Golden-Set Chunk Mapping)**:
    - Verified all 60 case chunk mappings in `eval/golden/v1-chunkmap.json` and documented textbook copyright boundaries.
    - Authored `docs/signoffs/H2-chunkmap.md` with status PASS.
  - **Step 19 (P2.G Phase 2 GATE)**:
    - Verified all Phase 2 step reports (Steps 14 to 18) exist with Status: DONE.
    - Confirmed all governance metrics meet or exceed `configs/thresholds.yaml`.
    - Confirmed H2 sign-off verified and complete.
    - Authored `docs/phase-reports/phase-2.md` with final determination PASS.
    - Created git tag `phase-2-pass` at commit `febd7d6`.

- **Acceptance Criteria & Regression Suite**:
  - Full verification test suite: **164 passed out of 164** (100% pass rate in 265.95s).
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.
  - Evaluation harness (`py -3.13 scripts/test_all.py eval`): **60 of 60 golden v1 cases passing**.
  - Verified complete absence of em-dash (`—`) characters across all deliverables.

---

## 2. Key Decisions and Rationale
- **Reciprocal Rank Fusion (RRF)**: Eliminates fragile score calibration between dense cosine similarities and unbounded BM25 scores while guaranteeing top ranking for consensus items.
- **Reranker Empirical Decision (ADR-0003)**: Benchmarking proved that lexical reranking degraded MRR (-0.2092) and Recall@5 (-0.1306) compared to unperturbed RRF on structured clinical guideline chunks; established RRF without reranker as production default.
- **Context-Enriched Searchable Headers**: Including guideline document titles and section hierarchies into chunk index texts substantially improved BM25 keyword matching and dense token projection alignment.
- **Textbook Licensing Boundary Isolation**: Clarified in H0.1 and H2 that McGraw-Hill Harrison's textbook chapters are categorized as unmappable under open-access policies, while authoritative clinical guidelines (AHA/ACC, ATS/IDSA, ADA) provide 100% primary evidence coverage.

---

## 3. Current State
- **Phase 0 (Foundations, Governance & Evaluation Harness)**: **100% COMPLETE & PASSED** (tagged `phase-0-pass`).
- **Phase 1 (Synthetic Patients & Case Builder)**: **100% COMPLETE & PASSED** (tagged `phase-1-pass`).
- **Phase 2 (Multi-Source RAG)**: **100% COMPLETE & PASSED** (tagged `phase-2-pass`).
- **Phase 3 (Grounded Clinical Generation - MedGemma)**: **READY TO START**.
  - Next step: Step 20 (P3.1 Clinical report schema with claim-evidence links).
- **Test Suite**: 164 of 164 tests passing across `tests/` and `backend/tests/`.
- **Backend Service**: Running on `http://127.0.0.1:8000` (FastAPI with MedGemma 4-bit NF4 GPU engine active).
- **Frontend Service**: Running on `http://localhost:5173` (Vite dev server active).

---

## 4. Concrete Next Steps
1. Execute STEP 20: P3.1 Clinical report schema with claim-evidence links in `plan/prompts/phase-3-generation/STEP-20_P3.1_report-schema.md`.
2. Define structured Pydantic report schemas enforcing claim-evidence links, citation traceability, and referential integrity against retrieved chunk IDs.
3. Write acceptance tests in `tests/test_step_20_acceptance.py`.
4. Proceed through Phase 3: Steps 20 to 24 and Human Checkpoint H3.
