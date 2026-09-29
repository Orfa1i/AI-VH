# AI Virtual Hospital (AI-VH) : Session Handoff

## 1. What Was Accomplished
- **Phase 2: Multi-Source RAG - Step 14 (P2.1 Source Adapters & NABD Regression) COMPLETED**:
  - **Source Adapters**: Implemented modular, licence-enforced source adapters in `src/vh/rag/sources/`:
    - `PubMedAdapter`: Parses MEDLINE XML abstract records with structured labels, publication dates, and evidence levels.
    - `PMCAdapter`: Extracts full-text JATS XML hierarchical section trees (`section_path`) and strictly enforces article-level licences.
    - `DailyMedAdapter`: Section-aware parser for FDA Structured Product Labeling (SPL) XML mapped against LOINC clinical codes.
    - `OpenFDAAdapter`: Parses openFDA drug label JSON endpoints with CC0 public domain verification.
    - `LocalGuidelinesAdapter`: Heading-aware ingestion for clinical guidelines in `data/sources/guidelines/` with `.meta.json` sidecars.
  - **Licence Enforcement**: Built strict policy engine rejecting and logging any document with unknown or unpermitted copyright terms.
  - **RxNorm Terminology Service**: Implemented isolated `RxNormService` providing drug name normalization, RxCUI resolution, active ingredient mapping, and pharmacological classes (exposed strictly as terminology, not chunked text).
  - **NABD Drug Search Engine**: Built `NABDService` and `nabd_drug_search` integrating RxNorm, DailyMed/openFDA labels, and PubMed evidence. Provided `backend/clinical/knowledge_sources.py` and root `knowledge_sources.py` compatibility aliases.
  - **Offline Network Guard**: Implemented global network-blocking fixture in `tests/conftest.py` guaranteeing zero live external network calls during test execution.
  - **Acceptance Tests**: Added `tests/test_step_14_acceptance.py` (11 unit/acceptance tests passing).
  - **Full Regression Suite**: All **142 of 142 tests passing** (100% pass rate in 259.48s). Secret scan: 0 detected. Golden eval harness: 60/60 passing.
  - **Report & Documentation**: Authored `docs/steps/STEP-14.md` and checked off Step 14 in `plan/README.md`.

---

## 2. Key Decisions and Rationale
- **Document Schema Contract**: Standardized `SourceDocument` Pydantic model (`source_id`, `doc_id`, `title`, `section_path`, `locator`, `version`, `published_or_updated_date`, `evidence_level`, `licence`, `text`) providing a consistent foundation for structure-aware chunking in Step 15.
- **Terminology vs Retrieval Distinction**: RxNorm is explicitly encapsulated as a terminology normalization service rather than text chunks, preventing wasteful vector indexing of relational drug lookups.
- **Strict Licence Gating**: Prevents ingestion of copyrighted clinical literature that would violate dissemination policies, safeguarding research reproducibility.

---

## 3. Current State
- **Phase 0 (Foundations, Governance & Evaluation Harness)**: **100% COMPLETE & PASSED** (tagged `phase-0-pass`).
- **Phase 1 (Synthetic Patients & Case Builder)**: **100% COMPLETE & PASSED** (tagged `phase-1-pass`).
- **Phase 2 (Multi-Source RAG)**:
  - Step 14 (P2.1 Source Adapters): **DONE** (commit `f3c1c03`).
  - Step 15 (P2.2 Structure-aware chunking): **READY TO START**.
- **Test Suite**: 142 of 142 tests passing across `tests/` and `backend/tests/`.
- **Backend Service**: Running on `http://127.0.0.1:8000` (FastAPI with MedGemma 4-bit NF4 GPU engine active).
- **Frontend Service**: Running on `http://localhost:5173` (Vite dev server active).

---

## 4. Concrete Next Steps
1. Execute STEP 15: P2.2 Structure-aware chunking in `plan/prompts/phase-2-rag/STEP-15_P2.2_chunking.md`.
2. Write acceptance criteria tests in `tests/test_step_15_acceptance.py`:
   - Split on document structure first (SPL sections, PMC sections, structured abstract parts, guideline headings), then by token budget with overlap.
   - Keep tables and lists whole where possible.
   - Deterministic `chunk_id` hashing (source doc version + locator + offsets).
   - Character offsets into the normalized source with parent document metadata.
   - Property tests: chunk text equals normalized source text at its offsets.
3. Implement `src/vh/rag/chunking.py`.
4. Run full regression suite (`scripts/test_all.py`), author `docs/steps/STEP-15.md`, and update `plan/README.md`.
