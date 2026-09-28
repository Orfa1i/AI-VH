# Step 11 Report: P1.5 Case Builder

- **Status:** DONE
- **Phase:** Phase 1: Synthetic Patients & Case Builder
- **Step:** 11 of 54 (P1.5)
- **Run after:** STEP 10 (P1.4) report shows Status: DONE
- **Next:** STEP 12 (P1.6): `plan/prompts/phase-1-synthetic-patients/STEP-12_P1.6_case-validation-suite.md`

---

## 1. Built and Changed Deliverables
- `configs/leakage_terms/`:
  - `acute_coronary_syndrome.yaml`: Comprehensive forbidden diagnosis terms, abbreviations ("ACS", "STEMI", "NSTEMI", "AMI", "MI", "UA"), and clinical synonyms.
  - `community_acquired_pneumonia.yaml`: Forbidden diagnosis terms, abbreviations ("CAP", "PNA"), and clinical synonyms.
  - `diabetic_ketoacidosis.yaml`: Forbidden crisis diagnoses, abbreviations ("DKA", "HHS", "NKH"), and clinical synonyms.
- `src/vh/cases/builder.py`:
  - `LeakageGuard`: Automated scanner compiling word-boundary regex patterns from `configs/leakage_terms/` with case-insensitivity to ensure zero diagnostic leakage in visible presentation, history, or physical exam.
  - `NumberConsistencyChecker`: Structural validator verifying that all numeric tokens appearing in narrative presentation map 100% to documented values in the structured clinical record (vitals, age, duration).
  - `SpecialtyCohortSpec`: Schema modeling target specialty cohorts (`ACS_COHORT`, `CAP_COHORT`, `DKA_COHORT`).
  - `CaseBuilderConfig`: Configuration container managing batch sizes, seeds, dataset lineage, reference dates, and LLM narrative flags.
  - `CaseBuilder`: Deterministic compiler assembling patient encounters into complete `CaseSpec` instances with strict data isolation, zero leakage terms, 100% narrative-number consistency, and full lineage tracking.
- `src/vh/cases/__init__.py`:
  - Exported `CaseBuilder`, `CaseBuilderConfig`, `LeakageGuard`, `NumberConsistencyChecker`, `SpecialtyCohortSpec`, and cohort presets.
- `tests/test_step_11_acceptance.py`:
  - Acceptance suite verifying leakage detection, number consistency, zero leakage across a 500-case batch, 100% number consistency across 500 cases, byte-for-byte determinism with seeds, and LLM narrative mode compliance.

---

## 2. Tests Added and Full-Suite Verification
- **Tests Added**:
  - `tests/test_step_11_acceptance.py::test_leakage_guard_detects_forbidden_terms` (PASSED)
  - `tests/test_step_11_acceptance.py::test_narrative_number_consistency_checker` (PASSED)
  - `tests/test_step_11_acceptance.py::test_zero_leakage_terms_across_500_case_batch` (PASSED)
  - `tests/test_step_11_acceptance.py::test_100_percent_narrative_number_consistency_across_500_cases` (PASSED)
  - `tests/test_step_11_acceptance.py::test_determinism_same_seed_gives_identical_cases` (PASSED)
  - `tests/test_step_11_acceptance.py::test_llm_narrative_mode_passes_same_tests` (PASSED)
- **Full Verification Suite (`scripts/test_all.py`)**:
  - Secret scan: Passed (0 secrets detected).
  - Test results: **123 passed out of 123 tests** (100% pass rate in 273.31s).

---

## 3. Failures Found and Resolved
- **Symptom**: `AssertionError: Mismatch between seeds for CASE-ACU-9996993` during determinism test.
- **Root Cause**: `CaseBuilder.build_single_case()` previously used `datetime.now(timezone.utc).isoformat()` for `built_at` in lineage metadata, introducing microsecond timestamp differences between identical batch runs.
- **Fix**: Added `reference_date: str = "2026-09-28T00:00:00Z"` to `CaseBuilderConfig` and recorded fixed deterministic reference timestamps in lineage and review metadata, ensuring byte-for-byte reproducibility.
- **Regression Test**: Verified via `tests/test_step_11_acceptance.py::test_determinism_same_seed_gives_identical_cases`.

---

## 4. Gap Review
- [x] **Select encounters matching specialty spec (condition codes, time window, severity)**:
  - Proven by `src/vh/cases/builder.py::SpecialtyCohortSpec` and `CaseBuilder.build_single_case()`.
- [x] **Build a CaseSpec (presentation data to visible, later results to hidden)**:
  - Proven by `CaseBuilder._build_hidden_results()` and `tests/test_step_11_acceptance.py`.
- [x] **Narrative generation (template-based by default, optional LLM narrative mode)**:
  - Proven by `CaseBuilder._generate_narrative_template()`, `CaseBuilder._generate_narrative_llm()`, and `tests/test_step_11_acceptance.py::test_llm_narrative_mode_passes_same_tests`.
- [x] **Leakage guard with per-condition term lists in configs/leakage_terms/**:
  - Proven by `configs/leakage_terms/*.yaml` and `tests/test_step_11_acceptance.py::test_leakage_guard_detects_forbidden_terms`.
- [x] **Consistency check (every number in narrative matches structured record)**:
  - Proven by `NumberConsistencyChecker` and `tests/test_step_11_acceptance.py::test_narrative_number_consistency_checker`.
- [x] **Zero leakage terms across 500-case batch**:
  - Proven by `tests/test_step_11_acceptance.py::test_zero_leakage_terms_across_500_case_batch`.
- [x] **100% narrative-number consistency across 500 cases**:
  - Proven by `tests/test_step_11_acceptance.py::test_100_percent_narrative_number_consistency_across_500_cases`.
- [x] **Same seed gives identical cases**:
  - Proven by `tests/test_step_11_acceptance.py::test_determinism_same_seed_gives_identical_cases`.
- [x] **LLM-narrative mode passes the same tests (integration marker)**:
  - Proven by `tests/test_step_11_acceptance.py::test_llm_narrative_mode_passes_same_tests`.

---

## 5. Open Questions and Assumptions
- None. All requirements and acceptance criteria are satisfied with zero open questions.
