# STEP 34 of 54 | P5.4: Encounter scoring and deterministic replay

- **Phase 5:** Agents & Orchestration (headless)
- **Run after:** STEP 33 (P5.3) report shows Status: DONE.
- **Next:** Human checkpoint(s) H5, then STEP 35 (P5.G): `plan/prompts/phase-5-agents/STEP-35_P5.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Agents are judged on the whole encounter, not just the final diagnosis: what they ordered, what they missed, and how long it took.

## Task
- Encounter scorer: diagnostic correctness (top-1 / top-3), workup recall (expected tests ordered), workup precision (unnecessary tests), red flags addressed, time to diagnosis (simulation time), verification status, budget used.
- Replay: record every LLM output per run; `vh replay <run_id>` re-executes deterministically from the recorded outputs and must reproduce the event log exactly.
- Add the encounter pipeline to the harness.
- Propose a value for `agents.encounter_score_min` in your step report. Do not write it; the project owner sets it.

## Acceptance criteria (write these as tests first)
- Scorer unit tests on hand-built encounters.
- Replaying 10 runs gives identical event logs (hash comparison).
- A full golden-set run completes and metrics are reported.

## Deliverables
- `src/vh/agents/scoring.py`, replay CLI
- `docs/steps/STEP-34.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-34.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
