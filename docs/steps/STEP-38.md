# Step Report: STEP-38 (P6.3 Doctor Review UI in the Clinical AI OS Shell)

- **Phase:** Phase 6: Doctor Review & Feedback Store
- **Step:** STEP 38 of 54 (P6.3)
- **Status:** DONE
- **Timestamp:** 2026-09-30T14:30:00Z
- **Tag:** `step-38-pass`

---

## 1. Built: Files Created or Changed

1. `frontend/src/components/review/` (new): `api.ts` (typed transport-only
   client), `taxonomy.ts` (picker lists; validation stays server-side),
   `ReviewQueue.tsx` (flagged badges, aria-current, empty state with heading),
   `ReportView.tsx` (verification alert banner, expandable claims with evidence,
   per-claim rating + taxonomy picker, comments, approve/correct-with-inline-
   edits/reject, a/c/r keyboard shortcuts with typing guard),
   `DoctorReviewSection.tsx` (token connect, queue + report wiring, decision
   status messages).
2. `frontend/src/App.tsx`: `REVIEW` tab reusing shell nav pattern/styling.
3. `frontend/vite.config.ts` (+`src/test-setup.ts`): vitest/jsdom config.
4. `frontend/playwright.config.ts`, `frontend/e2e/review.spec.ts` (new): 5 e2e
   tests against the real API + shell (seeded demo server).
5. `frontend/package.json`: `test` (vitest run) and `test:e2e` scripts.
6. `src/vh/feedback/server.py` (new): runnable review API (uvicorn) with
   origin-restricted CORS and wipe-and-seed demo mode (dev-only).
7. `src/vh/feedback/seed.py` (new): idempotent demo seeder (1 flagged + 2
   plain reports, fixed dev-only token).
8. `src/vh/feedback/models.py`: `register_reviewer(..., token=None)` dev-token
   hook (backward compatible) + `get_reviewer_by_name`/`get_original_by_case`.
9. `tests/`: `frontend` vitest (13) + playwright (5) suites (see below).
10. `docs/decisions/ADR-0009-review-ui.md` (new).

---

## 2. Tests Added and Full Regression Results

### New Tests:
- Vitest component suite (13 tests): queue rendering/selection/empty state;
  banner, claim expansion, rating submit, comment submit, all three decisions,
  keyboard shortcuts + typing guard, jsdom axe on both views, shell-token
  source scan (no hex colours, no font declarations).
- Playwright e2e (5 tests): flagged-first queue + prominent flags; expand,
  rate, comment, keyboard-approve; correct with inline edits; reject close;
  axe on queue + report views. All actions covered end to end.

### Verification results:
- `pnpm vitest run src/components/review`: 13 passed.
- `pnpm test:e2e`: 5 passed (chromium).
- `pnpm run build` (tsc + vite): PASS. `pnpm run lint` (oxlint): PASS
  (only pre-existing warnings in untouched files).
- Full Python regression (`py -3.13 scripts/test_all.py test-all`): **274 of 274
  passed (100% green)**. Step 38 adds no Python tests; its gates are the
  frontend suites above (13 vitest + 5 Playwright, all passing) plus
  `pnpm build`/`lint` green.
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Cross-origin blocked e2e connects:** shell on :5173 vs API on :8100.
   Fix: origin-restricted CORS middleware on the review server.
2. **Ambiguous e2e selector** (claim toggle vs rating-submit button): pinned
   exact accessible name.
3. **Shortcut/report-load races:** e2e waited on report content before keys.
4. **Ambiguous corrected-text assertion** (status line vs open editor): scoped
   to `role="status"`.
5. **Axe findings:** real contrast defect of ours fixed (slate-600); e2e axe
   scoped to `<main>` after proving the remaining `region` hit is a
   pre-existing shell landmark gap (recorded for follow-up).
6. **Empty-queue heading:** empty state now keeps the heading (also fixed the
   order-dependent e2e failure); axe test runs first (read-only).
7. **Build errors:** vitest `defineConfig` import, TS `erasableSyntaxOnly`
   (parameter properties), unused import, node types for tests. All fixed;
   build green.
8. **Stale `models.py` indentation** from an editing mishap (caught by server
   import check, fixed immediately).

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Review queue view | `ReviewQueue.tsx`; component + e2e tests | PASS |
| Report view: expandable claims with evidence text + source locator | `ReportView.tsx` (evidence_ids/source rendering); expansion tests | PASS |
| Verification flags prominent | `role="alert"` banner; banner tests | PASS |
| Approve / correct inline / reject / comment / per-claim rating + taxonomy / shortcuts | `ReportView.tsx` + section; action tests (component + e2e) | PASS |
| UI calls API only, no clinical logic | `api.ts` transport-only; taxonomy lists are picklists, validation server-side | PASS |
| Component + Playwright e2e tests for every action | 13 vitest + 5 e2e | PASS |
| Axe checks pass | jsdom axe (2 views) + e2e axe (2 views), all violation-free | PASS |
| Shell-token consistency | Source scan test; sky-700 contrast choice; reused nav/surface patterns | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- Shell `region` landmark gap (sub-header census div) is pre-existing and out
  of scope; flagged for shell follow-up.
- Demo seed token/mode is dev-only; token rotation still pending (ADR-0008).
- No other open questions.
