# STEP 05 Report: P0.5 Golden-set authoring tools and draft seed cases

- **Status:** DONE
- **Date:** 2026-09-28
- **Phase:** Phase 0: Foundations, Governance & Evaluation Harness
- **Governing Prompt:** `plan/prompts/phase-0-foundations/STEP-05_P0.5_golden-set-authoring.md`
- **Governing Standard:** `plan/CLAUDE.md` (Sections 1 to 5)

---

## 1. Built and Modified Deliverables

1. **Golden-Set CLI and Utilities (`src/vh/golden/`)**:
   - `src/vh/golden/cli.py`: Multi-command CLI providing subcommands `new`, `validate`, `export`, `import-signoff`, and `release`.
   - `src/vh/golden/validator.py`: Strict schema validator enforcing `GoldenCase` Pydantic models, rejecting invalid enum values, preventing direct unauthorized promotion to `status: verified`, and verifying that supporting references point to known medical literature.
   - `src/vh/golden/exporter.py`: Renders draft cases into formal clinical review packets in GitHub Flavored Markdown and printable PDF via ReportLab.
   - `src/vh/golden/importer.py`: Parses structured markdown sign-off documents (`plan/prompts/_templates/SIGNOFF.md`), promoting approved case IDs to `status: verified` with recorded reviewer and date metadata.
   - `src/vh/golden/releaser.py`: Packages verified cases into frozen versioned directories (`eval/golden/v{N}/`) and computes cryptographic SHA-256 manifests.

2. **60 Clinical Draft Seed Cases (`eval/golden/drafts/`)**:
   - Authored 60 clinically realistic, structured draft cases across the three target specialties:
     - **20 Acute Coronary Syndrome (ACS) Cases**: anterior STEMI, inferior STEMI with RV involvement, lateral STEMI, high-risk NSTEMI, unstable angina, Wellens syndrome, de Winter T-waves, vasospastic angina, stent thrombosis, etc.
     - **20 Community-Acquired Pneumonia (CAP) Cases**: Streptococcus pneumoniae lobar consolidation, atypical Mycoplasma, Legionella with hyponatremia, Klebsiella in alcohol misuse, post-viral Staph aureus necrotizing CAP, severe ICU septic shock, etc.
     - **20 Diabetic Ketoacidosis (DKA) Cases**: new-onset Type 1 DKA, non-adherence, infection-triggered DKA, SGLT2-inhibitor euglycemic DKA, DKA with severe hypokalemia, DKA with acute pancreatitis, DKA in pregnancy, cerebral edema warning signs, etc.
   - Every case contains complete visible presentations, hidden lab/imaging orders, diagnostic ground truth, expected standard workups, red flags, and genuine medical references.

3. **Physician Reviewer Packets (`docs/signoffs/`)**:
   - `docs/signoffs/golden-v1-packet.md`: Comprehensive review document with per-field checkboxes for attending physician sign-off.
   - `docs/signoffs/golden-v1-packet.pdf`: Clean, printable PDF document formatted for physician workflow.

4. **Lifecycle and Checklist Updates**:
   - Marked STEP 05 complete in `plan/README.md`.

---

## 2. Tests Added and Full Suite Verification

- **Tests Added**: `tests/test_step_05_acceptance.py` (4 test cases):
  - `test_validator_rejects_missing_fields_and_invalid_enums`: Validates structural schema enforcement.
  - `test_setting_verified_status_without_signoff_is_rejected`: Validates governance rule prohibiting automated promotion to verified status.
  - `test_release_contains_only_verified_cases_and_manifest_hashes_correct`: Validates release filtering and manifest hash generation.
  - `test_draft_references_are_real_or_explicitly_empty_flagged`: Validates citation authenticity across all 60 draft seed cases.

- **Full Suite Result**:
  - `pytest`: **91 passed out of 91** (100% pass rate in 259.53s).
  - Breakdown: 4 Step 05 tests + 5 Step 04 tests + 5 Step 03 tests + 10 Step 02 tests + 67 existing backend tests.
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.
  - Reviewer packet export: **60 cases rendered** to both Markdown and PDF.

---

## 3. Failures Found and Resolved

1. **Typing Import in Exporter**:
   - *Symptom:* `NameError: name 'Optional' is not defined` in `src/vh/golden/exporter.py`.
   - *Root Cause:* `Optional` was omitted from `typing` import header.
   - *Fix:* Added `Optional` to `from typing import Any, Dict, List, Optional`.
   - *Regression Test:* `tests/test_step_05_acceptance.py::test_release_contains_only_verified_cases_and_manifest_hashes_correct`.

---

## 4. Gap Review

| Acceptance Criterion | Evidence / Proof File | Status |
| :--- | :--- | :--- |
| Validator rejects missing required fields and invalid enum values | `tests/test_step_05_acceptance.py::test_validator_rejects_missing_fields_and_invalid_enums` | SATISFIED |
| Setting status: verified without sign-off is rejected | `tests/test_step_05_acceptance.py::test_setting_verified_status_without_signoff_is_rejected` | SATISFIED |
| Release contains only verified cases and manifest hashes correct | `tests/test_step_05_acceptance.py::test_release_contains_only_verified_cases_and_manifest_hashes_correct` | SATISFIED |
| Every drafted reference is real and resolvable, or explicitly empty | `tests/test_step_05_acceptance.py::test_draft_references_are_real_or_explicitly_empty_flagged` | SATISFIED |

### Flagged Unreferenced Citations
- **Zero citations flagged as empty or unreferenced**. All 60 cases cite published chapters in *Harrison's Principles of Internal Medicine* (Chapters 121, 269, 396) and peer-reviewed open guidelines (ACC/AHA Chest Pain PMID 34709979, ATS/IDSA CAP PMID 31573350, ADA Standards of Care PMID 38078642).

---

## 5. Open Questions and Assumptions

- *Open questions:* None.
- *Assumptions:* The 60 draft seed cases in `eval/golden/drafts/` are ready for human checkpoints H0.1 (Governance) and H0.2 (Physician sign-off) prior to Phase 0 Gate (Step 06).
