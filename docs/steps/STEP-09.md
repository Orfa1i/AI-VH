# STEP 09 Report: P1.3 Patient store and FHIR loader

- **Status:** DONE
- **Date:** 2026-09-28
- **Phase:** Phase 1: Synthetic Patients & Case Builder
- **Governing Prompt:** `plan/prompts/phase-1-synthetic-patients/STEP-09_P1.3_patient-store.md`
- **Governing Standard:** `plan/CLAUDE.md` (Sections 1 to 5)

---

## 1. Built and Modified Deliverables

1. **Architectural Decision Record (`docs/decisions/ADR-0002-patient-store.md`)**:
   - Evaluated dedicated HAPI FHIR Java server container vs Relational JSONB clinical patient store.
   - Decided on Relational JSONB architecture with indexed relational search columns (`patient_id`, `resource_type`, `effective_datetime`, `code`) and full JSON/JSONB document retention. Avoids heavy 2GB JVM overhead and enables seamless dual-mode execution (PostgreSQL in production, embedded SQLite for fast offline testing).

2. **Patient Repository (`src/vh/cases/patient_repo.py`)**:
   - Implemented `PatientRepository` managing `fhir_resources` table with primary key `(resource_type, resource_id)`.
   - Created B-tree performance indexes on `(patient_id, resource_type)`, `(patient_id, effective_datetime)`, and `code`.
   - Provided high-performance query methods: `get_patient`, `get_encounters`, `get_observations` (with time-window and code filters), `get_conditions`, `get_medications`, `get_allergies`, `get_clinical_timeline`, and `count_resources`.

3. **Idempotent FHIR Loader (`src/vh/cases/fhir_loader.py`)**:
   - Implemented `FHIRBundleLoader` parsing transaction and collection bundles.
   - Extracts subject and encounter linkages, resolves clinical effective timestamps, maps terminology codes, and performs upsert operations.
   - Guarantees complete idempotency: reloading identical bundles produces zero duplicate records and updates existing rows in place.

4. **Package and Checklist Updates**:
   - Exported `PatientRepository`, `FHIRBundleLoader`, and `LoadSummary` in `src/vh/cases/__init__.py`.
   - Marked STEP 09 complete in `plan/README.md`.

---

## 2. Tests Added and Full Suite Verification

- **Tests Added**: `tests/test_step_09_acceptance.py` (5 test cases):
  - `test_loader_resource_counts_equal_bundle_entry_counts`: Verifies stored resource counts match bundle entry counts exactly.
  - `test_idempotent_loading_creates_zero_duplicates`: Verifies reloading identical bundles creates 0 new records and causes 0 duplicate rows.
  - `test_query_patient_and_encounters`: Verifies retrieval of patient demographics and associated encounters.
  - `test_time_window_query_over_observations`: Verifies time-window filtering (`start_time`, `end_time`) returns chronologically ordered records.
  - `test_clinical_timeline_aggregates_multiple_resource_types`: Verifies aggregated multi-resource timeline ordering.

- **Full Suite Result**:
  - `pytest`: **111 passed out of 111** (100% pass rate in 295.01s).
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.

---

## 3. Failures Found and Resolved

None. All relational schema queries, reference cleaning, and idempotent loader logic passed on initial execution.

---

## 4. Gap Review: Acceptance Criteria vs Evidence

| Acceptance Criterion | Status | Evidence / Proving Test |
| :--- | :--- | :--- |
| Resource counts after loading equal counts in the bundles | **PASS** | `tests/test_step_09_acceptance.py::test_loader_resource_counts_equal_bundle_entry_counts` |
| Loading twice creates no duplicates | **PASS** | `tests/test_step_09_acceptance.py::test_idempotent_loading_creates_zero_duplicates` |
| Query tests over fixture bundles return correct, time-ordered results | **PASS** | `tests/test_step_09_acceptance.py::test_query_patient_and_encounters`, `test_time_window_query_over_observations` |
| ADR-0002 records storage choice and rationale | **PASS** | `docs/decisions/ADR-0002-patient-store.md` |

---

## 5. Open Questions & Physician Items

None. All criteria satisfied.
Next Step: STEP 10 (P1.4 Case spec schema and AgentView isolation) in `plan/prompts/phase-1-synthetic-patients/STEP-10_P1.4_case-spec-schema.md`.
