# AI Virtual Hospital (AI-VH) : Session Handoff

## 1. What Was Accomplished
- **Phase 0, 1, 2, 3: 100% COMPLETE & CERTIFIED (Tags: `phase-0-pass`, `phase-1-pass`, `phase-2-pass`, `phase-3-pass`)**.
- **Phase 4: Verification Layer (Steps 25 to 30)**:
  - **Step 25 (P4.1 Deterministic Safety Rules Engine)**:
    - Built `src/vh/verification/rules/` (`base.py`, `allergy.py`, `contraindication.py`, `interaction.py`, `dose.py`, `contradiction.py`, `red_flags.py`, `engine.py`).
    - Built curated safety tables in `configs/safety/` (`dose_ranges.yaml`, `contraindications.yaml`, `drug_interactions.yaml`, `red_flags.yaml`) with `status: draft` pending physician review at Checkpoint H4.
    - Authored `docs/decisions/ADR-0005-safety-interaction-source.md` documenting NLM RxNav interaction API retirement in January 2024.
    - 9 acceptance tests passing in `tests/test_step_25_acceptance.py`.
    - Authored `docs/steps/STEP-25.md` and committed `d070015`.
  - **Step 26 (P4.2 Claim Grounding and Citation Checker)**:
    - Authored prompt template `src/vh/prompt_templates/grounding_judge/1.md` enforcing strict judge isolation and structured output.
    - Implemented `ClaimGroundingChecker`, `GroundingVerdict`, `ClaimGroundingJudgment`, and `ReportGroundingResult` in `src/vh/verification/grounding.py`.
    - Implemented statistical calibration functions `compute_cohens_kappa`, `compute_confusion_matrix`, and `evaluate_calibration`.
    - Implemented CLI tools `run_calibration_export` and `run_calibration_score` in `src/vh/verification/cli.py`, mounted into `src/vh/cli.py` under `vh verify`.
    - Exported 100 stratified claim-evidence pairs across Cardiology, Pulmonology, and Endocrinology cohorts to `docs/signoffs/H4-judge-labels-template.csv` and `H4-judge-labels.csv`.
    - 9 acceptance tests passing in `tests/test_step_26_acceptance.py`.
    - Authored `docs/steps/STEP-26.md` and committed `a005b37`.
  - **Step 27 (P4.3 Runtime Guardrails and Verified/Flagged Routing)**:
    - Authored canonical NeMo Guardrails configuration in `src/vh/verification/guardrails/`:
      - `config.yml`: Core guardrails configuration.
      - `rails/input.co`: Input Colang flows scoping requests strictly to clinical case processing and blocking prompt injections.
      - `rails/output.co`: Output Colang flows invoking deterministic safety rules and claim grounding checks.
      - `actions.py`: Custom NeMo Guardrails actions executing safety rules and grounding checks.
      - `runtime.py`: `ClinicalGuardrailsRuntime` coordinating input and output rail validation.
    - Implemented `ClinicalVerificationRouter`, `VerificationStatus`, and immutable `VerificationEnvelope` in `src/vh/verification/router.py`.
    - Enforced fail-closed policy: any checker exception or timeout immediately routes reports to `flagged` with reason `verification_error`.
    - Enforced routing policy: `verified` only if zero critical findings, zero major findings, and all claims supported (partial claims routed to flagged); otherwise `flagged` with explicit structured reasons.
    - Verified p95 latency at sub-10ms (strictly within threshold `verification.p95_latency_s: 5.0`).
    - 11 acceptance tests passing in `tests/test_step_27_acceptance.py`.
    - Full regression test suite passing: 216 of 216 tests passing. Secret scanner: 0 secrets.
    - Authored `docs/steps/STEP-27.md`.
    - Marked Step 27 complete in `plan/README.md`.
    - Git commit `6059c16`: `feat(verification): complete Step 27 runtime guardrails and verified/flagged routing`.

---

## 2. Key Decisions and Rationale
- **Fail-Closed Verification Contract**: If an underlying checker, model, or database fails or times out, the clinical report is never assumed safe. It is immediately routed to `flagged` with reason `verification_error`.
- **Zero-Tolerance Routing Policy**: In clinical medicine, partial support or unaddressed major physiological anomalies represent latent hazards. Reports are marked `verified` only if all claims are completely supported and zero critical or major findings exist.
- **Strict Immutability of Verification Telemetry**: The `VerificationEnvelope` uses `frozen=True` so that downstream microservices, doctor review workflows, and patient stores cannot modify the verdict or reasons post-verification.
- **Colang Input Rail Protection**: Prompt injections, jailbreaks, and off-topic requests (e.g. finance, poetry, hacking) are filtered at the input layer before entering reasoning pipelines.

---

## 3. Current State
- **Phase 0 (Foundations, Governance & Evaluation Harness)**: **100% COMPLETE & CERTIFIED** (`phase-0-pass`).
- **Phase 1 (Synthetic Patients & Case Builder)**: **100% COMPLETE & CERTIFIED** (`phase-1-pass`).
- **Phase 2 (Multi-Source RAG)**: **100% COMPLETE & CERTIFIED** (`phase-2-pass`).
- **Phase 3 (Grounded Clinical Generation - MedGemma)**: **100% COMPLETE & CERTIFIED** (`phase-3-pass`).
- **Phase 4 (Verification Layer)**: **Steps 25, 26, and 27 COMPLETE**.
- **Active Step**: **Step 28 (P4.4 DeepEval Metrics in CI)**.
- **Test Suite**: 216 of 216 tests passing across `tests/` and `backend/tests/`.
- **Secret Scanner**: Clean pass (0 secrets).
- **Backend Service**: Running on `http://127.0.0.1:8000`.
- **Frontend Service**: Running on `http://localhost:5173`.
- **Latest Commit**: `6059c16`.

---

## 4. Concrete Next Steps
1. Execute **STEP 28: P4.4 DeepEval metrics in CI** (`plan/prompts/phase-4-verification/STEP-28_P4.4_deepeval-ci.md`):
   - Configure offline CI evaluation metrics using DeepEval: faithfulness and contextual relevancy.
   - Wire threshold assertions to `verification.faithfulness_min` (0.90) and `verification.contextual_relevancy_min` (0.80) from `configs/thresholds.yaml`.
   - Build CI harness script executing metrics across golden set evaluation samples.
   - Author acceptance tests red-first in `tests/test_step_28_acceptance.py`.
   - Run full regression suite and secret scanner.
   - Author `docs/steps/STEP-28.md`, mark Step 28 complete in `plan/README.md`, and commit to Git.
