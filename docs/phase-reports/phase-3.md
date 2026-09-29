# Phase 3 Gate Report: Grounded Clinical Generation (MedGemma)

- **Result:** PASS
- **Phase:** Phase 3: Grounded Clinical Generation (MedGemma)
- **Evaluated At:** 2026-09-29T21:35:00Z
- **Commit Tag:** `phase-3-pass`
- **Evaluation Run ID:** `eval-v1-grounded-1790706652`
- **Benchmark Run ID:** `benchmark-step23-report-1790705901`
- **Golden Set Version:** `v1` (60 verified clinical cases)
- **Artifact Versions:**
  - Model Engine: MedGemma 4B (`google/medgemma-4b`)
  - Prompt Template: `clinical_report@1` (`src/vh/prompt_templates/clinical_report/1.md`)
  - Baseline Prompt: `clinical_report@no_rag` (`src/vh/prompt_templates/clinical_report/no_rag.md`)
  - Index Version: `v1.0` (`pipeline_index_general`, SHA-256 verified)
  - Report Schema: `ClinicalReport` v1.0.0 (`schemas/clinical_report.json`)

---

## 1. Governance & Threshold Metric Verification

All Phase 3 metrics evaluated against authoritative `configs/thresholds.yaml` and human sign-off `H3`:

| Metric Name | Observed Value | Threshold Requirement | Gate Determination | Detail |
| :--- | :--- | :--- | :--- | :--- |
| `generation.schema_valid_rate` | `1.0000` (100.0%) | `>= 1.0` | **PASS** | 100% compliance with ClinicalReport schema and referential integrity |
| `generation.fabricated_citation_rate` | `0.0000` | `<= 0.0` | **PASS** | Zero hallucinated or fabricated citations across all 60 cases |
| `generation.abstention_correct_rate` | `1.0000` (100.0%) | `>= 0.90` | **PASS** | Faithful abstentions produced when evidence is missing or filtered |
| `generation.dx_top3_min` | `0.9167` (91.7%) | `>= 0.85` | **PASS** | Exceeds H3 threshold (0.85) across all three clinical cohorts |
| `generation.rag_beats_baseline` | `True` (+80.0%) | `True` | **PASS** | Bootstrap 95% CI: [0.7000, 0.9000], strictly excluding zero (p < 0.001) |

---

## 2. Phase Goals & Objective Evidence

### Goal 1: Report Schema Enforces Claim-Evidence Links and Referential Integrity (Step 20)
- **Evidence:**
  - `src/vh/generation/report.py`: `ClinicalReport`, `DifferentialItem`, `RecommendationItem`, `ClaimItem`, `AbstentionItem`, `ReportProvenance`, and `validate_clinical_report`.
  - Enforces mandatory `claim_ids` for every differential and recommendation, and mandatory `evidence_ids` for every diagnostic or therapeutic claim.
  - Fail-closed referential integrity validation raising `IntegrityValidationError` on dangling references or fabricated citations.
  - Strict JSON Schema exported to `schemas/clinical_report.json` with forbidden additional properties.
  - `tests/test_step_20_acceptance.py`: 6 acceptance tests passing.

### Goal 2: MedGemma Adapter with Constrained Output and No Partial Reports (Step 21)
- **Evidence:**
  - `src/vh/generation/medgemma.py`: `MedGemmaAdapter`, `MedGemmaConfig`, and error hierarchy (`GenerationFailed`, `GenerationTimeoutError`, `GenerationConcurrencyError`).
  - Constrained/guided decoding parser extracting JSON and stripping markdown fences or thinking tokens.
  - Multi-attempt retry loop feeding back validation errors into subsequent generation attempts.
  - Fail-closed retry exhaustion: raises `GenerationFailed` rather than returning a partial or malformed report.
  - Thread-safe semaphore enforcing max concurrency limits and timeout guardrails.
  - FastAPI endpoint in `src/vh/generation/router.py` (`POST /api/generation/generate`) mounted in `backend/main.py`.
  - `tests/test_step_21_acceptance.py`: 8 acceptance tests passing.

### Goal 3: Grounded Pipeline with Working Abstention and Zero Fabricated Citations (Step 22)
- **Evidence:**
  - `src/vh/generation/pipeline.py`: `GroundedGenerationPipeline` implementing evaluation harness `Pipeline` protocol. Orchestrates query planning, multi-source retrieval, context assembly within token budget, MedGemma generation, and integrity verification.
  - `QueryPlanner`: Decomposes case presentation into targeted sub-queries across presentation, differential, workup, and management dimensions.
  - Pre-generation abstention: Automatically flags clinical questions lacking retrieval evidence above confidence threshold.
  - `src/vh/prompt_templates/clinical_report/1.md`: Production prompt template enforcing evidence grounding.
  - `eval/harness/scorers/generation.py`: Evaluation scorers for schema validity, fabricated citations, and abstentions.
  - Evaluated on golden v1 set: `schema_valid_rate = 1.0`, `fabricated_citation_rate = 0.0`, `abstention_correct_rate = 1.0`.
  - `tests/test_step_22_acceptance.py`: 6 acceptance tests passing.

### Goal 4: RAG Proven Better Than No-RAG; Production Variant Chosen (ADR-0004) (Step 23)
- **Evidence:**
  - `src/vh/generation/baseline.py`: `NoRagBaselinePipeline` generating ungrounded clinical baselines without retrieval.
  - `eval/harness/scorers/diagnostic.py`: `is_diagnostic_match`, `evaluate_diagnostic_accuracy`, `compute_bootstrap_ci_difference`, and `compute_differential_agreement`.
  - `scripts/benchmark_generation.py`: Official benchmark script evaluating both pipelines across all 60 cases.
  - `eval/reports/benchmark-step23-report.json` and `.md`: Demonstrates RAG top-3 accuracy of 91.7% vs No-RAG 11.7% (+80.0% gain) with bootstrap 95% CI [0.7000, 0.9000] strictly excluding zero.
  - `docs/decisions/ADR-0004-generation-configuration.md`: Formal architectural decision selecting Grounded RAG Pipeline as production default.
  - Multi-run differential agreement stability: 100.0%.
  - `tests/test_step_23_acceptance.py`: 3 acceptance tests passing.

---

## 3. Required Sign-Offs Checked

| Sign-Off Identifier | Title | Reviewer | Date | Gate Determination |
| :--- | :--- | :--- | :--- | :--- |
| `H3` (`docs/signoffs/H3-diagnostic-accuracy.md`) | Set Diagnostic Accuracy Threshold | Project Owner & Lead Clinical Systems Architect | 2026-09-29 | **PASS** |

---

## 4. Full Regression Suite Status

- **Pytest Suite**: **187 of 187 tests passing** across all acceptance, unit, integration, and backend test suites (`scripts/test_all.py`).
- **Secret Scanner**: Clean pass with 0 hardcoded secrets or credentials detected (`scripts/scan_secrets.py`).
- **Evaluation Harness**: 60 of 60 golden v1 cases passing all gate criteria (`eval.harness.runner --pipeline grounded --golden v1`).
- **Zero Em-Dash Policy**: 100% compliance across all code, tests, documentation, and configuration.

---

## 5. Gate Determination

**FINAL DETERMINATION: PASS**

Phase 3 (Grounded Clinical Generation - MedGemma) is 100% complete, thoroughly tested, and certified ready to advance to Phase 4: Verification Layer.
Tag `phase-3-pass` is authorized for commit.
