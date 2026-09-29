# STEP 23: P3.4 Model Benchmark and No-RAG Baseline

- **Phase:** Phase 3: Grounded Clinical Generation (MedGemma)
- **Step:** 23 of 54 (P3.4)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-3-generation/STEP-23_P3.4_model-benchmark.md`

---

## 1. Executive Summary

Step 23 executes the comprehensive empirical benchmarking and validation of the AI Virtual Hospital (AI-VH) clinical generation subsystem. To determine whether evidence-grounded generation delivers demonstrable clinical value over ungrounded reasoning, the Grounded Generation Pipeline (`GroundedGenerationPipeline`) was benchmarked head-to-head against an ungrounded No-RAG baseline (`NoRagBaselinePipeline`) across all 60 physician-verified golden cases in `eval/golden/v1`.

The benchmark proved that the Grounded RAG pipeline decisively outperforms the baseline:
- Top-3 diagnostic accuracy (`dx_top3`): **91.7%** (RAG) vs **11.7%** (No-RAG), representing an absolute diagnostic gain of **+80.0%**.
- Non-parametric paired bootstrap 95% confidence interval for `dx_top3` difference: **[0.7000, 0.9000]**, strictly excluding zero (p < 0.001).
- Fabricated citation rate: **0.0000** for the grounded pipeline, completely satisfying the zero-hallucination requirement.
- Schema validity rate: **100.0%** across both pipelines.
- Multi-run top-3 differential stability agreement: **100.0%**, demonstrating exceptional diagnostic reproducibility.

Architectural decision record `docs/decisions/ADR-0004-generation-configuration.md` was authored, establishing the Grounded RAG Pipeline with MedGemma 4B as the production clinical generation standard. Based on the observed diagnostic performance (0.9167), a baseline threshold of `generation.dx_top3_min: 0.85` is proposed for human sign-off at Checkpoint H3.

---

## 2. Built Artifacts

1. `src/vh/prompt_templates/clinical_report/no_rag.md`:
   - Dedicated ungrounded prompt template enforcing report generation directly from visible presentation without retrieval context or citations.
2. `src/vh/generation/baseline.py`:
   - `NoRagBaselinePipeline`: Baseline pipeline implementing the evaluation harness `Pipeline` protocol without retrieval or citations.
3. `eval/harness/scorers/diagnostic.py`:
   - `is_diagnostic_match`: Evaluates diagnostic concordance against physician-verified ground truth with clinical alias expansions, token overlap, and core disease entity matching.
   - `evaluate_diagnostic_accuracy`: Computes aggregate top-1 and top-3 diagnostic concordance.
   - `compute_bootstrap_ci_difference`: Computes non-parametric paired bootstrap 95% confidence intervals for the accuracy delta.
   - `compute_differential_agreement`: Computes multi-run top-3 differential agreement (Jaccard similarity).
4. `scripts/benchmark_generation.py`:
   - Full benchmark runner executing both pipelines on all 60 golden cases, computing bootstrap CIs, measuring stability, and emitting versioned JSON and Markdown reports.
5. `eval/reports/benchmark-step23-report.json` and `eval/reports/benchmark-step23-report.md`:
   - Official benchmark output artifacts detailing head-to-head metrics, bootstrap CIs, latency, and threshold recommendations.
6. `docs/decisions/ADR-0004-generation-configuration.md`:
   - Architectural decision record formally selecting Grounded RAG Pipeline with MedGemma 4B as the production clinical generation architecture.
7. `tests/test_step_23_acceptance.py`:
   - Acceptance tests verifying No-RAG contract conformance, bootstrap 95% CI excluding zero, and multi-run differential stability.

---

## 3. Tests and Verification

- **Acceptance Tests**: `tests/test_step_23_acceptance.py` (3 tests):
  1. `test_norag_baseline_pipeline_contract`: Verifies that `NoRagBaselinePipeline` implements the `Pipeline` protocol and generates reports without evidence citations.
  2. `test_grounded_rag_beats_norag_baseline_with_bootstrap_ci`: Verifies that `dx_top3(RAG) > dx_top3(No-RAG)` with bootstrap 95% CI lower bound strictly greater than 0.0.
  3. `test_stability_reproducibility_across_runs`: Verifies that multi-run top-3 differential agreement is >= 0.90 (observed: 1.00).
- **Official Benchmark Run**:
  - `py -3.13 scripts/benchmark_generation.py`:
    - Evaluated 60/60 cases.
    - Grounded RAG `dx_top3`: 0.9167 (91.7%).
    - No-RAG Baseline `dx_top3`: 0.1167 (11.7%).
    - Bootstrap 95% CI: `[0.7000, 0.9000]` (excludes zero: True).
    - Fabricated citation rate: 0.0000.
    - Differential stability agreement: 1.0000.
- **Full Regression Test Suite**:
  - `py -3.13 scripts/test_all.py`: All acceptance and unit tests passing.
  - Secret scan: 0 hardcoded secrets or credentials detected.

---

## 4. Failures Found and Resolved

1. **Presentation History Key Name Variation**:
   - *Symptom*: Generation pipelines were not extracting detailed clinical histories from `visible_presentation`.
   - *Root Cause*: Cases in `eval/golden/v1` store clinical history under key `'history'` rather than `'history_of_present_illness'`.
   - *Fix*: Updated `QueryPlanner`, `GroundedGenerationPipeline`, and `NoRagBaselinePipeline` to check `pres.get("history") or pres.get("history_of_present_illness", "")` with similar fallbacks for `exam` and `labs`.
2. **Boundary Condition in Bootstrap CI Equality Assertion**:
   - *Symptom*: `assert ci_high > ci_low` failed with `assert 1.0 > 1.0` on a 15-case sample where RAG was 100% accurate and No-RAG was 0% accurate across all bootstrap resamples.
   - *Root Cause*: When performance difference is invariant at 1.0 across all resamples, the bootstrap distribution is a delta function with `ci_lower == ci_upper == 1.0`.
   - *Fix*: Corrected assertion to `assert ci_high >= ci_low` and `assert ci_low > 0.0`.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| No-RAG baseline pipeline implemented | MET | `src/vh/generation/baseline.py`, `tests/test_step_23_acceptance.py` |
| Benchmark script with bootstrap 95% CI | MET | `scripts/benchmark_generation.py`, `eval/reports/benchmark-step23-report.json` |
| RAG beats baseline with CI excluding zero | MET | `dx_top3` 91.7% vs 11.7%, CI [0.7000, 0.9000] |
| Zero fabricated citations in grounded pipeline | MET | `fabricated_citation_rate = 0.0000` |
| Stability across repeated runs measured | MET | `differential_stability_agreement = 1.0000` |
| ADR-0004 authored selecting generation config | MET | `docs/decisions/ADR-0004-generation-configuration.md` |
| Proposed threshold for H3 documented | MET | Proposed `generation.dx_top3_min: 0.85` |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Governance Handoff for H3

Per project governance rules:
- `configs/thresholds.yaml` is immutable by autonomous agents.
- Based on the observed top-3 diagnostic accuracy of **0.9167 (91.7%)**, we recommend that the project owner set `generation.dx_top3_min: 0.85` in `configs/thresholds.yaml`.
- This proposal is formally documented in `docs/signoffs/H3-diagnostic-accuracy.md` for human sign-off at Checkpoint H3.
