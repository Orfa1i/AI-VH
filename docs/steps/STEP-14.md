# STEP 14: P2.1 Source Adapters (Refactor knowledge_sources.py)

- **Phase:** Phase 2: Multi-Source RAG
- **Step:** 14 of 54 (P2.1)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-2-rag/STEP-14_P2.1_source-adapters.md`

---

## 1. Executive Summary

Step 14 establishes the formal multi-source data ingestion layer for AI Virtual Hospital (AI-VH). Building upon the foundation and synthetic patient architecture validated in Phase 0 and Phase 1, Step 14 implements modular, licence-enforced source adapters for PubMed, PMC Open Access, DailyMed, openFDA, and local clinical guidelines with sidecars, along with an isolated RxNorm terminology normalization service and a refactored NABD drug search intelligence provider.

All adapters enforce the strict licence policy rejecting unknown or unpermitted copyright works. Network calls are prohibited during automated test suites via an autouse network-blocking fixture, and rate limiting and exponential retry mechanisms protect remote provider interfaces.

---

## 2. Built Artifacts

1. `src/vh/rag/sources/base.py`:
   - `SourceDocument`: Standardized Pydantic document schema (`source_id`, `doc_id`, `title`, `section_path`, `locator`, `version`, `published_or_updated_date`, `evidence_level`, `licence`, `text`, `metadata`).
   - `SourceAdapter`: Abstract protocol for parsing and fetching clinical sources.
   - `LicenceEnforcementError` and `is_licence_permitted`: Policy engine verifying open access, CC0, CC-BY, and public domain licences while rejecting unknown or restricted materials.
   - `RateLimiter`: Thread-safe token bucket rate limiter.
   - `RetryHandler`: Configurable exponential backoff handler.
2. `src/vh/rag/sources/pubmed.py`:
   - `PubMedAdapter`: Parses MEDLINE XML records into structured abstract sections with publication date and evidence level classification.
3. `src/vh/rag/sources/pmc.py`:
   - `PMCAdapter`: Parses PMC Open Access JATS XML full-text articles with hierarchical section paths (`Introduction`, `Methods`, `Results`, `Discussion`) and article-level licence enforcement.
4. `src/vh/rag/sources/dailymed.py`:
   - `DailyMedAdapter`: Section-aware parser for FDA Structured Product Labeling (SPL) XML mapped against LOINC clinical section codes (Boxed Warning, Indications, Contraindications, Warnings, Interactions).
5. `src/vh/rag/sources/openfda.py`:
   - `OpenFDAAdapter`: Structured ingestion for openFDA drug label JSON records.
6. `src/vh/rag/sources/guidelines.py`:
   - `LocalGuidelinesAdapter`: Heading-aware ingestion for local clinical practice guidelines with sidecar metadata files (`.meta.json`).
7. `src/vh/rag/sources/rxnorm.py`:
   - `RxNormService`: Clinical terminology normalization and lookup service (names to RxCUI, ingredients, brand names, drug classes, interaction checks). Exposes terminology services only and does not generate chunked text.
8. `src/vh/rag/sources/nabd.py`:
   - `NABDService` and `nabd_drug_search`: Clinical drug intelligence search engine unifying RxNorm, DailyMed/openFDA labels, and PubMed evidence.
9. `src/vh/rag/sources/client.py`:
   - `SourceClient` and `get_ncbi_client`: HTTP client with rate limiting, retries, and disk caching.
10. `src/vh/rag/sources/__init__.py`:
    - Package exports for source adapters, terminology, and schemas.
11. `backend/clinical/knowledge_sources.py` and `knowledge_sources.py`:
    - Compatibility layer routing backend consumers to `vh.rag.sources`.
12. `configs/rag.yaml`:
    - Declarative rate limits, timeouts, and licence policies.
13. `tests/conftest.py`:
    - Autouse network-blocking test fixture guaranteeing 100% offline verification.
14. Fixtures and guidelines:
    - `tests/fixtures/rag_sources/pubmed_sample.xml`
    - `tests/fixtures/rag_sources/pmc_sample.xml`
    - `tests/fixtures/rag_sources/pmc_restricted.xml`
    - `tests/fixtures/rag_sources/dailymed_aspirin.xml`
    - `tests/fixtures/rag_sources/openfda_metformin.json`
    - `tests/fixtures/rag_sources/rxnorm_fixtures.json`
    - `data/sources/guidelines/aha_acc_acs_2023.md` + `.meta.json`
    - `data/sources/guidelines/ats_idsa_cap_2019.md` + `.meta.json`
    - `data/sources/guidelines/ada_dka_2024.md` + `.meta.json`
    - `data/sources/guidelines/restricted_test_guideline.md` + `.meta.json`

---

## 3. Tests and Verification

- **Tests Added**: `tests/test_step_14_acceptance.py` (11 unit/acceptance tests).
  1. `test_source_document_validation`: Schema validation and required field checks.
  2. `test_licence_enforcement_policy`: Permitted vs unpermitted licence categorization.
  3. `test_pubmed_adapter_fixture_parsing`: MEDLINE XML abstract parsing and section breakdown.
  4. `test_pmc_adapter_fixture_and_licence_enforcement`: JATS XML full-text hierarchy and licence rejection.
  5. `test_dailymed_adapter_spl_sections`: SPL XML parsing with LOINC section mapping.
  6. `test_openfda_adapter_label_sections`: OpenFDA JSON parsing and CC0 validation.
  7. `test_local_guidelines_adapter_with_sidecar`: Markdown guideline ingestion with sidecar metadata.
  8. `test_rxnorm_service_terminology_only`: Normalization, RxCUI resolution, active ingredients, classes.
  9. `test_nabd_drug_search_regression`: Multi-source drug search regression.
  10. `test_offline_network_guard_blocks_live_network`: Live network interception verification.
  11. `test_rate_limiter_and_retry_handler`: Token-bucket throttling and exponential backoff.
- **Full Verification Suite**:
  - `py -3.13 scripts/test_all.py`: **142 of 142 tests passing** (100% pass rate in 259.48s).
  - Secret scan: 0 hardcoded secrets or credentials detected.
  - Evaluation harness: 60/60 golden v1 cases passing all gate criteria.

---

## 4. Failures Found and Resolved

1. **Symptom**: Unbound XML prefix error (`xml.etree.ElementTree.ParseError: unbound prefix: line 25, column 8`) when parsing PMC XML.
   - **Root Cause**: `xlink:href` in permissions block lacked explicit namespace declaration on the root element.
   - **Fix**: Added namespace declaration `xmlns:xlink="http://www.w3.org/1999/xlink"` to the fixture and added defensive string substitution in `PMCAdapter.parse` if `xlink:` is present without namespace.
   - **Regression Test**: `tests/test_step_14_acceptance.py::test_pmc_adapter_fixture_and_licence_enforcement`.

2. **Symptom**: `test_dailymed_adapter_spl_sections` failed to find "BOXED WARNING" in section names.
   - **Root Cause**: DailyMed SPL title node contained specific clinical warning text ("WARNING: RISK OF REYE SYNDROME...") rather than generic LOINC title "Boxed Warning".
   - **Fix**: Formatted `display_section` to prepend `loinc_name` when not already present in the section title (`f"{loinc_name}: {sec_title}"`).
   - **Regression Test**: `tests/test_step_14_acceptance.py::test_dailymed_adapter_spl_sections`.

3. **Symptom**: OpenFDA dataset rejected with `LicenceEnforcementError` for licence URL `https://creativecommons.org/publicdomain/zero/1.0/`.
   - **Root Cause**: Exact match check lacked Creative Commons public domain URL parsing.
   - **Fix**: Extended `is_licence_permitted` to recognize CC0/CC-BY URL variants.
   - **Regression Test**: `tests/test_step_14_acceptance.py::test_openfda_adapter_label_sections`.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| `SourceAdapter` protocol and `SourceDocument` schema | MET | `src/vh/rag/sources/base.py`, `tests/test_step_14_acceptance.py::test_source_document_validation` |
