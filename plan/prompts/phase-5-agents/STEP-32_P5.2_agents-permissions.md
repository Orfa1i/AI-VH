# STEP 32 of 54 | P5.2: Specialised agents and tool permissions

- **Phase 5:** Agents & Orchestration (headless)
- **Run after:** STEP 31 (P5.1) report shows Status: DONE.
- **Next:** STEP 33 (P5.3): `plan/prompts/phase-5-agents/STEP-33_P5.3_orchestrator.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Permissions are enforced in the tool layer, not in the prompt. A prompt can be ignored; a blocked tool cannot.

## Task
- `BaseAgent` with role, allowed tools and a record of its own events.
- Doctor: uses the Phase 3 pipeline + Phase 4 verification for its final report; can order tests and consult.
- Nurse: vitals, observations, nursing notes; cannot order medications or diagnose.
- Lab: returns released lab results with reference ranges and flags.
- Radiology: returns report text from the case; image tools stubbed with an explicit `not_implemented` until Phase 9.
- Pharmacy: medication information via RxNorm/DailyMed sources; allergy and interaction checks via the P4.1 rules.
- Permission matrix in `configs/agents/permissions.yaml`, enforced in the tool layer.
- Each agent's prompt is a versioned template.

## Acceptance criteria (write these as tests first)
- For every role, a test attempts each forbidden tool: blocked and logged.
- All LLM calls go through the adapter (verified by patching).
- Agents receive only AgentView-derived data.

## Deliverables
- `src/vh/agents/roles/`, `configs/agents/permissions.yaml`, prompt templates
- `docs/steps/STEP-32.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-32.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
