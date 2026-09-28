# STEP 04 Report: P0.4 Evaluation harness and frozen golden-set mechanism

- **Status:** DONE
- **Date:** 2026-09-28
- **Phase:** Phase 0: Foundations, Governance & Evaluation Harness
- **Governing Prompt:** `plan/prompts/phase-0-foundations/STEP-04_P0.4_evaluation-harness.md`
- **Governing Standard:** `plan/CLAUDE.md` (Sections 1 to 5)

---

## 1. Built and Modified Deliverables

1. **Golden Case Schema and Isolation (`src/vh/cases/schema.py`, `eval/schema/golden_case.json`)**:
   - `GoldenCase`: Complete Pydantic model with `case_id`, `specialty`, `patient_ref`, `visible_presentation`, `hidden_results`, `ground_truth` (`primary_dx`, `acceptable_differential`, `expected_workup`, `red_flags`), `supporting_references`, `status` (`draft` | `verified`), `reviewer`, `reviewed_at`, `version`.
   - `CaseView`: Sanitized agent view containing only visible presentation data (`extra="forbid"`), strictly omitting ground truth and unreleased hidden findings.
   - `eval/schema/golden_case.json`: Exported standard JSON Schema.

2. **Frozen Golden Set and Integrity Enforcer (`eval/harness/manifest.py`, `eval/golden/v1/`)**:
   - `manifest.json`: Stores SHA-256 cryptographic hashes for each release file.
   - `validate_manifest()`: Strictly enforces file integrity; any modification, tampering, or missing file raises `GoldenSetIntegrityError`.
   - Seed verified cases authored for target specialties:
     - `eval/golden/v1/case_acs_001.json` (Acute Coronary Syndrome / STEMI)
     - `eval/golden/v1/case_cap_002.json` (Community-Acquired Pneumonia)
     - `eval/golden/v1/case_dka_003.json` (Diabetic Ketoacidosis)
     - `eval/golden/v1/manifest.json`: Validated release manifest.

3. **Pipeline and Scorer Protocols (`eval/harness/interfaces.py`)**:
   - `Pipeline` protocol: `run(case_view: CaseView) -> PipelineResult`.
   - `Scorer` protocol: `score(results, golden_cases) -> Dict[str, float]`.
   - `DummyPipeline`: Deterministic test pipeline.
   - `DummyScorer`: Baseline evaluator computing schema validity, recall, mrr, and fault detection metrics.
   - `SpyPipeline`: Verification spy proving ground truth isolation.

4. **Evaluation Harness Runner (`eval/harness/runner.py`)**:
   - `run_evaluation()`: Orchestrates manifest validation, case execution, metric calculation, governance threshold comparisons, and report generation.
   - Governance rule enforcement: Any metric lacking a defined threshold or having a `null` threshold in `configs/thresholds.yaml` reports **FAIL** (never a silent PASS).
   - Generates `eval/reports/<run_id>/report.json` and `report.md`.
   - Strict determinism: Identical inputs produce identical reports.

5. **Lifecycle and Build Tooling**:
   - Updated `Makefile` with parameterized `eval` target (`make eval GOLDEN=vN PIPELINE=<name>`).
   - Updated `scripts/test_all.py` and `scripts/test-all.ps1` with harness runner execution.
   - Checked off Step 04 in `plan/README.md`.

---

## 2. Tests Added and Full Suite Verification

- **Tests Added**: `tests/test_step_04_acceptance.py` (5 test cases):
  - `test_dummy_pipeline_scores_end_to_end_and_writes_reports`: Verifies full harness execution, metric scoring, and report file generation.
  - `test_modifying_frozen_version_refuses_with_clear_error`: Proves harness refuses execution on tampered files with `GoldenSetIntegrityError`.
  - `test_metric_with_no_or_null_threshold_reports_fail`: Proves null and undefined thresholds evaluate to FAIL.
  - `test_identical_inputs_give_identical_report`: Proves deterministic report generation.
  - `test_pipeline_never_receives_ground_truth`: Proves ground truth and hidden results are never passed to pipelines.

- **Full Suite Result**:
  - `pytest`: **87 passed out of 87** (100% pass rate in 286.33s).
  - Breakdown: 5 Step 04 tests + 5 Step 03 tests + 10 Step 02 tests + 67 existing backend tests.
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.
  - Harness run (`python -m eval.harness.runner --golden v1 --pipeline dummy`): **PASS** across all 3 verified golden cases.

---

## 3. Failures Found and Resolved

1. **Pydantic Deprecation Notice in Runner**:
   - *Symptom:* `PydanticDeprecatedSince20: The dict method is deprecated; use model_dump instead`.
   - *Root Cause:* Calling `.dict()` on Pydantic v2 models.
   - *Fix:* Replaced `.dict()` with `.model_dump()` in `eval/harness/runner.py` and `tests/test_step_04_acceptance.py`.
   - *Regression Test:* `tests/test_step_04_acceptance.py`.

---

## 4. Gap Review

| Acceptance Criterion | Evidence / Proof File | Status |
| :--- | :--- | :--- |
| Dummy pipeline scored end-to-end and report written | `tests/test_step_04_acceptance.py::test_dummy_pipeline_scores_end_to_end_and_writes_reports` | SATISFIED |
| Modifying file in frozen version makes harness refuse with clear error | `tests/test_step_04_acceptance.py::test_modifying_frozen_version_refuses_with_clear_error` | SATISFIED |
| Metric with no or null threshold reported FAIL (never silent PASS) | `tests/test_step_04_acceptance.py::test_metric_with_no_or_null_threshold_reports_fail` | SATISFIED |
| Same inputs give identical report (ignoring timestamps) | `tests/test_step_04_acceptance.py::test_identical_inputs_give_identical_report` | SATISFIED |
| Test proves pipeline never receives ground_truth fields | `tests/test_step_04_acceptance.py::test_pipeline_never_receives_ground_truth` | SATISFIED |

---

## 5. Open Questions and Assumptions

- *Open questions:* None.
- *Assumptions:* Seed cases in `eval/golden/v1/` serve as the initial frozen testbed for harness validation ahead of physician sign-off in Step 05.
