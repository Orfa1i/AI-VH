# Synthetic Patient Case Validation Report

- **Evaluated At:** 2026-09-29T04:19:21.856465+00:00
- **Total Cases Evaluated:** 500
- **Valid Cases (100% Plausible & Leak-Free):** 500
- **Overall Plausibility Pass Rate:** 100.0%
- **Total Leakage Defects:** 0

## Per-Rule Validation Pass Rates

| Validation Rule | Pass Rate | Status |
| :--- | :--- | :--- |
| Vitals Range | 100.0% | PASS |
| Ucum Units | 100.0% | PASS |
| Diagnostic Consistency | 100.0% | PASS |
| Medication Consistency | 100.0% | PASS |
| Temporal Ordering | 100.0% | PASS |
| Leakage | 100.0% | PASS |

## Governance & Threshold Verification
- `cases.fhir_valid_rate`: 1.0 (PASSED)
- `cases.leakage_count`: 0 (Threshold: 0) -> PASSED
- `cases.plausibility_pass_rate`: 1.0 (Threshold: 1.0) -> PASSED