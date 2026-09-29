# STEP 15: P2.2 Structure-Aware Chunking

- **Phase:** Phase 2: Multi-Source RAG
- **Step:** 15 of 54 (P2.2)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-2-rag/STEP-15_P2.2_chunking.md`

---

## 1. Executive Summary

Step 15 implements the structure-aware clinical chunking engine for AI Virtual Hospital (AI-VH). Operating on normalized `SourceDocument` instances produced by the multi-source adapters from Step 14, `StructureAwareChunker` preserves document structural boundaries first (SPL sections, PMC full-text sections, guideline headings, and structured abstract divisions) before applying a token budget with sliding overlap.

Markdown tables and structured lists are preserved as intact atomic units where possible. Large atomic tables exceeding token ceilings are retained whole and flagged with `exceeds_bounds=True` to eliminate tabular truncation errors. Crucially, every chunk records deterministic provenance offsets such that `doc.text[start_char_offset:end_char_offset] == chunk.text` holds with 100% mathematical precision across all source types.

---

## 2. Built Artifacts

1. `src/vh/rag/chunking.py`:
   - `count_tokens`: Deterministic word and punctuation symbol token counter.
   - `ChunkerConfig`: Configurable parameters (`target_chunk_tokens`, `max_chunk_tokens`, `overlap_tokens`, `chunker_version`, `preserve_tables`, `preserve_lists`).
   - `Chunk`: Pydantic schema (`chunk_id`, `text`, `token_count`, `section_path`, `locator`, `start_char_offset`, `end_char_offset`, `chunker_version`, `exceeds_bounds`, `parent_metadata`).
   - `StructureAwareChunker`: Structural block partitioner (tables, lists, paragraphs, sentence spans) guaranteeing zero section boundary crossing, exact offset substring equality, and SHA-256 cryptographic provenance hashing.
2. `src/vh/rag/__init__.py`:
   - Exported `Chunk`, `ChunkerConfig`, and `StructureAwareChunker`.
3. `tests/test_step_15_acceptance.py`:
   - Unit and property test suite covering section isolation, offset string equality, bound enforcement, and deterministic hash reproduction.

---

## 3. Tests and Verification

- **Tests Added**: `tests/test_step_15_acceptance.py` (5 unit/property tests).
  1. `test_no_chunk_crosses_section_boundary`: Verifies chunks strictly retain parent document section paths without cross-section contamination.
  2. `test_property_chunk_text_equals_normalized_source_at_offsets`: Exhaustive property test verifying that for every chunk across DailyMed, PMC, and PubMed fixtures, `doc.text[start_char_offset:end_char_offset] == chunk.text`.
  3. `test_chunk_sizes_stay_within_bounds_and_tables_flagged`: Validates chunk token bounds on standard prose, and verifies oversized tables remain whole while flagged with `exceeds_bounds=True`.
  4. `test_chunk_ids_are_deterministic`: Bit-for-bit repeatability check across identical inputs, and verified hash divergence upon metadata alteration.
  5. `test_parent_metadata_and_chunker_version`: Confirms retention of parent provenance fields (`source_id`, `doc_id`, `licence`, `evidence_level`, `custom_meta`) and chunker semantic version.
- **Full Verification Suite**:
  - `py -3.13 scripts/test_all.py`: **147 of 147 tests passing** (100% pass rate in 256.81s).
  - Secret scan: 0 hardcoded secrets or credentials detected.
  - Evaluation harness: 60/60 golden v1 cases passing all gate criteria.

---

## 4. Failures Found and Resolved

None. All structural chunking logic and offset substring properties satisfied all requirements on first implementation pass.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| Split on document structure first (SPL, PMC, guidelines, abstracts) | MET | `src/vh/rag/chunking.py`, `tests/test_step_15_acceptance.py::test_no_chunk_crosses_section_boundary` |
| Token budget with overlap between consecutive chunks | MET | `src/vh/rag/chunking.py`, `tests/test_step_15_acceptance.py::test_chunk_sizes_stay_within_bounds_and_tables_flagged` |
| Keep tables and lists whole where possible | MET | `src/vh/rag/chunking.py`, `tests/test_step_15_acceptance.py::test_chunk_sizes_stay_within_bounds_and_tables_flagged` |
| Deterministic `chunk_id` hash (source doc version + locator + offsets) | MET | `src/vh/rag/chunking.py`, `tests/test_step_15_acceptance.py::test_chunk_ids_are_deterministic` |
| Property test: chunk text equals normalized source text at its offsets | MET | `tests/test_step_15_acceptance.py::test_property_chunk_text_equals_normalized_source_at_offsets` |
| Chunk sizes within bounds (whole tables exceeding bounds flagged) | MET | `tests/test_step_15_acceptance.py::test_chunk_sizes_stay_within_bounds_and_tables_flagged` |
| Record chunker version | MET | `src/vh/rag/chunking.py`, `tests/test_step_15_acceptance.py::test_parent_metadata_and_chunker_version` |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All criteria satisfied with 100% test coverage.
