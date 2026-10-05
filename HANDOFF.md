# AI Virtual Hospital (AI-VH) : Session Handoff

## 0. Latest Session (2026-10-05) — Review → Feedback → Training Dataset Pipeline (Commit `8a7f291`)
- **Review & Feedback Architecture (`backend/clinical/models.py`, `backend/rl/dataset_curator.py`, `backend/simulation/orchestrator.py`)**:
  - Implemented the complete human review, structured error taxonomy, and curated training dataset pipeline:
    1. **Immutable Original Reports**: The original AI report in `clinical_reports` is treated as strictly read-only and immutable. Feedback submissions never overwrite or mutate original model outputs.
    2. **Separate Storage for Reviews & Corrections**: Reviewer feedback is persisted in `physician_reviews`, while model corrections and training artifacts are stored in `training_dataset_records`.
    3. **Structured Review Taxonomy**:
       - Assessments: `CORRECT`, `PARTIALLY_CORRECT`, `INCORRECT`.
       - Error Taxonomy: `MISSING_INFORMATION`, `HALLUCINATION`, `INCORRECT_DIAGNOSIS`, `INCORRECT_REASONING`, `UNSUPPORTED_RECOMMENDATION`, `INCORRECT_MEDICAL_FACT`, `POOR_EVIDENCE_USE`, `OTHER`.
       - Reviewer Metadata: `physician_name`, `reviewer_role` (`ATTENDING_PHYSICIAN`, `RESIDENT`, `STUDENT`), `specialty`.
       - Structured Corrections: `corrected_diagnosis`, `corrected_reasoning`, `corrected_recommendations`, `corrected_treatment`, and clinical notes.
    4. **13-Field Training Dataset Records (`TrainingDatasetRecord`)**:
       - Preserves all 13 canonical fields: `case_id`, `patient_id`, `report_id`, `model_version`, `specialty`, `original_input`, `original_ai_output`, `reviewer_feedback`, `corrected_output` / `preferred_output`, `provenance`, `review_status`, `dataset_eligibility`, `timestamp`.
    5. **Patient/Case Deduplication**:
       - Prevents duplicate patient cases from artificially inflating training counts. When multiple reviews exist for the same patient/case, subsequent records are flagged with `INELIGIBLE_DUPLICATE` so only unique clinical cases are exported for fine-tuning.
    6. **Ground-Truth Isolation**:
       - Reviewers and students identify errors without seeing hidden Ground Truth, gold standards, or future clinical outcomes. Reports exposed via API strip hidden evaluator keys.
    7. **Strictly Manual Training Enforcement**:
       - Review submission does NOT trigger model training. Model fine-tuning remains strictly manual through authorized operator triggers with guardrails.
- **Persistence & API Integration (`backend/database/` & `backend/api/router.py`)**:
  - Added `training_dataset_records` table to SQLite (`SQLITE_SCHEMA`) and PostgreSQL (`POSTGRES_SCHEMA`) with indexes on `(patient_id, case_id)` and `dataset_eligibility`.
  - Added `save_training_dataset_record()`, `get_training_dataset_records()`, and `is_patient_case_reviewed()` to `HospitalRepository`.
  - Updated `POST /api/reviews` endpoint to accept the rich feedback taxonomy and return the curated training eligibility status.
  - Added `GET /api/rl/dataset/curated` endpoint supporting filtering by `eligibility` (`ELIGIBLE`, `INELIGIBLE_INCOMPLETE`, `INELIGIBLE_DUPLICATE`, `INELIGIBLE_UNGROUNDED`).
- **Frontend Review Dashboard (`frontend/src/`)**:
  - Updated `PhysicianReviewDashboard.tsx`:
    - Assessment selector buttons with color coding (`Correct`, `Partially Correct`, `Incorrect`).
    - Multi-select structured error taxonomy chips with instant descriptions.
    - Reviewer role dropdown (`Attending Physician`, `Resident`, `Medical Student`).
    - Structured correction inputs for primary diagnosis, clinical reasoning, and clinical recommendations.
    - Live dataset eligibility indicator badge reflecting whether the submission meets training eligibility criteria in real time.
  - Added `frontend/src/components/review/taxonomy.ts` and updated `types.ts` with all enums and schemas.
- **Verification Results**:
  - `backend/tests/test_review_dataset_pipeline.py`: **8 of 8 tests passing (100% green)** in 10.86s.
  - Full backend test suite (`backend/tests/`): **123 of 123 tests passing (100% green)** in 293.92s.
  - Frontend test suite (`frontend/`): **10 test files passed (39 tests green)**.
  - Frontend production build (`npm run build`): compiled cleanly in 1.23s with zero errors.
  - Frontend lint (`npm run lint`): 0 errors across all 54 files.

---

