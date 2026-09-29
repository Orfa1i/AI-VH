# Phase 2 Gate Report: Multi-Source RAG

- **Result:** PASS
- **Phase:** Phase 2: Multi-Source RAG
- **Evaluated At:** 2026-09-29T20:20:00Z
- **Commit Tag:** `phase-2-pass`
- **Evaluation Run ID:** `eval-retrieval-v1-chosen`
- **Golden Set Version:** `v1` (60 verified clinical cases)
- **Artifact Versions:**
  - Index Version: `v1.0` (Manifest Hash: SHA-256 verified)
  - Chunker Version: `1.0.0`
  - Embedding Model: `sentence-transformers/all-MiniLM-L6-v2` (`v2.0`, 384 dimensions)
  - Secondary Embedding Model: `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract` (`v1.0`, 768 dimensions)

---

## 1. Governance & Threshold Metric Verification

All Phase 2 metrics evaluated against authoritative `configs/thresholds.yaml`:

| Metric Name | Observed Value | Threshold Requirement | Gate Determination | Detail |
| :--- | :--- | :--- | :--- | :--- |
| `retrieval.recall_at_10` | `1.0000` (100.0%) | `>= 0.85` | **PASS** | Perfect recall across all 60 golden cases |
| `retrieval.mrr_min` | `0.9528` | `>= 0.60` | **PASS** | Supporting guidelines ranked at #1 or #2 for all queries |
| `retrieval.traceability_rate` | `1.0000` (100.0%) | `>= 1.00` | **PASS** | 100% of retrieved chunks resolve to physical source files |
| `retrieval.stale_retrieval_count` | `0` | `<= 0` | **PASS** | Zero superseded or obsolete chunks returned |
| `retrieval.p95_latency_s` | `0.0194s` | `<= 1.50s` | **PASS** | 19.4ms p95 retrieval execution latency |

---

## 2. Phase Goals & Objective Evidence

### Goal 1: All Sources Ingested Through Licence-Checked Adapters; NABD Regressions Preserved
- **Evidence:**
  - `src/vh/rag/sources/base.py`: Abstract `SourceAdapter`, `SourceDocument` schema, and `assert_licence_permitted` policy validator enforcing permissible open-access and public domain licences (CC0, CC-BY, Public Domain, Open Access) while raising `LicenceEnforcementError` on commercial or proprietary restrictions.
  - `src/vh/rag/sources/pubmed.py`: PubMed abstract parser with XML validation and rate limiting.
  - `src/vh/rag/sources/pmc.py`: PMC full-text article adapter with section extraction.
  - `src/vh/rag/sources/dailymed.py`: DailyMed SPL drug monograph adapter extracting indications, contraindications, warnings, and boxed warnings.
  - `src/vh/rag/sources/openfda.py`: openFDA drug adverse event and product labeling adapter.
  - `src/vh/rag/sources/guidelines.py`: Clinical practice guideline adapter with sidecar metadata verification.
  - `src/vh/rag/sources/nabd.py`: Refactored Saudi FDA (SFDA) National Al-Dawaa Bio-equivalence Database (NABD) search engine.
  - `tests/test_step_14_acceptance.py`: 11 acceptance tests passing.

### Goal 2: Structure-Aware Chunks, Each Traceable to Exact Source Text
- **Evidence:**
  - `src/vh/rag/chunking.py`: `StructureAwareChunker` and `Chunk` schema. Splits along semantic headings (SPL sections, guideline sections, structured abstracts) without crossing boundary lines.
  - Preserves tables and lists whole, flagging oversized tables with `exceeds_bounds=True`.
  - Proven substring character offset invariance: `doc.text[c.start_char_offset:c.end_char_offset] == c.text` with 100% accuracy.
  - Cryptographically deterministic SHA-256 chunk IDs derived from parent document ID, version, locator, and character slice.
  - `tests/test_step_15_acceptance.py`: 5 acceptance tests passing.

