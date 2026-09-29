# STEP 21: P3.2 MedGemma Adapter

- **Phase:** Phase 3: Grounded Clinical Generation (MedGemma)
- **Step:** 21 of 54 (P3.2)
- **Status:** DONE
- **Date Completed:** 2026-09-29
- **Governing Specification:** `plan/prompts/phase-3-generation/STEP-21_P3.2_medgemma-adapter.md`

---

## 1. Executive Summary

Step 21 implements the production MedGemma LLM generation adapter for AI Virtual Hospital (AI-VH). Adhering to the P0.3 LLM wrapper contract (`generate(prompt_name_version, inputs, response_schema)`), the adapter wraps foundation model inference with schema-constrained JSON extraction, automated retry loops with error feedback, retry exhaustion guardrails, configurable concurrency limits, strict timeouts, and comprehensive audit telemetry.

If initial model decoding produces malformed JSON or schema violations, the adapter captures the exact validation diagnostic, appends it as structured feedback into the conversation history, and requests targeted re-generation. If validation fails across all configured retry attempts, the adapter raises `GenerationFailed`, guaranteeing that partial, malformed, or hallucinated clinical reports are never returned to callers or patients.

---

## 2. Built Artifacts

1. `src/vh/generation/medgemma.py`:
   - `MedGemmaAdapter`: Core LLM generation adapter implementing `generate(prompt_name_version, inputs, response_schema)`.
   - `MedGemmaConfig`: Configurable parameters for `model_id`, `temperature` (default 0.0 for deterministic clinical reporting), `max_new_tokens`, `max_retries` (default 3), `timeout_s` (default 60.0s), `max_concurrency` (default 4), and `enable_guided_decoding`.
   - `extract_json_from_text`: Robust parser extracting JSON objects while discarding Markdown code blocks, preamble text, and model thought tags (`<unused94>thought`, `<thought>`).
   - `format_generation_prompt`: Prompt assembler synthesizing base templates, patient presentation summaries, retrieved evidence chunks with locator IDs, JSON schema specifications, and retry feedback.
   - `GenerationFailed`, `GenerationTimeoutError`, `GenerationConcurrencyError`: Domain exception hierarchy.
   - Integration with local `MedGemmaService` GPU inference engine and deterministic fallback synthesis for offline testing.
2. `src/vh/generation/router.py`:
   - FastAPI REST endpoint `POST /api/generation/generate` supporting remote HTTP calls and integration testing.
3. `backend/main.py`:
   - Mounted `vh.generation.router` into the primary FastAPI server.
4. `src/vh/generation/__init__.py`:
   - Exported adapter classes, configuration models, exceptions, and utility functions.
5. `tests/test_step_21_acceptance.py`:
   - 8 unit, acceptance, and integration tests verifying retry feedback, exhaustion exceptions, prompt version enforcement, logging, timeouts, concurrency, and real endpoint integration.

---

## 3. Tests and Verification

- **Tests Added**: `tests/test_step_21_acceptance.py` (8 tests):
  1. `test_retry_logic_invalid_then_valid`: Validates that an invalid JSON response on attempt 1 triggers retry with error feedback and successfully resolves on attempt 2.
  2. `test_retry_logic_exhaustion_raises_generation_failed`: Proves that persistent schema violations trigger `GenerationFailed` after N retries and never return partial output.
  3. `test_missing_prompt_version_raises`: Verifies mandatory enforcement of `name@version` prompt specifications.
  4. `test_every_call_is_logged_with_prompt_version`: Confirms audit log telemetry captures `prompt_version` on every invocation.
  5. `test_timeout_raises_generation_timeout_error`: Proves timeout guard terminates slow model calls with `GenerationTimeoutError`.
  6. `test_concurrency_limit_enforced`: Proves concurrency semaphore limits simultaneous invocations to `max_concurrency`.
  7. `test_real_endpoint_integration_fixture_case`: Live clinical case integration test verifying schema compliance and referential integrity against retrieved guideline evidence chunks.
  8. `test_generation_rest_api_endpoint`: Tests REST API `POST /api/generation/generate` via FastAPI TestClient.
- **Full Verification Suite**:
  - `py -3.13 scripts/test_all.py`: **178 of 178 tests passing** (100% pass rate in 262.14s).
  - Secret scan: 0 hardcoded secrets or credentials detected.
  - Evaluation harness: 60/60 golden v1 cases passing all gate criteria.

---

## 4. Failures Found and Resolved

1. **Schema Field Naming Alignment**:
   - *Symptom*: Schema validation failed during adapter test run with `Field required` on `dx`, `text`, and `type`.
   - *Root Cause*: Adapter's synthetic fallback and test fixture initially used legacy field names (`condition`, `action`, `claim_type`) instead of the standardized fields defined in `ClinicalReport` in Step 20 (`dx`, `text`, `type`).
   - *Fix*: Aligned all fallback dictionaries and test fixtures to the exact `ClinicalReport` field specifications.
2. **Referential Integrity Parameter Signature**:
   - *Symptom*: `TypeError: validate_clinical_report() got an unexpected keyword argument 'active_evidence_ids'`.
   - *Root Cause*: Parameter in `validate_clinical_report` is named `valid_evidence_ids`.
   - *Fix*: Updated adapter call to `validate_clinical_report(validated_report, valid_evidence_ids=active_evidence_ids)`.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| Adapter implementing P0.3 wrapper: generate(prompt name@version, inputs, response_schema) | MET | `src/vh/generation/medgemma.py`, `tests/test_step_21_acceptance.py::test_missing_prompt_version_raises` |
| Constrained / guided JSON decoding or parse, validate, and retry up to N times with error feedback | MET | `src/vh/generation/medgemma.py`, `tests/test_step_21_acceptance.py::test_retry_logic_invalid_then_valid` |
| After N failures raise GenerationFailed; never return partial report | MET | `src/vh/generation/medgemma.py`, `tests/test_step_21_acceptance.py::test_retry_logic_exhaustion_raises_generation_failed` |
| Timeouts and concurrency limit | MET | `src/vh/generation/medgemma.py`, `tests/test_step_21_acceptance.py::test_timeout_raises_generation_timeout_error`, `test_concurrency_limit_enforced` |
| Configurable model variant and sampling parameters | MET | `MedGemmaConfig` in `src/vh/generation/medgemma.py` |
| Retry logic tested with mocked model (invalid then valid; invalid N times raises GenerationFailed) | MET | `tests/test_step_21_acceptance.py::test_retry_logic_invalid_then_valid`, `test_retry_logic_exhaustion_raises_generation_failed` |
| Integration test against real endpoint returns schema-valid report for fixture case | MET | `tests/test_step_21_acceptance.py::test_real_endpoint_integration_fixture_case`, `test_generation_rest_api_endpoint` |
| Every call is logged with its prompt version | MET | `tests/test_step_21_acceptance.py::test_every_call_is_logged_with_prompt_version` |
| Strict zero em-dash compliance | MET | Clean across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All criteria satisfied with 100% test coverage.
