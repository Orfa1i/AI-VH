# Step 10 Report: P1.4 Case Spec Schema and AgentView Isolation

- **Status:** DONE
- **Phase:** Phase 1: Synthetic Patients & Case Builder
- **Step:** 10 of 54 (P1.4)
- **Run after:** STEP 09 (P1.3) report shows Status: DONE
- **Next:** STEP 11 (P1.5): `plan/prompts/phase-1-synthetic-patients/STEP-11_P1.5_case-builder.md`

---

## 1. Built and Changed Deliverables
- `src/vh/cases/spec.py`:
  - `DataIsolationError`: Dedicated security exception inheriting from `PermissionError`, raised upon any unauthorized access to hidden results or gold-standard ground truth.
  - `VisiblePresentation`: Encapsulates clinical presentation narrative, patient demographics, past history, current medications, allergies, initial vitals, physical exam, and raw attributes.
  - `HiddenResult`: Models diagnostic laboratory, imaging, or procedural findings with `order_code`, `order_name`, `result`, `turnaround_time_minutes`, `category`, and `loinc_code`.
  - `ReleasedResult`: Diagnostic finding explicitly ordered, turnaround elapsed, and released to an `AgentView`.
  - `AgentView`: Sanitized, strictly isolated, immutable (`frozen=True`, `extra="forbid"`) view supplied to clinical agents, pipelines, and evaluators. Intercepts all dot-attribute, dictionary-subscript, and `get()` calls targeting hidden data or ground truth to guarantee zero leakage.
  - `CaseSpec`: Complete clinical case specification used by simulation orchestrators, evaluation scorers, and attending reviewers. Provides `to_agent_view()`, `release(order, audit_logger)`, `release_to_view(view, order)`, `from_golden_case(golden_case)`, and `to_golden_case()`.
- `src/vh/cases/schema.py`:
  - Extended `GoldenCase` with `to_case_spec()` and `to_agent_view()` helper methods.
- `src/vh/cases/__init__.py`:
  - Exported `CaseSpec`, `AgentView`, `VisiblePresentation`, `HiddenResult`, `ReleasedResult`, and `DataIsolationError`.
- `tests/test_step_10_acceptance.py`:
  - Acceptance suite verifying CaseSpec structure, zero-leakage recursive serialization, access prohibition, logged order release, and lossless round-tripping across all 60 golden cases.

---

## 2. Tests Added and Full-Suite Verification
- **Tests Added**:
  - `tests/test_step_10_acceptance.py::test_case_spec_structure_and_validation` (PASSED)
  - `tests/test_step_10_acceptance.py::test_agent_view_serialization_zero_leakage` (PASSED)
  - `tests/test_step_10_acceptance.py::test_agent_view_access_attempts_raise` (PASSED)
  - `tests/test_step_10_acceptance.py::test_agent_view_logged_order_release` (PASSED)
  - `tests/test_step_10_acceptance.py::test_golden_case_round_trip_synthetic` (PASSED)
  - `tests/test_step_10_acceptance.py::test_golden_case_round_trip_all_golden_v1_cases` (PASSED)
- **Full Verification Suite (`scripts/test_all.py`)**:
  - Secret scan: Passed (0 secrets detected).
  - Test results: **117 passed out of 117 tests** (100% pass rate in 264.38s).

---

## 3. Failures Found and Resolved
- **Symptom**: `TypeError: multiple bases have instance lay-out conflict` when defining `class DataIsolationError(PermissionError, AttributeError, KeyError)`.
- **Root Cause**: CPython built-in exception classes (`PermissionError` which extends C-level `OSError`, `AttributeError`, and `KeyError` which extends `LookupError`) have incompatible internal C-struct memory layouts, prohibiting multi-exception inheritance among them.
- **Fix**: Derived `DataIsolationError` directly from `PermissionError`, allowing `pytest.raises((DataIsolationError, PermissionError, ...))` to cleanly match access violations across both dot-attribute and dictionary subscript lookups.
- **Regression Test**: Verified via `tests/test_step_10_acceptance.py::test_agent_view_access_attempts_raise`.

---

## 4. Gap Review
- [x] **CaseSpec three-part structure (visible, hidden, ground_truth)**:
  - Proven by `src/vh/cases/spec.py::CaseSpec` and `tests/test_step_10_acceptance.py::test_case_spec_structure_and_validation`.
- [x] **AgentView isolation (no field, method or reference reaches hidden or ground_truth)**:
  - Proven by `src/vh/cases/spec.py::AgentView` and `tests/test_step_10_acceptance.py::test_agent_view_access_attempts_raise`.
- [x] **Serializing an AgentView contains no hidden or ground-truth keys (recursive test)**:
  - Proven by `tests/test_step_10_acceptance.py::test_agent_view_serialization_zero_leakage`.
- [x] **Any attempt to reach hidden data from an AgentView raises**:
  - Proven by `tests/test_step_10_acceptance.py::test_agent_view_access_attempts_raise`.
- [x] **Golden case to CaseSpec round-trip is lossless**:
  - Proven across synthetic cases and all 60 golden v1 cases by `tests/test_step_10_acceptance.py::test_golden_case_round_trip_all_golden_v1_cases`.
- [x] **Hidden results arrive only through explicit logged release(order) call**:
  - Proven by `tests/test_step_10_acceptance.py::test_agent_view_logged_order_release`.

---

## 5. Open Questions and Assumptions
- None. All requirements and acceptance criteria are satisfied with zero open questions.
