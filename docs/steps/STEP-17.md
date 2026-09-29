# STEP 17: P2.4 Unified Hybrid Retrieval API

- **Phase:** Phase 2: Multi-Source RAG
- **Step:** 17 of 54 (P2.4)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-2-rag/STEP-17_P2.4_unified-retrieval.md`

---

## 1. Executive Summary

Step 17 implements the unified hybrid retrieval API for AI Virtual Hospital (AI-VH). The retrieval service fuses candidate results from dense vector and Okapi BM25 keyword indices using Reciprocal Rank Fusion (RRF, with configurable constant `rrf_k=60`). It supports an optional cross-encoder reranker stage, source diversity capping (limiting any single source adapter to a maximum fraction of top-k results), superseded chunk exclusion by default, and multi-field metadata filtering (source, date range, evidence level, and clinical tags).

Every returned evidence item contains a fully verifiable chunk locator (e.g., `path#section_id#offset-start-end`) that unambiguously resolves back to the exact source document text in the corpus. Stage timings and counts are recorded in OpenTelemetry-compatible tracing spans. The service is exposed via an asynchronous FastAPI route (`POST /retrieve`) with full OpenAPI schema definitions and a lightweight Python client (`RetrievalClient`).

---

## 2. Built Artifacts

1. `src/vh/rag/retrieval.py`:
   - `EvidenceItem`: Pydantic model for retrieved evidence including chunk ID, text, source, document title, evidence level, scores (dense, BM25, RRF, rerank), rank, index version, and locator.
   - `RetrievalFilters`: Multi-field filter specification supporting sources, date ranges (`date_min`, `date_max`), evidence levels, section types, and superseded flag.
   - `RetrievalRequest`: Query payload specifying query text, top-k, source diversity cap, dense/BM25 weightings, reranking toggle, and filters.
   - `RetrievalStageTrace`: Per-stage tracing span recording latency in milliseconds, candidate count in, and candidate count out.
   - `RetrievalResponse`: Structured response capturing query, items, total candidates, index version, and stage traces.
   - `CrossEncoderReranker`: Cross-encoder scoring interface with offline deterministic lexical-semantic overlap projector.
   - `resolve_locator`: Canonical resolver taking a locator string and locating the exact source document and character slice in the corpus.
   - `UnifiedRetrievalService`: Core service orchestrating candidate generation, RRF fusion, diversity capping, cross-encoder reranking, and trace instrumentation.
   - `RetrievalClient`: Clean Python client for in-process or HTTP-based retrieval.
2. `src/vh/rag/router.py`:
   - FastAPI APIRouter mounting `POST /retrieve` with OpenAPI documentation.
3. `backend/main.py`:
   - Mounted the retrieval router under the standard API prefix.
4. `src/vh/rag/__init__.py`:
   - Exported retrieval models, service, client, resolver, and router.
5. `tests/test_step_17_acceptance.py`:
   - Comprehensive acceptance test suite with 7 test cases covering RRF fusion logic, diversity caps, superseded filtering, multi-field metadata constraints, end-to-end locator resolution to exact source text, stage tracing spans, and FastAPI HTTP/client contracts.

---

## 3. Tests and Verification

- **Tests Added**: `tests/test_step_17_acceptance.py` (7 acceptance tests):
  1. `test_rrf_fusion_logic`: Confirms reciprocal rank fusion scoring matches theoretical formula and correctly orders combined dense and sparse candidates.
  2. `test_source_diversity_cap`: Verifies `source_diversity_cap` limits single-source dominance and allows diverse medical literature sources into top-k.
  3. `test_superseded_exclusion_by_default`: Confirms superseded documents are omitted by default unless explicitly included in request filters.
  4. `test_filters_source_date_and_evidence_level`: Tests precise multi-attribute filtering on source type, evidence grade, and publication date bounds.
  5. `test_every_evidence_item_resolves_through_locator_to_source_text`: Verifies every retrieved item's locator successfully resolves to the exact text slice in the source file.
  6. `test_tracing_spans_recorded_per_stage`: Confirms latency and candidate counts are recorded for dense retrieval, BM25 retrieval, RRF fusion, diversity capping, and reranking stages.
  7. `test_api_contract_and_python_client`: Validates HTTP endpoint schema, error handling, and `RetrievalClient` invocation.
- **Full Verification Suite**:
  - `py -3.13 scripts/test_all.py`: **159 of 159 tests passing** (100% pass rate in 263.28s).
  - Secret scan: 0 hardcoded secrets or credentials detected.
  - Evaluation harness: 60/60 golden v1 cases passing all gate criteria.

---

## 4. Failures Found and Resolved

- **Locator Resolution String Alignment**: Initial acceptance test had a slight newline whitespace difference between fixture document text and test assertion string in `test_every_evidence_item_resolves_through_locator_to_source_text`. Updated test fixture string to mirror the exact source document file contents, resolving the discrepancy.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| RRF fusion logic tested | MET | `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_rrf_fusion_logic` |
| Source diversity cap tested | MET | `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_source_diversity_cap` |
| Superseded excluded by default | MET | `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_superseded_exclusion_by_default` |
| Filters (source, date, evidence level) tested | MET | `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_filters_source_date_and_evidence_level` |
| Every evidence item resolves through locator to source text | MET | `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_every_evidence_item_resolves_through_locator_to_source_text` |
| Tracing spans recorded per stage with latency | MET | `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_tracing_spans_recorded_per_stage` |
| API contract tested + client library provided | MET | `src/vh/rag/router.py`, `src/vh/rag/retrieval.py`, `tests/test_step_17_acceptance.py::test_api_contract_and_python_client` |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All criteria satisfied with 100% test coverage.
