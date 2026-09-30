# ADR-0009: Doctor Review UI Test Strategy and Shell Integration

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-6-feedback/STEP-38_P6.3_review-ui.md`

---

## 1. Context

P6.3 requires component tests, Playwright e2e for every action, axe checks,
and strict shell-token reuse. The repo plans `web/` but code lives in
`frontend/` (ADR-0001 mapping); no frontend test runner existed.

## 2. Decision

- Stack: vitest + jsdom + Testing Library (component), @playwright/test +
  @axe-core/playwright (e2e + axe). Reused the pre-installed
  chromium-1243 browsers (exact match for @playwright/test 1.63, no download).
- The UI talks to the real STEP 37 API in e2e via a minimal runnable server
  (`vh/feedback/server.py`, uvicorn) with a wipe-and-seed demo mode
  (`FEEDBACK_DEMO_SEED=1`, fixed dev-only token, 1 flagged + 2 plain reports).
  Seeding lives in `vh/feedback/seed.py` (dev-only, idempotent).
- New `REVIEW` tab in the shell reuses existing nav patterns, Tailwind
  slate/sky palette, Inter/`font-mono` type, and `hud-bracket` surfaces.
  White-on-sky buttons use sky-700 (passes 4.5:1; sky-600 does not).
- Axe in e2e is scoped to `<main>` (all review UI lives there). Scoping
  exposed a genuine contrast defect of ours (slate-500 on sky-50, 4.46:1),
  fixed to slate-600. It also surfaced a PRE-EXISTING shell issue outside our
  scope: the sub-header census div sits outside any landmark (axe `region`).
  Flagged for shell follow-up; review views themselves are violation-free.
- CORS on the review server is origin-restricted via `FEEDBACK_CORS_ORIGINS`
  (default localhost:5173 only).

## 3. Consequences

- `pnpm test` (vitest) and `pnpm test:e2e` (playwright) are the frontend gates;
  `pnpm build` (tsc + vite) and `pnpm lint` (oxlint) stay green.
- Token revocation (ADR-0008) still pending before production use.
