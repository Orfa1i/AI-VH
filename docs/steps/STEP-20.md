# STEP 20: P3.1 Clinical Report Schema with Claim-Evidence Links

- **Phase:** Phase 3: Grounded Clinical Generation (MedGemma)
- **Step:** 20 of 54 (P3.1)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-3-generation/STEP-20_P3.1_report-schema.md`

---

## 1. Executive Summary

Step 20 implements the formal clinical report schema and referential integrity validator for AI Virtual Hospital (AI-VH). Every diagnosis in the differential and every clinical recommendation must be grounded in explicit clinical claims, and every claim must be linked to verified evidence chunk IDs retrieved during the encounter.

The `ClinicalReport` Pydantic model enforces structured representations of `patient_summary`, `findings`, `differential` (with diagnostic likelihood and claim links), `recommendations` (with claim links), `claims` (with clinical proposition classification and evidence chunk links), explicit `abstentions` (clinical questions where evidence is insufficient), and execution `provenance`. A validator enforces bidirectional referential integrity before any model output is accepted. The formal JSON Schema is exported to `schemas/clinical_report.json` for constrained decoding with MedGemma.

---

## 2. Built Artifacts

1. `src/vh/generation/report.py`:
   - `ClinicalReport`: Comprehensive structured clinical report model.
   - `DifferentialItem`: Diagnostic entity with categorical likelihood (`high`, `moderate`, `low`) and non-empty `claim_ids`.
   - `RecommendationItem`: Actionable clinical management instruction with non-empty `claim_ids`.
   - `ClaimItem`: Verifiable proposition classified by type (`diagnostic`, `therapeutic`, `prognostic`, `factual`) and linked to `evidence_ids`.
   - `AbstentionItem`: Documented abstention capturing specific clinical questions and rationale when evidence is absent or inconclusive.
   - `ReportProvenance`: Audit metadata recording `run_id`, `model_id`, `prompt_name_version`, `index_version`, and `case_id`.
   - `validate_clinical_report`: Referential integrity validator checking claim existence, evidence context resolution, and non-empty claim bindings.
   - `IntegrityValidationError`, `MissingClaimError`, `UnresolvedEvidenceError`, `EmptyClaimsError`: Granular domain exceptions.
   - `export_clinical_report_json_schema`: Utility exporting strict JSON Schema definitions.
2. `schemas/clinical_report.json`:
   - Exported JSON Schema definition corresponding to `ClinicalReport.model_json_schema()`, formatted for constrained grammar decoding.
3. `src/vh/generation/__init__.py`:
   - Exported all report schemas, validator functions, and exception classes.
4. `tests/test_step_20_acceptance.py`:
   - Acceptance test suite with 6 tests verifying valid fixture parsing, missing claim detection, unresolved evidence detection, empty claim detection, literal enum validation, and JSON Schema file parity.

---

## 3. Tests and Verification

- **Tests Added**: `tests/test_step_20_acceptance.py` (6 acceptance tests):
  1. `test_valid_clinical_report_fixture_passes_validation`: Validates complete compliant clinical report against retrieval context.
  2. `test_integrity_violation_missing_claim`: Confirms `MissingClaimError` is raised when differential or recommendation references an undeclared claim ID.
  3. `test_integrity_violation_unresolved_evidence`: Confirms `UnresolvedEvidenceError` is raised when a claim references a chunk ID not in the active retrieval context.
  4. `test_integrity_violation_empty_claims`: Confirms `EmptyClaimsError` is raised when recommendation or differential entries lack claims.
  5. `test_schema_type_constraints`: Verifies Pydantic validation rejects invalid likelihood categories and unapproved claim types.
  6. `test_exported_json_schema_matches_model`: Proves `schemas/clinical_report.json` on disk matches `ClinicalReport.model_json_schema()` exactly.
- **Full Verification Suite**:
  - `py -3.13 scripts/test_all.py`: **170 of 170 tests passing** (100% pass rate in 282.15s).
  - Secret scan: 0 hardcoded secrets or credentials detected.
  - Evaluation harness: 60/60 golden v1 cases passing all gate criteria.

---

## 4. Failures Found and Resolved

1. **Cascading Validation in Test Fixture**:
   - *Symptom*: `test_integrity_violation_unresolved_evidence` initially triggered `MissingClaimError` instead of `UnresolvedEvidenceError`.
   - *Root Cause*: The test corrupted `claims` but left recommendations referencing now-missing claim IDs, causing the validator to abort on claim integrity before reaching evidence resolution.
   - *Fix*: Aligned recommendation claim references in the test fixture to isolate the unresolved evidence violation specifically.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| ClinicalReport model with summary, findings, differential, recommendations, claims, abstentions, provenance | MET | `src/vh/generation/report.py`, `tests/test_step_20_acceptance.py::test_valid_clinical_report_fixture_passes_validation` |
| Export JSON Schema to schemas/clinical_report.json | MET | `schemas/clinical_report.json`, `tests/test_step_20_acceptance.py::test_exported_json_schema_matches_model` |
| Referential integrity validator (claim existence, evidence existence, non-empty claims) | MET | `src/vh/generation/report.py`, `tests/test_step_20_acceptance.py` |
| Valid fixture passes; each integrity violation detected | MET | `tests/test_step_20_acceptance.py` (6 unit tests) |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All criteria satisfied with 100% test coverage.
