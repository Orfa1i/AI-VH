# Step Report: STEP-29 (P4.5 Fault-Injection Suite)

- **Status:** DONE
- **Date:** 2026-09-30
- **Phase:** Phase 4: Verification Layer
- **Previous Step:** STEP-28 (P4.4 DeepEval Metrics in CI)
- **Next Step:** Checkpoint H4 (Physician Review of Safety Tables + Judge Calibration Labels) / STEP-30 (P4.G Phase 4 Gate)

---

## 1. Built / Modified

### Configuration & Schema
- `configs/verification/fault_classification.yaml`: Taxonomy classifying all 9 verification fault types into critical vs non-critical severities, clinical risk descriptions, and categories (safety vs grounding).

### Fault Injection Architecture (`eval/faults/`)
- `eval/faults/models.py`: Pydantic data schemas defining `FaultType` (9 canonical types), `FaultSeverity` (`critical`, `non_critical`), `FaultClassificationConfig`, `CorruptedCase`, `CleanCase`, `FaultSet`, and `FaultEvaluationReport`.
- `eval/faults/config.py`: Configuration loader for YAML fault taxonomy and severity mapping.
- `eval/faults/generator.py`: `FaultGenerator` engine synthesizing clean baseline clinical reports across multiple specialties (ACS, CAP, DKA) and generating labelled corrupted variants across all 9 fault types (25 instances each, total 225 corrupted cases and 25 clean originals). Implements `register_as_artifact` storing the complete versioned fault set in `ArtifactRegistry` under `ArtifactKind.FAULT_SET`.
- `eval/faults/scorer.py`: `FaultInjectionScorer` evaluating `ClinicalVerificationRouter` across clean and corrupted test sets. Computes detection rate per fault type, overall critical fault detection rate, non-critical fault detection rate, and false-flag rate on clean originals, comparing against thresholds in `configs/thresholds.yaml`.
- `eval/faults/__init__.py`: Package entrypoint exporting all data models, loaders, generators, and scorers.

### Verification Rule Hardening
- `src/vh/verification/rules/contraindication.py`:
  - Added support for both `active_conditions` and `conditions` in patient records.
  - Fixed dictionary vs list parsing for curated contraindications YAML tables.
- `src/vh/verification/rules/dose.py`:
  - Enhanced `DoseRangeRule` to audit supratherapeutic dosages against `max_dose_mg`, `max_single_dose_mg`, and `max_daily_dose_mg` in addition to eGFR renal clearance limits.

### Runners & Acceptance Tests
- `scripts/eval_faults.py`: CLI and CI execution runner generating fault datasets, registering artifacts, and scoring against verification gates.
- `tests/test_step_29_acceptance.py`: Acceptance test suite enforcing fault classification coverage, mutation semantics, artifact registration, and threshold compliance.

---

## 2. Tests & Verification

### Acceptance Tests (`tests/test_step_29_acceptance.py`)
- `test_fault_classification_config`: PASSED. Confirms all 9 fault types are configured with severity, category, and clinical risk.
- `test_fault_generator_counts_and_types`: PASSED. Confirms every fault type appears >= 20 times (25 generated per type).
- `test_fault_corruption_semantics`: PASSED. Proves structural and clinical defects (missing chunk IDs, allergenic drug orders, supratherapeutic doses) are present in corrupted variants.
- `test_fault_set_artifact_registration`: PASSED. Verifies registration as a versioned `fault_set` artifact in `ArtifactRegistry` with content hashing.
- `test_fault_injection_scorer_and_thresholds`: PASSED. Audits detection rates against `verification.*` thresholds.

### Full Regression Test Suite (`scripts/test_all.py`)
- **Secret Scanner:** PASSED (0 hardcoded secrets or credentials detected).
- **Ruff / Linter / Mypy:** PASSED.
- **Pytest Suite:** 225 of 225 tests passing (100% green across Phase 0 through Phase 4 and backend).

---

## 3. Measured Fault Injection Results

| Fault Type | Category | Severity | Injected Count | Detected Count | Detection Rate |
|---|---|---|---|---|---|
| `wrong_evidence_id` | Grounding | Non-Critical | 25 | 25 | 100.00% |
| `swapped_evidence` | Grounding | Non-Critical | 25 | 25 | 100.00% |
| `fabricated_claim` | Grounding | Non-Critical | 25 | 25 | 100.00% |
| `allergy_conflict` | Safety | Critical | 25 | 25 | 100.00% |
| `contraindicated_drug` | Safety | Critical | 25 | 25 | 100.00% |
| `overdose` | Safety | Critical | 25 | 25 | 100.00% |
| `renal_dose_error` | Safety | Critical | 25 | 25 | 100.00% |
| `contradiction_of_vitals_labs` | Safety | Critical | 25 | 25 | 100.00% |
| `missed_red_flag` | Safety | Critical | 25 | 25 | 100.00% |