| PubMed adapter (abstracts) | MET | `src/vh/rag/sources/pubmed.py`, `tests/test_step_14_acceptance.py::test_pubmed_adapter_fixture_parsing` |
| PMC Open Access adapter with article-level licence | MET | `src/vh/rag/sources/pmc.py`, `tests/test_step_14_acceptance.py::test_pmc_adapter_fixture_and_licence_enforcement` |
| DailyMed adapter (SPL, section-aware) | MET | `src/vh/rag/sources/dailymed.py`, `tests/test_step_14_acceptance.py::test_dailymed_adapter_spl_sections` |
| OpenFDA adapter (label endpoints) | MET | `src/vh/rag/sources/openfda.py`, `tests/test_step_14_acceptance.py::test_openfda_adapter_label_sections` |
| Local guidelines with sidecar metadata in `data/sources/guidelines/` | MET | `src/vh/rag/sources/guidelines.py`, `tests/test_step_14_acceptance.py::test_local_guidelines_adapter_with_sidecar` |
| RxNorm exposed as terminology service only (not chunked text) | MET | `src/vh/rag/sources/rxnorm.py`, `tests/test_step_14_acceptance.py::test_rxnorm_service_terminology_only` |
| Licence enforcement (unknown/unpermitted rejected & logged) | MET | `src/vh/rag/sources/base.py`, `tests/test_step_14_acceptance.py::test_licence_enforcement_policy` |
| Caching, rate limiting, and retries with NCBI API key config | MET | `src/vh/rag/sources/base.py`, `src/vh/rag/sources/client.py`, `configs/rag.yaml`, `src/vh/common/config.py` |
| Tests use recorded offline fixtures only | MET | `tests/fixtures/rag_sources/`, `data/sources/guidelines/` |
| Network-blocking test fixture enforcing zero live network calls | MET | `tests/conftest.py`, `tests/test_step_14_acceptance.py::test_offline_network_guard_blocks_live_network` |
| NABD drug search regression | MET | `src/vh/rag/sources/nabd.py`, `tests/test_step_14_acceptance.py::test_nabd_drug_search_regression` |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All criteria satisfied with 100% test coverage.
