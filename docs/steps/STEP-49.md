# Step Report: STEP-49 (P8.4 UI Integration and No-Side-Effect Proof)

- **Phase:** Phase 8: Virtual Hospital Environment (2D then 3D)
- **Step:** STEP 49 of 54 (P8.4)
- **Status:** DONE
- **Timestamp:** 2026-09-30T20:00:00Z
- **Tag:** `step-49-pass`
- **Note:** Executed under the plan's explicit permission to run Phase 8 while
  Phase 7 waits on training data.

---

## 1. Built: Files Created or Changed

1. `tests/test_step_49_integration.py` (new): 6 integration tests (see below).
2. `src/vh/agents/replay.py` (additive): `replay_encounter` accepts an optional
   external `event_store` so a live UI tail can attach during the run; hash is
   computed over exactly what landed in the store used.

---

## 2. Tests Added and Full Regression Results

### New Tests (6):
- `test_identical_outputs_ui_on_vs_off`: 10 golden encounters, recorded LLM
  outputs; plain replay vs replay with a live tail draining the same store
  plus SSE serving over the result. Canonical log hashes and report hashes
  compared per case; divergence count asserted 0 against
  `ui.output_divergence_count`.
- `test_replay_with_live_tail_attached_matches`: tail attached during replay
  reproduces the recorded (actor, action, sim_time) sequence and hash.
- `test_sse_delivery_lag_below_threshold`: full-stream delivery completes far
  below `ui.max_sync_lag_ms` (500); every event wall_time predates delivery.
- `test_consumers_cannot_mutate_clinical_state`: frozen `SimEvent`/`AgentView`
  reject assignment; append-only store rejects set/del.
- `test_ui_thresholds_present`: both UI bars loaded with specified values.
- `test_no_clinical_write_paths_in_view_layers`: static scan of
  `src/vh/events/stream.py` for engine/scorer/store symbols.

### Test Suite Execution:
- `tests/test_step_49_integration.py`: 6 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **327 of 327
  tests passed (100% green)** in 481.64s (321 pre-existing + 6 new Step 49).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Missing `event_store` hook** (expected test-first failure): added the
   optional parameter, backward compatible.
2. **Raw event-id comparison across runs**: event ids are random per run by
   design (canonical hash excludes them). Tests now assert canonical hashes
   plus exact (actor, action, sim_time) sequences — the honest identity.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Same seeded encounters + recorded LLM outputs, UI on vs off | `record_encounter` + dual replay per case (10 golden) | PASS |
| Report hashes and event logs compared | Per-case canonical + report hash compare | PASS |
| Identical outputs (`output_divergence_count` = 0) | 0 divergences == threshold 0 | PASS |
| Lag at/below `max_sync_lag_ms` (500) | SSE delivery timing test | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- Delivery lag is measured emission→SSE-delivery through the real HTTP stack;
  browser paint is bounded separately by the fps gate (Step 48, ≥ 50 fps).
  No other open questions.
