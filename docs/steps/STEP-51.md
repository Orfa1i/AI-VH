# Step Report: STEP-51 (P9.1 Imaging Models as Radiology Agent Tools)

- **Phase:** Phase 9: Advanced Intelligence
- **Step:** STEP 51 of 54 (P9.1)
- **Status:** DONE
- **Timestamp:** 2026-09-30T21:00:00Z
- **Tag:** `step-51-pass`

---

## 1. Built: Files Created or Changed

1. `src/vh/agents/tools/__init__.py` (new): `ImagingToolOutput` typed contract
   (output id, tool, version, finding, location, grade, confidence,
   `interpretation: "model-output"`).
2. `src/vh/agents/tools/imaging.py` (new): seeded phantom generators +
   deterministic `FractureLocalizationTool` (dark-region bbox measurement) and
   `KneeOAGradingTool` (median joint-gap measurement vs calibrated edges).
3. `src/vh/generation/report.py` (extended): `IMAGING_*` keyword sets and
   `find_uncited_imaging_claims` (P3.1 validator extension).
4. `src/vh/verification/rules/imaging.py` (new) + engine registration +
   package exports: `RULE-IMAGING-CITE-001` (major, fail-closed).
5. `src/vh/agents/roles/radiology.py`: P5.2 stub replaced with tool dispatch
   (`fracture` / `knee-oa` / `auto` by study code; `ValueError` on unknown
   tool or missing pixels); permission matrix already gated the tool.
6. `tests/test_step_51_acceptance.py` (new): 8 acceptance tests.
7. `tests/test_step_32_acceptance.py`: stub assertion replaced with
   equal-or-stronger tool behavior checks per the plan directive.
8. `docs/decisions/ADR-0014-imaging-reference-tools.md` (new).

---

## 2. Tests Added and Full Regression Results

### New Tests (8):
- Fracture center error ≤ 4 px (max) / ≤ 2.5 px (mean) over 10 seeds.
- Negatives report `no_fracture` (no false positives).
- KOA grades exact over severities 0–4 × 3 seeds.
- Typed schema incl. version + model-output labeling.
- Uncited imaging claim flagged; cited claim passes (with distractor).
- Agent dispatch incl. unknown-tool and missing-image rejections.
- Engine-level imaging rule fires once on an uncited imaging claim.

### Test Suite Execution:
- `tests/test_step_51_acceptance.py` + Step-32 file: 16 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **335 of 335
  tests passed (100% green)** in 486.98s (327 pre-existing + 8 new Step 51).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

None on implementation (16/16 first green run after test-first failures).
The engine extension produced zero new findings on all pre-existing fixtures
(confirmed by the full suite), as designed — it fires only on imaging language.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Typed tool outputs (finding, location, grade/probability, version) | `tools/__init__.py`; schema test | PASS |
| Baselines reproduced within tolerance | Phantom sweeps with locked tolerances | PASS |
| Outputs labeled model output, never ground truth | `interpretation` field; label tests | PASS |
| Imaging claims cite tool-output ids (P3.1 + P4.1) | `report.py` checker + `rules/imaging.py`; flag tests | PASS |
| Stubs replaced | `radiology.py`; dispatch tests | PASS |
| Full regression green | Below | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- No trained weights and no image dataset exist in-repo; nothing was fetched
  (synthetic-only + no-network rules). Real-model integration (licensed
  dataset, weights, revalidation of these baselines) is future work owned by
  the project owner. No other open questions.

## 6. Mini-gate (STEP 51 §8)

| Acceptance criterion | Result |
| :--- | :--- |
| Baselines reproduced within tolerance | PASS (fracture ≤ 4 px max; KOA exact) |
| Imaging claims without tool-output citation flagged | PASS (unit + engine level) |
| Full regression suite of all phases passes | PASS (see below) |
| **Mini-gate** | **PASS** |
