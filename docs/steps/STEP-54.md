# Step Report: STEP-54 (P9.4 New Agent / Department Scaffold)

- **Phase:** Phase 9: Advanced Intelligence
- **Step:** STEP 54 of 54 (P9.4) — last step in the plan
- **Status:** DONE
- **Timestamp:** 2026-09-30T23:00:00Z
- **Tag:** `step-54-pass`
- **Note:** STEP 53 remains BLOCKED by design (null `min_preference_pairs`);
  Step 54 is technically independent (scaffold + new agent), so it executes
  now per the owner's continue directive.

---

## 1. Built: Files Created or Changed

1. `src/vh/agents/scaffold.py` (new): `generate_agent_scaffold` emitting agent
   class, versioned prompt, permission snippet, starter tests, docs page.
2. `src/vh/agents/cli.py` (extended): `new-agent` subcommand with
   repository-layout placement.
3. `src/vh/cli.py`: `vh new-agent` routing + help text.
4. `src/vh/agents/roles/icu.py` (new): ICU proof agent (deterministic flags
   and acuity bands); `src/vh/prompt_templates/icu/1.0.0.md` (new).
5. `configs/agents/permissions.yaml`: hand-applied ICU entry (allowed:
   monitor/assess/note; clinical actions forbidden).
6. `src/vh/agents/roles/__init__.py`, `src/vh/agents/__init__.py`: ICU exports.
7. `src/vh/agents/roles/base.py` (FIX-LOOP): repo-root depth fix so the
   permissions config actually loads.
8. `docs/agents/icu.md` (new): agent docs page with checklist.
9. `tests/test_step_54_acceptance.py` (new): 6 acceptance tests.
10. `tests/test_step_32_acceptance.py`: permissions-load regression test.
11. `docs/decisions/ADR-0016-agent-scaffold.md` (new).

---

## 2. Tests Added and Full Regression Results

### New Tests (6):
- Scaffold artifact completeness (class, prompt, permissions, tests, docs).
- Red state: generated stubs raise `NotImplementedError` on real construction.
- ICU proof agent: permission gating (allowed execute, forbidden blocked),
  CaseSpec rejection, deterministic critical acuity on fixture vitals.
- Snippet idempotency (byte-identical re-runs).
- Prompt version convention (`icu@1.0.0`, `1.0.0.md`).
- CLI wiring (`vh new-agent --help` exits 0).

### Test Suite Execution:
- `tests/test_step_54_acceptance.py`: 6 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **349 of 349
  tests passed (100% green)** in 504.18s (342 pre-existing + 6 new Step 54 +
  1 Step-32 FIX-LOOP regression). Ruff/mypy skipped by the runner (modules not
  installed locally; pre-existing environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Permissions config never loaded (Phase-5 FIX-LOOP):** `base.py` repo root
   one level short → empty permission sets for all roles → tool layer gated
   nothing. Fixed depth; regression test added; audited all other REPO_ROOT
   computations (only this one wrong). Phase-5 suites re-run green.
2. **Scaffold/test authoring slips** (`from typing` typo, over-strict snippet
   assertion, missing subprocess env): fixed during development.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Scaffold generates class, prompt, permissions, stubs, tests, docs, checklist | `scaffold.py`; artifact test | PASS |
| Generated tests fail before, pass after | Red-state test + ICU suite (same shapes, implemented) | PASS |
| New agent passes Phase-5 suites | ICU permission/leakage/scoring tests; Phase-5 suites green in full run | PASS |
| Full regression green | Below | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

None. All 54 plan steps are now DONE, PASS-certified, or BLOCKED by design
(Step 41: data; Step 53: threshold value; H6/H7: optional external).

## 6. Mini-gate (STEP 54 §8)

| Acceptance criterion | Result |
| :--- | :--- |
| Generated tests fail before implementation and pass after | PASS |
| The new agent passes the Phase 5 test suites | PASS |
| Full regression suite passes | PASS (see below) |
| **Mini-gate** | **PASS** |