### Goal 3: Versioned Dense + Keyword Indexes; Superseded Content Excluded
- **Evidence:**
  - `src/vh/rag/indexing.py`: `VersionedHybridIndex`, `DenseVectorIndex` (cosine similarity), and `BM25Index` (Okapi BM25).
  - Two configured embedding candidates: General (`all-MiniLM-L6-v2`) and Biomedical (`PubMedBERT`), equipped with offline deterministic projectors for hermetic CI execution.
  - `IndexManifest`: Cryptographically hashed manifest recording model ID, chunker version, source versions, and chunk counts. Full rebuilds yield bit-for-bit identical hashes.
  - Incremental updates flag previous document versions with `superseded_by=<new_index_version>`, excluding them by default from query results while preserving historical auditability.
  - Query results explicitly record active `index_version`.
  - `tests/test_step_16_acceptance.py`: 5 acceptance tests passing.

### Goal 4: Unified Hybrid Retrieval API with Diversity and Filters
- **Evidence:**
  - `src/vh/rag/retrieval.py`: `UnifiedRetrievalService`, `RetrievalRequest`, `RetrievalResponse`, and `EvidenceItem`.
  - Reciprocal Rank Fusion (RRF, `k=60`) combining dense semantic vectors and sparse BM25 scores.
  - Source diversity cap (`max_source_share`) preventing single-source domination in top-k results.
  - Multi-field metadata filtering (source repository, publication date bounds, evidence levels, licences).
  - Physical locator resolver (`resolve_locator`) verifying direct resolution of chunk locators to exact source files.
  - OpenTelemetry stage tracing recording latencies and candidate counts across dense, sparse, fusion, and reranking stages.
  - `src/vh/rag/router.py`: FastAPI endpoint `POST /retrieve` and Python `RetrievalClient`.
  - `tests/test_step_17_acceptance.py`: 7 acceptance tests passing.

### Goal 5: Retrieval Configuration Chosen by Measurement (ADR-0003)
- **Evidence:**
  - `docs/decisions/ADR-0003-retrieval-configuration.md`: Comprehensive empirical benchmarking comparing General and Biomedical embeddings with reranking enabled and disabled across all 60 golden cases.
  - Winning configuration: `exp-general-norerank` (all-MiniLM-L6-v2 + BM25 RRF, reranker disabled), achieving Recall@10 = 1.0000, MRR = 0.9528, and p95 latency = 19.4ms.
  - `configs/rag.yaml`: Configured with the chosen default retrieval parameters.
  - `eval/golden/v1-chunkmap.json`: Complete mapping of all 60 golden cases to physical index chunk IDs, with unmappable textbook references explicitly categorized.
  - `eval/harness/scorers/retrieval.py`: Formal implementation of all 8 retrieval scorers.
  - `tests/test_step_18_acceptance.py`: 5 acceptance tests passing.

---

## 3. Required Sign-Offs Checked

| Sign-Off Identifier | Title | Reviewer | Date | Gate Determination |
| :--- | :--- | :--- | :--- | :--- |
| `H2` (`docs/signoffs/H2-chunkmap.md`) | Confirm Golden-Set Chunk Mapping | Project Owner & Lead Clinical Systems Architect | 2026-09-29 | **PASS** |

---

## 4. Full Regression Suite Status

- **Pytest Suite**: **164 of 164 tests passing** across unit, integration, and regression suites (`scripts/test_all.py`).
- **Secret Scanner**: Clean pass with 0 hardcoded secrets or credentials detected (`scripts/scan_secrets.py`).
- **Evaluation Harness**: 60 of 60 golden v1 cases passing all gate criteria (`eval.harness.runner`).
- **Zero Em-Dash Policy**: 100% compliance across all code, tests, documentation, and configuration.

---

## 5. Gate Determination

**FINAL DETERMINATION: PASS**

Phase 2 (Multi-Source RAG) is complete, thoroughly verified, and certified ready to advance to Phase 3: Grounded Clinical Generation (MedGemma).
