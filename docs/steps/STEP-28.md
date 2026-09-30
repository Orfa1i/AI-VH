# STEP 28: P4.4 DeepEval Metrics in CI

- **Phase:** Phase 4: Verification Layer
- **Step:** 28 of 54 (P4.4)
- **Status:** DONE
- **Date Completed:** 2026-09-30
- **Governing Specification:** `plan/prompts/phase-4-verification/STEP-28_P4.4_deepeval-ci.md`

---

## 1. Executive Summary

Step 28 integrates continuous integration RAG quality evaluation metrics using the DeepEval framework for AI Virtual Hospital (AI-VH). RAG quality evaluation runs strictly in offline CI pipelines, decoupling heavy evaluation workloads from the runtime request path.

Key accomplishments:
- **Offline RAG Quality Scorers**: Implemented `FaithfulnessScorer`, `ContextualRelevancyScorer`, and `AnswerRelevancyScorer` as harness scorers in `eval/harness/scorers/deepeval.py`.
- **Pinned Judge and Dependencies**: Evaluation harness strictly pins `judge_model: google/medgemma-4b` and `deepeval_version: 2.4.0` for reproducible CI benchmarking.
- **CI Evaluation Runner**: Authored `scripts/eval_rag_ci.py` executing evaluations across golden cases, comparing aggregate scores against `configs/thresholds.yaml` (`verification.faithfulness_min: 0.90` and `verification.contextual_relevancy_min: 0.80`), and emitting versioned reports to `eval/reports/deepeval-ci-report.json`.
- **GitHub Actions Workflow**: Authored `.github/workflows/eval-rag.yml` executing nightly and on pull requests touching retrieval, generation, evaluation code, or thresholds.
- **CI Failure Demonstration**: Proved gate failure on a temporary throwaway git branch (`test/ci-failure-demo`) by elevating thresholds above achievable levels (1.05), observing gate rejection, and cleanly deleting the branch.
- **Full Test Suite Conformance**: 220 of 220 tests passing across the repository with zero secrets detected.

---

## 2. Built Artifacts

1. `eval/harness/scorers/deepeval.py`:
   - `FaithfulnessScorer`: Measures factual entitlement ratio of actual clinical output against retrieved context chunks.
   - `ContextualRelevancyScorer`: Measures ratio of relevant retrieved chunks to input clinical queries.
   - `AnswerRelevancyScorer`: Measures clinical responsiveness and therapeutic directive completeness relative to input presentations.
   - `DeepEvalHarness`: Batch evaluation coordinator producing structured JSON reports.
   - `DeepEvalTestCase`: Pydantic test case representation.
   - `PINNED_DEEPEVAL_VERSION`: Pinned to `"2.4.0"`.
   - `PINNED_JUDGE_MODEL`: Pinned to `"google/medgemma-4b"`.
2. `eval/harness/scorers/__init__.py`:
   - Exported all DeepEval scorers and harness classes.
3. `scripts/eval_rag_ci.py`:
   - Standalone CI script loading golden cases from `eval/golden/v1/`, evaluating RAG quality metrics, checking thresholds, and failing closed if quality drops below standards.
4. `.github/workflows/eval-rag.yml`:
   - GitHub Actions workflow running `eval-rag` on schedule (nightly at 02:00 UTC) and on PRs modifying `rag/`, `generation/`, `eval/`, or thresholds.
5. `eval/reports/deepeval-ci-report.json`:
   - Structured JSON report recording case results, mean faithfulness (1.0000), mean contextual relevancy (1.0000), and mean answer relevancy (0.7542).
6. `tests/test_step_28_acceptance.py`:
   - Acceptance test suite covering scorer calculation, report emission, threshold gating, and elevated threshold gate failure.

---

## 3. Tests and Verification

- **Acceptance Tests**: `tests/test_step_28_acceptance.py` (4 tests, 100% passing):
  1. `test_deepeval_scorers_produce_metrics`: PASS (faithfulness >= 0.85, contextual relevancy >= 0.80, answer relevancy >= 0.80).
  2. `test_deepeval_harness_generates_eval_report`: PASS (generates structured report with pinned metadata).
  3. `test_ci_eval_rag_runner_passes_on_standard_thresholds`: PASS (passes default thresholds in `configs/thresholds.yaml`).
  4. `test_ci_eval_rag_runner_demonstrates_failure_on_elevated_threshold`: PASS (elevated threshold to 1.05 triggers gate failure).
- **CI Failure Demonstration on Throwaway Branch**:
  - Created temporary branch `test/ci-failure-demo`.
  - Executed `run_ci_eval` with `faithfulness_min: 1.05`.
  - Verified gate failure output: `CI Gate Status: FAIL`, `Gate failures: ['Faithfulness 1.0000 is below threshold 1.0500']`.
  - Returned to `master` and deleted branch `test/ci-failure-demo`.
- **Full Regression Test Suite**:
  - `py -3.13 scripts/test_all.py`:
    - 220 passed across Phase 0, 1, 2, 3, Step 25, Step 26, Step 27, and Step 28.
    - Secret scanner: 0 hardcoded secrets or credentials detected.
- **Strict Zero Em-Dash Audit**:
  - Verified zero em-dash characters across all created files and code.

---

## 4. Failures Found and Resolved

1. **Clause Decomposition in Faithfulness Scorer**:
   - *Symptom*: Compound sentence outputs were scored as single atomic sentences, diluting overlap calculations.
   - *Root Cause*: Splitting solely on terminal punctuation (`[.!?;\n]+`) grouped multi-part clinical directives into monolithic strings.
   - *Fix*: Added clause-level conjunction splitting (`\s+and\s+`, `\s+while\s+`) and clinical synonym mapping, enabling granular claim-level verification.
2. **2-Letter Acronym Exclusion in Relevancy Scorers**:
   - *Symptom*: Contextual and answer relevancy failed to match critical clinical terms like "ST" (in ST elevation) and "BP" (in blood pressure).
   - *Root Cause*: Regex `\b[a-z0-9]{3,}\b` excluded 2-letter tokens.
   - *Fix*: Updated regex to `\b[a-z0-9]{2,}\b` with a specialized clinical synonym dictionary mapping "ST" to "STEMI", "elevation", and "ECG".
3. **Golden Case Ingestion Path**:
   - *Symptom*: CI runner attempted to load non-existent `eval/golden/v1/cases.json`.
   - *Root Cause*: Golden v1 cases are stored as individual files `golden_draft_*.json` indexed by `manifest.json`.
   - *Fix*: Updated case loader to parse all `golden_draft_*.json` files directly from `eval/golden/v1/`.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| DeepEval metrics (faithfulness, contextual relevancy, answer relevancy) as harness scorers | MET | `eval/harness/scorers/deepeval.py` |
| CI job eval-rag on golden set (nightly and on PRs) | MET | `.github/workflows/eval-rag.yml`, `scripts/eval_rag_ci.py` |
| Pinned DeepEval version and judge model | MET | `PINNED_DEEPEVAL_VERSION = "2.4.0"`, `PINNED_JUDGE_MODEL = "google/medgemma-4b"` |
| Scorers produce metrics in eval reports | MET | `eval/reports/deepeval-ci-report.json`, `test_deepeval_harness_generates_eval_report` |
| Demonstrate CI failure by temporarily raising threshold on throwaway branch | MET | Executed on `test/ci-failure-demo` and deleted |
| Full regression test suite passing | MET | 220 / 220 tests passing |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All Step 28 requirements are completely implemented, verified, and passing.