## 1. Complete End-to-End Clinical AI Pipeline Status
The full clinical AI pipeline is now fully implemented, integrated, and verified:
$$\text{Synthea} \rightarrow \text{Synthetic Case Builder} \rightarrow \text{Case Pool} \rightarrow \text{Admit Patient} \rightarrow \text{Start Diagnosis} \rightarrow \text{Router} \rightarrow \text{Specialty Agent} \rightarrow \text{MedGemma (4B)} + \text{Specialty Book RAG} + \text{Shared Knowledge Sources} \rightarrow \text{Diagnosis Report} \rightarrow \text{Multi-Stage Evaluation} \rightarrow \text{Review Page} \rightarrow \text{Student/Reviewer Feedback} \rightarrow \text{Model Training Dataset} \rightarrow \text{Training} \rightarrow \text{Improved Model}$$

1. **Synthetic Case Intake & Case Pool (Commit `e3e4c0d`)**:
   - Synthea FHIR ingestion to high-fidelity simulated lab banks and cases.
   - Deterministic patient deduplication via SHA-256 MRN hashing.
2. **Specialty Routing & Multi-Specialist RAG (Commit `ecc1451`)**:
   - `MedicalSpecialtyRouter` assigns cases to `INTERNAL_MEDICINE` vs `CARDIOLOGY`.
   - Dedicated medical books: Harrison's for Internal Medicine, Braunwald's (16,359 chunks) for Cardiology.
   - Decoupled router from model training.
3. **Ground Truth Isolation & Shared Knowledge Sources (Commit `57b12ec`)**:
   - Autonomous `determine_diagnostic_workup()` without ground-truth leakage.
   - Unified RxNorm and NABD shared pharmacology sources across all agents.
4. **Generalized Multi-Source Verification (Commit `9df15ce`)**:
   - Cross-source citation verifier validating evidence against authorized texts.
5. **Specialist Diagnostic Workflow (Commit `4b702ec`)**:
   - 11-step diagnostic synthesis workflow combining clinical presentation, book RAG, and pharmacology evidence without verbatim source copying.
6. **Independent 6-Dimension Evaluation Pipeline (Commit `619a5ae`)**:
   - Independent automated evaluation covering clinical context relevance, hallucination detection, structural compliance, reasoning consistency, recommendation validity, and evidence grounding quality.
   - Fail-closed execution and separate schema storage.
7. **Review → Feedback → Training Dataset Pipeline (Commit `8a7f291`)**:
   - Immutable original AI reports, separate review and correction storage, 8-code structured error taxonomy, 13-field training dataset record preservation, patient deduplication, and manual-only training enforcement.

---

## 2. Key Architectural Invariants & Rationale
- **Single Generation Model**: Local `google/medgemma-4b` 4-bit NF4 running on the user's RTX 4060 GPU is the ONLY text generation model across all specialty agents.
- **Router Independence**: `MedicalSpecialtyRouter` is a deterministic clinical router that assigns cases to specialties; it is NEVER the model being trained or fine-tuned.
- **Specialty Book RAG + Shared Knowledge**: Each specialty agent has its own dedicated Medical Book (Harrison's for Internal Medicine, Braunwald's for Cardiology), while all agents share unified clinical pharmacology sources (RxNorm, NABD).
- **Ground Truth Isolation**: Specialty agents never access ground truth data or recommended labs during encounter simulation. All laboratory and imaging orders are selected autonomously via `determine_diagnostic_workup()`.
- **Review & Dataset Separation**: Human/student reviews and automated evaluations are stored in separate schemas (`physician_reviews` vs `report_evaluations`), and training is strictly manual.
- **Immutability of AI Generations**: AI reports are permanent historical artifacts; corrections are stored as distinct preferred outputs for DPO/training pairs.

---

## 3. Current Verification State
- **Backend Test Suite (`backend/tests/`)**: **123 of 123 tests passing (100% green)** in 293.92s.
- **Review Dataset Pipeline Suite (`backend/tests/test_review_dataset_pipeline.py`)**: **8 of 8 tests passing (100% green)**.
- **Evaluation Pipeline Suite (`backend/tests/test_evaluation_pipeline.py`)**: **23 of 23 tests passing (100% green)**.
- **Acceptance Tests (`tests/`)**: **29 of 29 tests passing (100% green)**.
- **Frontend Test Suite (`frontend/`)**: **10 test files passed (39 tests green)**.
- **Frontend Production Build (`npm run build`)**: Built in 1.23s with zero TypeScript or bundling errors.
- **Frontend Linter (`npm run lint`)**: 0 errors across 54 files.

---

## 4. Next Steps
1. Perform an end-to-end clinical simulation walk-through from UI (Admit -> Run Simulation -> Specialty Routing -> Diagnostic Synthesis -> Independent Evaluation -> Physician Review -> Curated Training Dataset Export).
2. Expand specialty roster (e.g., Neurology with Adams & Victor's RAG, Pulmonology with Murray & Nadel's RAG) using the established modular architecture.
3. Fine-tuning dataset evaluation: execute manual fine-tuning run against baseline MedGemma 4B once sufficient curated preference pairs have been collected from physician reviews.
