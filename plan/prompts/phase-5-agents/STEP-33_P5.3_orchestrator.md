# STEP 33 of 54 | P5.3: Orchestrator, budgets and loop detection

- **Phase 5:** Agents & Orchestration (headless)
- **Run after:** STEP 32 (P5.2) report shows Status: DONE.
- **Next:** STEP 34 (P5.4): `plan/prompts/phase-5-agents/STEP-34_P5.4_encounter-scoring-replay.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Multi-agent systems fail by looping, stalling or silently giving up. Every encounter must end in an explicit, recorded state.

## Task
- Orchestrator (LangGraph unless ADR-0001 chose otherwise) managing turns, shared encounter state and termination (report submitted and routed, or a budget exhausted).
- Budgets per encounter: max steps, max tokens, max cost, max simulation time (configurable).
- Loop detection: the same action with the same arguments repeated K times, or no progress for M steps, ends the encounter with status `loop_detected`.
- Timeouts and errors: an agent failure ends the encounter with status `error`, never a silent success.

## Acceptance criteria (write these as tests first)
- Tests for every termination path.
- Each budget is enforced.
- A loop scenario triggers `loop_detected`.
- An end-to-end run of 10 golden cases completes.

## Deliverables
- `src/vh/agents/orchestrator.py`
- `docs/steps/STEP-33.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-33.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
