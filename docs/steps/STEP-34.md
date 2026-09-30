# Step Report: STEP-34 (P5.4 Encounter Scoring and Deterministic Replay)

- **Phase:** Phase 5: Agents & Orchestration (headless)
- **Step:** STEP 34 of 54 (P5.4)
- **Status:** DONE
- **Timestamp:** 2026-09-30T12:00:00Z
- **Tag:** `step-34-pass` (to be applied by project owner on acceptance)

---

## 1. Built: Files Created or Changed

1. `src/vh/agents/scoring.py` (new):
   - `EncounterScore`: per-encounter metrics with 0-1 composite `encounter_score`.
   - `EncounterScorer`: diagnostic correctness (top-1/top-3), workup recall/
     precision, red-flags addressed, time to diagnosis + efficiency, verification
     status, budget use + efficiency. Self-contained matching (no `src` -> `eval`
     dependency) plus documented `WORKUP_ALIASES` panel/component map.
   - `aggregate_encounter_scores`: distribution summary (mean/min/max, rates).
2. `src/vh/agents/replay.py` (new):
   - `TranscriptEntry`, `ReplayBundle`, `RecordingAdapter`, `ReplayAdapter`.
   - `record_encounter` / `replay_encounter` / `save_bundle` / `load_bundle`.
   - `hash_event_log`: canonical hash normalizing volatile IDs, excluding
     `event_id`/`wall_time`/`run_id` envelope fields.
3. `src/vh/agents/cli.py` (new): `vh replay <run_id>` re-executes from the
   recorded transcript and reports MATCH/MISMATCH (exit 0/1).
4. `src/vh/cli.py`: routes the `replay` command suite.
5. `src/vh/agents/__init__.py`: exports scorer and replay symbols.
6. `src/vh/agents/orchestrator.py` (FIX-LOOP fix + replay hooks):
   - `run_encounter` accepts optional `run_id`/`seed`/`event_store` (defaults
     preserve prior behavior).
   - Workup scheduler routes every hidden diagnostic (previously the LAB/DX
     prefix filter ordered zero tests for natural-named golden orders).
7. `eval/harness/encounter.py` (new): `EncounterPipeline` and
   `EncounterHarnessScorer`; `eval/harness/runner.py` supports
   `pipeline_name="encounter"`.
8. `tests/test_step_34_acceptance.py` (new): 9 acceptance tests.
9. `tests/test_step_33_acceptance.py`: FIX-LOOP regression test
   `test_orders_natural_named_hidden_tests_regression`.
10. `docs/decisions/ADR-0006-encounter-scoring-replay.md` (new).
11. `.gitignore`: ignores `data/replays/` (generated reproducible artifacts).

---

## 2. Tests Added and Full Regression Results

### New Tests (`tests/test_step_34_acceptance.py`, 9 tests):
- `test_scorer_perfect_encounter_high_score`: hand-built perfect encounter,
  composite >= 0.85, all axes 1.0.
- `test_scorer_missed_diagnosis_low_score`: wrong dx gives dx 0.0, composite < 0.5.
- `test_scorer_workup_recall_precision`: partial + unnecessary orders give 0.5/0.5.
- `test_scorer_workup_alias_panel_matching`: panel/component synonyms match.
- `test_scorer_red_flags_verification_time_budget`: missed flags, failed
  verification, degraded time/budget axes.
- `test_replay_10_runs_identical_hashes`: 10 golden runs replay byte-identical.
- `test_full_golden_set_run_reports_metrics`: all 60 verified cases scored,
  distribution keys present and in [0,1].
- `test_encounter_pipeline_in_harness`: harness pipeline + scorer integration.
- `test_replay_cli_reproduces_log`: `vh replay <run_id>` exits 0 with MATCH.

### Test Suite Execution:
- `tests/test_step_33_acceptance.py`: 10 passed (9 original + 1 FIX-LOOP regression).
- `tests/test_step_34_acceptance.py`: 9 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **259 of 259
  tests passed (100% green)** in 309.83s (249 pre-existing + 9 new Step 34 +
  1 Step 33 FIX-LOOP regression). Ruff/mypy skipped by the runner (modules not
  installed locally; pre-existing environment condition).
- Secret scanner: 0 hardcoded secrets or credentials detected.

### Measured golden-set distribution (60 verified cases, seed 42):
- 60/60 `completed`; 60/60 replays byte-identical (0 mismatches).
- `encounter_score_mean` 0.3596, min 0.1644, max 0.9944.
- `dx_top1_rate` 0.1667, `dx_top3_rate` 0.3333, `workup_recall_mean` 0.2403,
  `workup_precision_mean` 0.2667, `red_flags_addressed_mean` 0.25,
  `verification_pass_rate` 1.0.

---

## 3. Failures Found and Resolved

1. **Empty-workup defect (STEP 33 FIX-LOOP):** symptom: workup recall/precision
   0.0 on all 60 golden cases. Root cause: the P5.3 scheduler's LAB/DX-prefix
   filter matched none of golden v1's natural order names, ordering zero tests.
   Fix: route every hidden diagnostic (lab/imaging/name-heuristic/default).
   Regression test added; Step 33 suite re-run 10/10 green, then Step 34 suite.
2. **Collection IndentationErrors (2x):** caused by malformed no-op edits during
   development; repaired immediately, no test logic affected.
3. **CLI subprocess `ModuleNotFoundError`:** fixed by passing `PYTHONPATH=src`
   in the test's subprocess environment.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Encounter scorer (dx top-1/top-3, workup recall/precision, red flags, time to diagnosis, verification status, budget used) | `src/vh/agents/scoring.py`; scorer unit tests (5 tests) | PASS |
| Scorer unit tests on hand-built encounters | `tests/test_step_34_acceptance.py` (tests 1-5) | PASS |
| Replay records every LLM output; `vh replay <run_id>` reproduces event log exactly | `src/vh/agents/replay.py`, `src/vh/agents/cli.py`; CLI test | PASS |
| Replaying 10 runs gives identical event logs (hash comparison) | `test_replay_10_runs_identical_hashes` | PASS |
| Full golden-set run completes and metrics reported | `test_full_golden_set_run_reports_metrics` (60 cases) | PASS |
| Encounter pipeline added to the harness | `eval/harness/encounter.py`, runner `encounter` branch; harness test | PASS |
| Thresholds/golden sets untouched | `git diff` shows no `configs/thresholds.yaml` or `eval/golden/` changes | PASS |

---

## 5. Open Questions / Assumptions

- **Proposal for H5 (owner decides, NOT written):** `agents.encounter_score_min = 0.30`.
  Rationale: below the measured 0.36 mean and above the 0.16 floor, so the gate
  catches regressions without blocking Phase 5 on fine-tuning gains (diagnostic
  uplift is Phase 7 work per layer separation). Low dx_top1 (0.17) reflects the
  deterministic heuristic generation baseline; low workup recall (0.24) partly
  reflects golden naming gaps (generic hidden names vs specific expected workup).
- Replay determinism scope: volatile IDs and wall-clock fields are normalized
  before hashing (documented in ADR-0006); all clinical content must match exactly.
- No other open questions. All criteria met.
