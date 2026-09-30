# Step Report: STEP-47 (P8.2 2D Department Dashboard)

- **Phase:** Phase 8: Virtual Hospital Environment (2D then 3D)
- **Step:** STEP 47 of 54 (P8.2)
- **Status:** DONE
- **Timestamp:** 2026-09-30T18:30:00Z
- **Tag:** `step-47-pass`
- **Note:** Executed under the plan's explicit permission to run Phase 8 while
  Phase 7 waits on training data.

---

## 1. Built: Files Created or Changed

1. `frontend/src/components/hospital/` (new): `api.ts` (typed transport +
   `groupByRun`), `departments.ts` (pure actor/action → department mapping,
   status derivation; display only, zero clinical logic), `DepartmentBoard.tsx`
   (8 departments, counts, selection), `PatientCard.tsx` (expandable timeline,
   agent activity feed, filed-report display), `DepartmentBoardSection.tsx`
   (mode toggle, replay fetch + incremental live SSE parsing).
2. `frontend/src/App.tsx`: `WARDS` tab ("Department Board") reusing shell nav.
3. `frontend/e2e/department-board.spec.ts` (new): 2 e2e tests (replay state
   sequence; live parity).
4. `frontend/playwright.config.ts`: event-API webServer (:8101, seeded demo).
5. `src/vh/events/server.py` (new): runnable event API with origin-restricted
   CORS and wipe-and-seed demo mode (dev-only, 1 completed + 1 in-progress run).
6. `tests/`: `frontend` vitest (5) + playwright (2) suites (see below).

---

## 2. Tests Added and Full Regression Results

### New Tests:
- Vitest (5): department mapping incl. all-8 coverage + unknown fallback;
  status derivation; board render/select; card expand (timeline, feed, report).
- Playwright e2e (2): replay renders exact action/actor sequences + report;
  live mode reaches identical states.

### Verification results:
- `pnpm vitest run`: 18 passed (all frontend suites).
- `pnpm test:e2e`: 7 passed (5 review + 2 board; review suite unregressed).
- `pnpm run build` (tsc + vite): PASS. `pnpm run lint`: PASS (only
  pre-existing warnings in untouched files).
- Full Python regression (`py -3.13 scripts/test_all.py test-all`): **321 of 321
  passed (100% green)**. Step 47 adds no Python tests; its gates are the
  frontend suites above (5 vitest + 2 Playwright, all passing) plus
  `pnpm build`/`lint` green.
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **CORS block** (browser :5173 → API :8101): origin-restricted middleware.
2. **SSE named events vs `onmessage`**: fetch + manual frame parsing instead.
3. **Infinite live responses**: client renders frames incrementally as they
   arrive (proper live semantics) instead of awaiting completion.
4. **SSE frame parser seeded `'{}'` then appended**: parsed garbage; fixed to
   empty-seed with `{}` fallback.
5. **Test races**: `allTextContents` doesn't auto-wait (added `toHaveCount`
   guards); ambiguous `getByText('Live')` scoped.
6. **Toggle not committing (dev StrictMode)**: functional `setState` updater
   form repeatedly failed to commit in this tree; direct-value form verified
   working with identical toggle semantics (documented in code).
7. **Invisible syntax gremlin** in the test file (balanced text, oxc parse
   error): resolved by clean rewrite; plus substring-match and unused-import
   build fixes.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Department board: ER, Reception, Lab, Radiology, Pharmacy, Wards, ICU, Clinics | `departments.ts` (8), board columns; mapping test | PASS |
| Patient cards: status, timeline, activity feed, report/review links | `PatientCard.tsx`; card test (timeline, feed, filed report) | PASS |
| Driven only by event stream; live + replay | Section modes; replay + live e2e | PASS |
| Replay renders expected state sequence | Replay e2e (exact action/actor arrays) | PASS |
| Live and replay both tested | Live e2e + replay e2e | PASS |
| No clinical logic in frontend | Mapping/display only; scorer/router never imported (transport + labels) | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- ICU has no mapped encounter actions yet (shows honest empty state); Step 48's
  3D scene may populate specialized flows. No other open questions.
