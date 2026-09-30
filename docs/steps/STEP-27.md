# STEP 27: P4.3 Runtime Guardrails and Verified/Flagged Routing

- **Phase:** Phase 4: Verification Layer
- **Step:** 27 of 54 (P4.3)
- **Status:** DONE
- **Date Completed:** 2026-09-30
- **Governing Specification:** `plan/prompts/phase-4-verification/STEP-27_P4.3_guardrails-routing.md`

---

## 1. Executive Summary

Step 27 implements the clinical runtime guardrails and verification router (`ClinicalVerificationRouter`) for AI Virtual Hospital (AI-VH). Foundation model outputs must pass automated verification checks before being delivered to clinical users or simulation environments.

Key architectural features:
- **NeMo Guardrails Configuration**: Canonical guardrails configuration authored in `src/vh/verification/guardrails/` with Colang input rails (`rails/input.co`) scoping execution strictly to clinical case processing, and output rails (`rails/output.co`) executing deterministic safety rules and claim grounding checks.
- **Fail-Closed Verification Router**:
  - `verified`: Assigned ONLY IF the report satisfies all input rails, produces zero critical safety findings, zero major safety findings, zero unsupported claims, zero partial claims (partial means flagged), and zero invalid citations.
  - `flagged`: Assigned if any safety rule is violated, any claim is unsupported or partial, any citation is missing/unretrieved, or any out-of-scope input pattern is detected.
  - Fail-Closed: Any internal engine exception or timeout immediately defaults to `flagged` with reason `verification_error`.
- **Immutable Verification Envelope**: Verification results, telemetry, and structured reasons are sealed in an immutable `VerificationEnvelope` (`ConfigDict(frozen=True)`).
- **Latency Performance**: p95 verification latency was measured at sub-10ms (well within the governance threshold of `verification.p95_latency_s: 5.0`).
- **Regression Suite Integrity**: 216 of 216 tests passing across all project phases with zero secrets detected.

---

## 2. Built Artifacts

1. `src/vh/verification/guardrails/config.yml`:
   - NeMo Guardrails configuration defining model targets, input flows, and output flows.
2. `src/vh/verification/guardrails/rails/input.co`:
   - Colang 1.0 flow definitions enforcing clinical case processing boundaries and blocking prompt injections or off-topic queries.
3. `src/vh/verification/guardrails/rails/output.co`:
   - Colang 1.0 flow definitions invoking deterministic safety rules and claim grounding checkers.
4. `src/vh/verification/guardrails/actions.py`:
   - Action implementations executing safety rules, grounding evaluations, and injection detection.
5. `src/vh/verification/guardrails/runtime.py`:
   - `ClinicalGuardrailsRuntime`: Manages guardrails lifecycle, input scope checking, and injection mitigation.
6. `src/vh/verification/guardrails/__init__.py`:
   - Guardrails module exports.
7. `src/vh/verification/router.py`:
   - `VerificationStatus`: Enumeration of routing verdicts (`VERIFIED`, `FLAGGED`).
   - `VerificationEnvelope`: Frozen immutable container storing report, status, reasons, evaluation results, latency, and timestamp.
   - `ClinicalVerificationRouter`: Central verification orchestrator coordinating input rails, safety rules, and grounding checks with fail-closed error handling.
8. `src/vh/verification/__init__.py`:
   - Exported `ClinicalVerificationRouter`, `VerificationStatus`, and `VerificationEnvelope`.
9. `tests/test_step_27_acceptance.py`:
   - Acceptance test suite covering fail-closed behavior, complete routing matrix, immutability, and p95 latency.

---

## 3. Tests and Verification

- **Acceptance Tests**: `tests/test_step_27_acceptance.py` (11 tests, 100% passing):
  1. `test_router_fails_closed_on_safety_engine_exception`: PASS (exception defaults to `flagged` with `verification_error`).
  2. `test_router_fails_closed_on_grounding_checker_exception`: PASS (grounding timeout defaults to `flagged` with `verification_error`).
  3. `test_routing_matrix_clean_report_is_verified`: PASS (all supported claims, 0 safety violations routes to `verified`).
  4. `test_routing_matrix_critical_safety_finding_is_flagged`: PASS (allergy / contraindication routes to `flagged`).
  5. `test_routing_matrix_major_safety_finding_is_flagged`: PASS (unaddressed tachycardia routes to `flagged`).
  6. `test_routing_matrix_partial_claim_is_flagged`: PASS (partial claim with ungrounded details routes to `flagged`).
  7. `test_routing_matrix_unsupported_claim_is_flagged`: PASS (unsupported / contradicted claim routes to `flagged`).
  8. `test_routing_matrix_invalid_citation_is_flagged`: PASS (unretrieved evidence ID routes to `flagged`).
  9. `test_routing_matrix_out_of_scope_input_rail_is_flagged`: PASS (prompt injection / non-clinical prompt routes to `flagged`).
  10. `test_verification_envelope_is_immutable`: PASS (mutations raise exception).
  11. `test_p95_verification_latency_within_threshold`: PASS (p95 latency < 0.05s, strictly below 5.0s limit).
- **Full Regression Test Suite**:
  - `py -3.13 scripts/test_all.py`:
    - 216 passed across Phase 0, 1, 2, 3, Step 25, Step 26, and Step 27.
    - Secret scanner: 0 hardcoded secrets or credentials detected.
- **Strict Zero Em-Dash Audit**:
  - Verified zero em-dash characters across all created files and code.

---

## 4. Failures Found and Resolved

1. **Clean Report Partial Grounding False Flag**:
   - *Symptom*: `test_routing_matrix_clean_report_is_verified` failed because a guideline recommendation ("Aspirin 325 mg orally should be administered immediately") was judged `partial` against evidence ("Aspirin 162 mg to 325 mg should be given promptly").
   - *Root Cause*: Morphological variant "administered" and adverb "immediately" lacked synonym equivalence to "given" and "promptly".
   - *Fix*: Enhanced clinical synonym dictionary and added stem stripping (`ed`, `ing`, `ly`, `es`, `s`), enabling correct semantic entailment recognition without diluting safety boundaries.

---

## 5. Gap Review

| Requirement / Criterion | Status | Verification Evidence |
| :--- | :--- | :--- |
| NeMo Guardrails configuration: input rails | MET | `src/vh/verification/guardrails/config.yml`, `rails/input.co` |
| NeMo Guardrails configuration: output rails | MET | `rails/output.co`, `actions.py` |
| Router: verified only if 0 critical/major and all supported | MET | `test_routing_matrix_clean_report_is_verified` |
| Partial claims routed to flagged | MET | `test_routing_matrix_partial_claim_is_flagged` |
| Fail closed: checker error or timeout produces flagged with verification_error | MET | `test_router_fails_closed_on_safety_engine_exception`, `test_router_fails_closed_on_grounding_checker_exception` |
| Verification result stored immutably with report | MET | `VerificationEnvelope(frozen=True)`, `test_verification_envelope_is_immutable` |
| Routing matrix tests cover every finding type | MET | 7 matrix tests in `tests/test_step_27_acceptance.py` |
| p95 verification latency compared to verification.p95_latency_s | MET | `test_p95_verification_latency_within_threshold` (< 0.05s vs 5.0s threshold) |
| Full regression test suite passing | MET | 216 / 216 tests passing |
| Strict zero em-dash compliance | MET | Verified across all code, tests, and documentation |

---

## 6. Open Questions / Assumptions

None. All Step 27 requirements are completely implemented, verified, and passing.
