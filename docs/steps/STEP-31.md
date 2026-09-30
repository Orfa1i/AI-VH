# Step Report: STEP-31 (P5.1 Hospital Environment Simulator and Event Log)

- **Phase:** Phase 5: Agents & Orchestration (headless)
- **Step:** STEP 31 of 54 (P5.1)
- **Status:** DONE
- **Timestamp:** 2026-09-30T10:25:00Z
- **Tag:** `step-31-pass`

---

## 1. Built: Files Created or Changed

1. `src/vh/agents/events.py`:
   - `SimEvent`: Immutable Pydantic model (`frozen=True`, `extra="forbid"`) conforming strictly to `{event_id, run_id, sim_time, wall_time, actor, action, payload, result_ref}`.
   - `EventStore`: Append-only event ledger with in-memory store and optional JSONL disk persistence. Forbids event mutation and deletion (`PermissionError` raised on `__setitem__` / `__delitem__`, no `update` or `delete` methods). Supports resuming/reloading previous runs seamlessly from disk.
2. `src/vh/agents/environment.py`:
   - `OrderStatus`: Enum (`pending`, `released`, `result_unavailable`).
   - `ActionResponse`: Frozen response model containing order status, turnaround time, released result, message, and diagnostic category.
   - `HospitalEnvironment`: Simulator coordinating case specification, isolated `AgentView`, simulation clock, and append-only event store.
   - Actions: `request_vitals`, `order_lab(code)`, `order_imaging(code)`, `request_medication_info(drug_name)`, `consult(role, query)`, `submit_report(report)`, `advance_clock(minutes)`.
   - Security: Ground truth isolation enforced via private attributes and explicit `DataIsolationError` guard in `__getattr__`.
   - Turnaround times: Diagnostic results remain unreleased until the elapsed simulation time meets or exceeds the test's clinical turnaround time.
   - Unavailability handling: Nonexistent orders return `result_unavailable` with zero hallucinated data.
3. `src/vh/agents/__init__.py`:
   - Exported `HospitalEnvironment`, `ActionResponse`, `OrderStatus`, `SimEvent`, and `EventStore`.
4. `tests/test_step_31_acceptance.py`:
   - 7 acceptance and unit tests covering turnaround enforcement, unavailability, append-only events, fuzzing against ground truth leakage, disk reload, and multi-order staging.
5. `tests/test_step_25_acceptance.py`:
   - Updated draft table rejection/warning tests to use self-contained `tmp_path` draft fixtures, decoupling them from production-promoted tables in `configs/safety/`.

---

## 2. Tests Added and Full Regression Results

### New Tests (`tests/test_step_31_acceptance.py`):
- `test_turnaround_times_respected`: Verifies diagnostic results remain unreleased until simulation clock advances past turnaround duration.
- `test_unavailable_orders_return_result_unavailable`: Verifies non-existent lab and imaging orders return `result_unavailable` and never invent data.
- `test_actions_produce_exactly_one_event_and_events_are_append_only`: Verifies 1:1 action-to-event guarantee, schema integrity, and append-only persistence.
- `test_ground_truth_unreachable_fuzz`: 100-trial randomized hostile fuzzing test verifying zero leakage of ground truth.
- `test_event_store_reload_from_disk`: Verifies reloading an existing event log preserves historical actions.
- `test_advance_clock_validation_and_multi_orders`: Verifies negative clock rejection and staggered multi-order turnaround completion.
- `test_order_by_name_and_duplicate_orders`: Verifies ordering by clinical name and deduplication handling.

### Test Suite Execution:
- `py -3.13 -m pytest tests/test_step_31_acceptance.py`: 7 passed in 8.23s.
- `py -3.13 scripts/test_all.py test-all`: **232 of 232 tests passed (100% green)** in 268.71s.
- Secret scanner: 0 hardcoded secrets or credentials detected.

---

## 3. Failures Found and Resolved

1. **Symptom:** `test_ground_truth_unreachable_fuzz` raised `DataIsolationError` during `assert not hasattr(env.agent_view, "ground_truth")`.
   - **Root Cause:** In Python, `hasattr` catches `AttributeError`. `AgentView.__getattr__` purposely raises `DataIsolationError` (subclass of `PermissionError`) to aggressively block unauthorized snooping.
   - **Fix:** Updated the test assertion to explicitly assert `pytest.raises(DataIsolationError)` when inspecting forbidden ground truth attributes on `env.agent_view` and `env`.
   - **Regression Test:** Verified in `tests/test_step_31_acceptance.py::test_ground_truth_unreachable_fuzz`.
2. **Symptom:** Full suite run failed in `tests/test_step_25_acceptance.py` for draft table rejection in production mode.
   - **Root Cause:** In Step 30 Checkpoint H4, safety tables in `configs/safety/` were audited and promoted to `status: reviewed`. Testing draft table rejection against default tables failed because the default tables are now reviewed.
   - **Fix:** Isolated the draft table tests in `tests/test_step_25_acceptance.py` to use a temporary directory `tmp_path` containing an explicit `status: draft` table fixture.
   - **Regression Test:** Verified in `tests/test_step_25_acceptance.py` (9 passed).

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
|:---|:---|:---|
| Ground truth unreachable through any action (fuzz test) | `tests/test_step_31_acceptance.py::test_ground_truth_unreachable_fuzz` | PASS |
| Turnaround times respected | `tests/test_step_31_acceptance.py::test_turnaround_times_respected` | PASS |
| Unavailable orders return `result_unavailable` | `tests/test_step_31_acceptance.py::test_unavailable_orders_return_result_unavailable` | PASS |
| Every action produces exactly one append-only event | `tests/test_step_31_acceptance.py::test_actions_produce_exactly_one_event_and_events_are_append_only` | PASS |
| Full verification suite passing | `scripts/test_all.py` (232/232 passed) | PASS |

---

## 5. Open Questions / Assumptions

None. All criteria met and certified.
