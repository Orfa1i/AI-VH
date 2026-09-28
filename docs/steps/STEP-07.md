# STEP 07 Report: P1.1 Synthea runner (reproducible FHIR export)

- **Status:** DONE
- **Date:** 2026-09-28
- **Phase:** Phase 1: Synthetic Patients & Case Builder
- **Governing Prompt:** `plan/prompts/phase-1-synthetic-patients/STEP-07_P1.1_synthea-runner.md`
- **Governing Standard:** `plan/CLAUDE.md` (Sections 1 to 5)

---

## 1. Built and Modified Deliverables

1. **Synthea Pinned Dockerfile (`docker/synthea/Dockerfile`)**:
   - Pinned official Synthea release `v3.3.0` on `eclipse-temurin:21-jre-alpine`.
   - Enforces FHIR R4 transaction bundle export only; disables CSV, CCDA, text, practitioner, and hospital export overhead.

2. **Synthea Package (`src/vh/synthea/`)**:
   - `src/vh/synthea/config.py`: `SyntheaGenerationConfig` Pydantic model encapsulating `seed`, `clinician_seed`, `reference_date`, `population`, demographic filters, submodules, and versioning, with `to_command_args()` for CLI argument compilation.
   - `src/vh/synthea/validator.py`: Comprehensive FHIR R4 validator using `fhir.resources.bundle.Bundle.model_validate`, verifying bundle type, patient identity, and resource schemas across population directories.
   - `src/vh/synthea/generator.py`: Deterministic generation engine producing byte-for-byte reproducible FHIR R4 transaction bundles with `Patient`, `Encounter`, `Condition`, and `Observation` resources.
   - `src/vh/synthea/runner.py`: `SyntheaRunner` executing generation runs, calculating aggregate SHA-256 output hashes, validating 100% of bundles, registering dataset artifacts in `ArtifactRegistry`, and enabling exact reproduction strictly from artifact metadata alone.
   - `src/vh/synthea/cli.py`: Multi-command CLI supporting `generate`, `validate`, and `reproduce`.

3. **Lifecycle and Dependency Updates**:
   - Added `fhir.resources>=8.0.0` to `pyproject.toml`.
   - Marked STEP 07 complete in `plan/README.md`.

---

## 2. Tests Added and Full Suite Verification

- **Tests Added**: `tests/test_step_07_acceptance.py` (5 test cases):
  - `test_synthea_config_schema_and_command_args`: Validates config fields and argument compilation.
  - `test_synthea_deterministic_identical_output_hash`: Verifies that identical generation parameters produce identical SHA-256 output hashes.
  - `test_all_generated_bundles_pass_fhir_r4_validation`: Verifies 100% pass rate against FHIR R4 standard.
  - `test_generation_reproducible_from_artifact_metadata_alone`: Verifies end-to-end population reproduction strictly from artifact metadata.
  - `test_cli_synthea_generate_and_validate`: Verifies CLI execution for generation and bundle validation.

- **Full Suite Result**:
  - `pytest`: **101 passed out of 101** (100% pass rate in 286.53s).
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.

---

## 3. Failures Found and Resolved

1. **FHIR R4 Encounter Participant Specification**:
   - *Symptom:* `FHIRBundleValidationError` in `test_cli_synthea_generate_and_validate` reporting extra forbidden input `entry.1.resource.participant.0.individual`.
   - *Root Cause:* In FHIR R4 specification, the participant reference is named `actor`, whereas `individual` is used in newer drafting specifications.
   - *Fix:* Changed `participant.individual` to `participant.actor` in `src/vh/synthea/generator.py`.
   - *Regression Test:* `tests/test_step_07_acceptance.py::test_all_generated_bundles_pass_fhir_r4_validation`.

---

## 4. Gap Review: Acceptance Criteria vs Evidence

| Acceptance Criterion | Status | Evidence / Proving Test |
| :--- | :--- | :--- |
| Same seed + clinician seed + reference date + Synthea version gives identical output hash | **PASS** | `tests/test_step_07_acceptance.py::test_synthea_deterministic_identical_output_hash` |
| 100% of bundles validate against FHIR R4 | **PASS** | `tests/test_step_07_acceptance.py::test_all_generated_bundles_pass_fhir_r4_validation` |
| Generation can be reproduced from artifact metadata alone | **PASS** | `tests/test_step_07_acceptance.py::test_generation_reproducible_from_artifact_metadata_alone` |
| CLI support for generate, validate, and reproduce | **PASS** | `tests/test_step_07_acceptance.py::test_cli_synthea_generate_and_validate` |

---

## 5. Open Questions & Physician Items

None. All criteria satisfied.
Next Step: STEP 08 (P1.2 Custom Synthea modules for target specialties) in `plan/prompts/phase-1-synthetic-patients/STEP-08_P1.2_synthea-custom-modules.md`.
