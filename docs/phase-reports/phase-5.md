# Phase Gate Report: Phase 5 — Agents & Orchestration (headless)

- **Result:** PASS
- **Gate step:** STEP 35 (P5.G)
- **Date:** 2026-09-30
- **Code evaluated:** `7be2bf2` (includes Steps 31-34 + H5 threshold + FIX-LOOP test update)
- **Golden set:** v1 (manifest 2026-09-28, 60 files, 60 verified cases)
- **Artifact versions:** agent prompt templates doctor/nurse/lab/radiology/pharmacy
  @1.0.0 (`src/vh/prompt_templates/`); orchestrator config 1.0.0
  (`configs/agents/orchestrator.yaml`); permissions matrix
  (`configs/agents/permissions.yaml`); MedGemmaAdapter `google/medgemma-4b`
  (deterministic heuristic synthesis in CI/test environments)

---

## 1. Preconditions

- `docs/steps/STEP-31.md`, `STEP-32.md`, `STEP-33.md`, `STEP-34.md` all exist
  with Status: DONE. Verified 2026-09-30.
- Required sign-offs: none for this gate.
- Human checkpoint H5 completed by project owner: `agents.encounter_score_min`
  set to `0.30` in `configs/thresholds.yaml` (verified on disk).

## 2. Verification runs

- Full regression (`py -3.13 scripts/test_all.py test-all`): **260 of 260 tests
  passed (100% green)**; secret scanner clean (0 findings). Ruff/mypy skipped
  by the runner (modules not installed locally; pre-existing environment
  condition, identical to prior green runs).
- Eval (`eval.harness.runner --golden v1 --pipeline dummy`, default config):
  outcome PASS, 60/60 cases; schema_valid_rate 1.0, min_verified_cases 60,
  recall_at_10 0.90, mrr_min 0.80, critical_fault_detection 1.0,
  faithfulness_min 0.95, contextual_relevancy_min 0.85, traceability_rate 1.0
  (run `eval-v1-dummy-1790760765`).

## 3. Metrics vs thresholds (`configs/thresholds.yaml`, agents section)

| Metric | Threshold | Measured | Comparison | Status |
| :--- | :--- | :--- | :--- | :--- |
| `agents.permission_violations` | 0 | 0 (tool-layer gating enforced; Step 32 suite 8/8; zero violations across all encounter runs) | <= | PASS |
| `agents.runaway_loops` | 0 | 0 (every encounter ends in an explicit terminal state; Step 33 budgets/loop tests 10/10; 60/60 golden encounters completed) | <= | PASS |
| `agents.replay_mismatch_count` | 0 | 0 (60/60 replays byte-identical on canonical event-log hash, seed 42) | <= | PASS |
| `agents.encounter_score_min` | 0.30 (H5, owner-set) | 0.3596 (mean over 60 verified cases; min 0.1644, max 0.9944) | >= | PASS |

`_min` thresholds compare the aggregate mean against the minimum, consistent
with `dx_top3_min` / `mrr_min` / `faithfulness_min` usage elsewhere in this repo.

## 4. Phase goals: evidence

| Phase goal | Evidence |
| :--- | :--- |
| Environment releases hidden data only via orders; never invents data | `src/vh/agents/environment.py` (clock-gated release; unknown orders return `result_unavailable`); `src/vh/agents/events.py` (append-only store); `tests/test_step_31_acceptance.py` (7 tests incl. isolation/leakage) |
| Five specialised agents with tool-layer permissions | `src/vh/agents/roles/` (Doctor/Nurse/Lab/Radiology/Pharmacy + `BaseAgent` permission gating), `configs/agents/permissions.yaml`, versioned prompts @1.0.0; `tests/test_step_32_acceptance.py` (8 tests) |
| Orchestrator with budgets, loop detection, explicit termination states | `src/vh/agents/orchestrator.py`, `configs/agents/orchestrator.yaml` v1.0.0; `tests/test_step_33_acceptance.py` (10 tests incl. FIX-LOOP natural-order regression) |
| Encounter scoring and exact replay | `src/vh/agents/scoring.py`, `src/vh/agents/replay.py`, `vh replay` CLI, `eval/harness/encounter.py`; `tests/test_step_34_acceptance.py` (9 tests); `docs/decisions/ADR-0006-encounter-scoring-replay.md` |

## 5. Sign-offs checked

None required for this gate. (No physician sign-off exists in Phase 5 by design;
physician checkpoints sit at H4, H6, H7.)

## 6. Fix loop 1 (during gate execution)

- **Failure:** `tests/test_step_02_acceptance.py::test_thresholds_loader_null_reported_as_not_set`
  (`assert True is False`): the test hard-coded the Step 02 provisional
  assumption that `agents.encounter_score_min` is null.
- **Root cause (one sentence):** the sanctioned H5 owner edit (null -> 0.30)
  invalidated the test's stale provisional-null assumption.
- **Fix:** kept null-behavior coverage via the still-null `generation.dx_top3_min`
  and added `test_thresholds_loader_set_values_pass_gates` verifying SET status,
  the 0.30 value, and gate evaluation in both directions; corrected a stale
  comment in `src/vh/agents/scoring.py`. No thresholds, golden sets, or clinical
  logic touched. No existing test skipped, weakened, or deleted.
- **Re-run:** targeted file 11/11 green; full suite **260/260 green**; eval PASS.
- **Observation (not a defect, no reopen):** `generation.dx_top3_min` is still
  null despite H3 being ticked in `plan/README.md`; flagged for the owner to
  reconcile, since a future strict gate on that key would fail. Phase 3 remains
  certified (`phase-3-pass`) and is not reopened by this gate.

## 7. Decision

**PASS.** Phase 5 is complete. Commit tagged `phase-5-pass`. Next: STEP 36 (P6.1).
