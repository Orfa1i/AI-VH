# STEP 38 of 54 | P6.3: Doctor review UI in the Clinical AI OS shell

- **Phase 6:** Doctor Review & Feedback Store
- **Run after:** STEP 37 (P6.2) report shows Status: DONE.
- **Next:** STEP 39 (P6.4): `plan/prompts/phase-6-feedback/STEP-39_P6.4_agreement-and-snapshots.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Build inside the existing "Virtual Hospital – Clinical AI OS" shell, using its design system and components.

## Task
- Views: review queue; report view listing claims, each expandable to its cited evidence text and source locator; verification flags and reasons shown prominently.
- Actions: approve, correct (inline edit), reject, comment; per-claim rating with taxonomy picker; keyboard shortcuts.
- The UI calls the API only. No clinical logic in the frontend.

## Acceptance criteria (write these as tests first)
- Component tests and Playwright end-to-end tests for every action.
- Basic accessibility checks (axe) pass.
- Visual consistency with the shell: reuse its tokens; no new ad-hoc colours or fonts.

## Deliverables
- Review pages and components in `web/`
- `docs/steps/STEP-38.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-38.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
