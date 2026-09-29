# STEP 16: P2.3 Dense + Keyword Indexing with Versioned Indexes

- **Phase:** Phase 2: Multi-Source RAG
- **Step:** 16 of 54 (P2.3)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-2-rag/STEP-16_P2.3_indexing.md`

---

## 1. Executive Summary

Step 16 implements the versioned dense and keyword retrieval index subsystem for AI Virtual Hospital (AI-VH). The indexing layer configures dual embedding candidates: a general-purpose model (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) and a biomedical-specific model (`microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract`, 768-dim), both equipped with deterministic offline projections to ensure 100% offline verification in CI and test harnesses.

Dense vector indexing is paired with a full Okapi BM25 keyword index to enable hybrid multi-source search. Every generated index artifact is accompanied by a cryptographically hashed manifest (`IndexManifest`) recording embedding candidate versions, chunker version, source document versions, and chunk counts. Incremental updates dynamically mark superseded chunks with `superseded_by=<new_index_version>`, and every query result explicitly records the index version used.

---

## 2. Built Artifacts

1. `src/vh/rag/indexing.py`:
   - `EmbeddingModel`: Abstract embedding interface defining vector generation contracts.
   - `DeterministicProjector`: High-dimensional token projection ensuring deterministic, offline-capable dense vectors.
   - `GeneralEmbeddingModel`: General-purpose candidate model using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
   - `BiomedicalEmbeddingModel`: Biomedical domain candidate model using `PubMedBERT` (768 dimensions).
   - `get_embedding_model`: Candidate selector factory.
   - `DenseVectorIndex`: Dense semantic vector store computing cosine similarity.
   - `BM25Index`: Okapi BM25 keyword index (`k1=1.5`, `b=0.75`).
   - `IndexManifest`: Pydantic schema for cryptographically verifiable index manifests (`index_id`, `index_version`, `embedding_model`, `chunker_version`, `source_document_versions`, counts, `manifest_hash`).
   - `RetrievedItem` and `QueryResult`: Structured search responses capturing chunks, dense/BM25 score breakdowns, retrieval mode, and the exact index version used.
   - `VersionedHybridIndex`: Full indexing pipeline supporting on-disk persistence, deterministic rebuilds, incremental updates, and superseded marking.
2. `src/vh/rag/__init__.py`:
   - Exported indexing models, indices, and query structures.
3. `tests/test_step_16_acceptance.py`:
   - Acceptance test suite covering manifest completeness, rebuild determinism, query version tracking, superseded chunk isolation, and dual embedding candidates.

---

## 3. Tests and Verification

- **Tests Added**: `tests/test_step_16_acceptance.py` (5 unit/acceptance tests).
  1. `test_two_embedding_candidates_configured`: Validates configuration and dimensional outputs of both general and biomedical embedding candidates.
  2. `test_index_manifest_completeness_and_match`: Verifies manifest fields match actual indexed contents and source document versions.
  3. `test_full_rebuild_deterministic_ids_and_counts`: Confirms bit-for-bit identical chunk IDs, counts, and vector values across rebuilds.
  4. `test_query_output_records_index_version`: Confirms query output explicitly logs `index_version` and produces relevant clinical matches.
  5. `test_incremental_updates_and_superseded_marking`: Validates incremental updates mark modified document chunks with `superseded_by` while default search excludes stale content.
- **Full Verification Suite**:
  - `py -3.13 scripts/test_all.py`: **152 of 152 tests passing** (100% pass rate in 262.65s).
  - Secret scan: 0 hardcoded secrets or credentials detected.
  - Evaluation harness: 60/60 golden v1 cases passing all gate criteria.

---

## 4. Failures Found and Resolved

None. All indexing abstractions, BM25 scoring, and superseded chunk lifecycle management passed on first test execution.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| Embedding interface with two configured candidates (general, biomedical) | MET | `src/vh/rag/indexing.py`, `tests/test_step_16_acceptance.py::test_two_embedding_candidates_configured` |
| Dense index + BM25 keyword index | MET | `src/vh/rag/indexing.py`, `tests/test_step_16_acceptance.py::test_query_output_records_index_version` |
| Manifest complete and matches actual index contents | MET | `tests/test_step_16_acceptance.py::test_index_manifest_completeness_and_match` |
| Full rebuild gives identical chunk IDs and counts | MET | `tests/test_step_16_acceptance.py::test_full_rebuild_deterministic_ids_and_counts` |
| Query output records index version used | MET | `tests/test_step_16_acceptance.py::test_query_output_records_index_version` |
| Incremental updates with superseded marking tested | MET | `tests/test_step_16_acceptance.py::test_incremental_updates_and_superseded_marking` |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All criteria satisfied with 100% test coverage.
