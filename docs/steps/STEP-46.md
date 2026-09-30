# Step Report: STEP-46 (P8.1 Read-Only Event Stream API)

- **Phase:** Phase 8: Virtual Hospital Environment (2D then 3D)
- **Step:** STEP 46 of 54 (P8.1)
- **Status:** DONE
- **Timestamp:** 2026-09-30T17:00:00Z
- **Tag:** `step-46-pass`
- **Note:** Executed under the plan's explicit permission to run Phase 8 while
  Phase 7 waits on training data (depends only on the Phase 5 event log).

---

## 1. Built: Files Created or Changed

1. `src/vh/events/stream.py` (new):
   - `EventStream`: ordered immutable view over an event log; sources are an
     `EventStore` (+ optional run filter) or a recorded replay bundle
     (Phase 5 synergy: `ReplayBundle.event_log` parses as `SimEvent`s).
     `tail()` yields history-then-live in append order.
   - `ReplayController`: deterministic replay with speed-scaled timing math
     (`sim-minute gap * 60 / speed`; `inf` = instant).
   - `create_event_app`: FastAPI app with `GET /events` (JSON paging with
     `after` cursor + `limit`) and `GET /events/stream` (SSE with `id:` set to
     `event_id`, `event:` to the action, replay `speed`, `live` tail mode).
     Unknown resume cursors 404 (fail closed). No write routes exist.
   - `events_after` cursor helper; `ROUTE_METHOD_ALLOWLIST = {"GET"}`.
2. `tests/test_step_46_acceptance.py` (new): 8 acceptance tests.

---

## 2. Tests Added and Full Regression Results

### New Tests (8):
- Ordering across JSON paging and SSE (ids exactly append-ordered, unique).
- Resume after forced disconnect via `after=` (JSON + SSE remainder exact).
- Unknown cursor 404s on both endpoints (fail closed).
- No-write audit: allowlist is GET-only; every route checked; POST/PUT/PATCH/
  DELETE return 404/405.
- Replay speed math (10 sim-min @2x = 300 s gaps; `inf` instant; order kept).
- Live tail across the append boundary via producer thread (4/4 in order).
- Cursor helper unit behavior incl. unknown-id KeyError.
- Replay from a recorded encounter bundle file.

### Test Suite Execution:
- `tests/test_step_46_acceptance.py`: 8 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **321 of 321
  tests passed (100% green)** in 475.26s (313 pre-existing + 8 new Step 46).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Test deadlock (test bug):** consumed from the tail generator before
   producing, single-threaded. Fix: producer thread + join timeout.
2. **Tail start position (design):** cursor began at log end, missing history.
   Fix: tail yields from the beginning; resume handled by `after=`.
3. **TestClient.delete() rejects `json=` kwarg:** split the write-method probe.
4. **Repeated `from typing X` typos** in new files (missing `import`): fixed on
   sight; full-suite typecheck unaffected (mypy not installed locally).

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Read-only SSE/WebSocket streaming live | `stream.py` SSE + live tail; ordering/tail tests | PASS |
| Replay mode at adjustable speed | `ReplayController` + `speed=`; replay/bundle tests | PASS |
| Resume from last event id | `after=` + `events_after`; resume + unknown-cursor tests | PASS |
| Ordering guaranteed | Order assertions on both surfaces | PASS |
| No write endpoints | Route audit + 404/405 probes | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- SSE (not WebSocket): one-way server→dashboard flow needs no duplex channel;
  documented here instead of an ADR. No other open questions.