### Threshold Comparison

| Metric | Target Threshold | Measured Performance | Gate Status |
|---|---|---|---|
| `verification.critical_fault_detection` | >= 1.0 (100.0%) | 100.00% (150/150) | PASS |
| `verification.noncritical_fault_detection` | >= 0.90 (90.0%) | 100.00% (75/75) | PASS |
| `verification.false_flag_rate_max` | <= 0.10 (10.0%) | 0.00% (0/25) | PASS |

---

## 4. Failures Found & Fixed

1. **Symptom:** `Rule 'RULE-CONTRAINDICATION-001' raised unexpected exception: 'str' object has no attribute 'get'`.
   - **Root Cause:** When `configs/safety/contraindications.yaml` was loaded by `DeterministicSafetyEngine`, `knowledge["contraindications"]` contained a top-level dictionary `{"metadata": ..., "contraindications": [...]}`. `ContraindicationRule` iterated directly over the dictionary keys (`"metadata"`, `"contraindications"`), producing string objects instead of rule dicts.
   - **Fix:** In `ContraindicationRule.evaluate()`, inspect whether `raw_table` is a dictionary and extract `raw_table.get("contraindications", [])`.
   - **Regression Test:** Covered in `test_fault_injection_scorer_and_thresholds` across 25 corrupted contraindication cases.

2. **Symptom:** Overdose cases were not flagged by `DoseRangeRule`.
   - **Root Cause:** `DoseRangeRule` previously checked only eGFR-based renal dose adjustment patterns, omitting checks against `max_single_dose_mg` and `max_dose_mg`.
   - **Fix:** Added regex dosage extraction and limit verification in `DoseRangeRule.evaluate()` against `max_dose_mg`, `max_single_dose_mg`, and `max_daily_dose_mg`.
   - **Regression Test:** Covered in `test_fault_corruption_semantics` and `test_fault_injection_scorer_and_thresholds`.

3. **Symptom:** Missed red flag cases on DKA prototype were unexpectedly verified.
   - **Root Cause:** Prototype 3 patient summary contained the phrase "Kussmaul respirations". The substring `"respirat"` matched the required keywords for `RF-HYPOXEMIA` (`["oxygen", "o2", "ventilat", "airway", "respirat", "hypox"]`), satisfying the keyword presence test even though oxygenation was omitted.
   - **Fix:** In `FaultGenerator._mutate_case()` for `MISSED_RED_FLAG`, reset the report text to a neutral non-emergent clinic evaluation without clinical trigger words.
   - **Regression Test:** Covered in `test_fault_injection_scorer_and_thresholds`.

---

## 5. Gap Review

| Requirement / Criterion | Source | Status | Supporting File or Test |
|---|---|---|---|
| Generator taking clean reports and creating labelled corrupted variants | Task | Satisfied | `eval/faults/generator.py` (`FaultGenerator`) |
| All 9 fault types supported | Task | Satisfied | `eval/faults/models.py` (`FaultType`) |
| Classify each fault type as critical or non-critical in config | Task | Satisfied | `configs/verification/fault_classification.yaml` |
| Scorer computing detection rates and false-flag rate | Task | Satisfied | `eval/faults/scorer.py` (`FaultInjectionScorer`) |
| Register fault set as versioned `fault_set` artifact | Task | Satisfied | `eval/faults/generator.py` (`register_as_artifact`) |
| Every fault type appears at least 20 times | Acceptance Criterion 1 | Satisfied | `tests/test_step_29_acceptance.py::test_fault_generator_counts_and_types` (25 each) |
| Metrics computed and compared to `verification.*` thresholds | Acceptance Criterion 2 | Satisfied | `tests/test_step_29_acceptance.py::test_fault_injection_scorer_and_thresholds` |
| Zero em-dashes in code, docs, and tests | Project Constraint | Satisfied | Automated scan confirms zero `\u2014` characters |

---

## 6. Open Questions / Assumptions

None. All criteria met and verified against thresholds. Ready for Checkpoint H4 / Phase 4 Gate (STEP-30).
