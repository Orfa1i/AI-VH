# FIX LOOP (use whenever a step or gate fails)

Paste this prompt together with the failing step report or gate report.

> Read `CLAUDE.md`. Fix only what is listed as failing. Do not start new work.

1. List every failure: test id or metric, symptom, and the first failing commit if known.
2. For each failure: reproduce it, identify the root cause (not the symptom), and state it in one sentence.
3. Write a regression test that fails because of this defect. Confirm it fails.
4. Fix the root cause. Do not skip, weaken or delete existing tests. Do not edit `configs/thresholds.yaml`. Do not modify released golden sets.
5. Run the full regression suite (`make test-all`) and `make eval`.
6. Repeat 2 to 5 until everything passes.
7. **Reopen rule:** if the root cause lives in an earlier phase, write `REOPENED` with the reason at the top of that phase's `docs/phase-reports/phase-N.md`, fix it there, re-run that phase's gate, then re-run every later gate in order before continuing.
8. If a failure cannot be fixed without changing a threshold, the golden set, or a clinical decision, stop with Status: BLOCKED and explain. Those decisions belong to the project owner.
9. Report (append to the failing step or gate report under "Fix loop N"): failures, root causes, fixes, new regression tests, full-suite result.
10. Then re-run the original step's checks or gate prompt from the beginning.
