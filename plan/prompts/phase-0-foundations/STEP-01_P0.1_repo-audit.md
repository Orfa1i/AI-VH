# STEP 01 of 54 | P0.1: Repository audit (read-only)

- **Phase 0:** Foundations, Governance & Evaluation Harness
- **Run after:** Nothing. This is the first step.
- **Next:** STEP 02 (P0.2): `plan/prompts/phase-0-foundations/STEP-02_P0.2_skeleton-config-ci.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
This project extends existing work. Known components (verify each one, do not assume):
- A MedGemma service governed by a system prompt.
- A backend with `knowledge_sources.py` integrating RxNorm, DailyMed, openFDA and PubMed, used by the NABD drug search feature.
- A frontend app shell called "Virtual Hospital – Clinical AI OS".
- Separate specialist imaging models (fracture localisation, knee OA grading).
These may live in one repository or several.

## Task
- This is a read-only audit. Do not modify, move, install or delete anything. The only files you write are the two deliverables below.
- Inventory: languages, frameworks, package managers, entry points, and how to run each component.
- MedGemma: which variant, how it is served (runtime, endpoint, hardware), where the system prompt lives.
- `knowledge_sources.py`: what each function does, which external APIs it calls, how results reach the frontend.
- Frontend: stack, routing, shell components, design tokens/theme, state management.
- Existing tests, configuration, environment variables, dependencies and their versions.
- Security scan: hard-coded secrets, API keys, tokens, and any real patient data. Report file locations only; never print secret values.
- Map the existing code onto the target layout in `plan/README.md` (section "Target repository layout").
- For each phase 1–9 write one line: reuse / adapt / build new, with file paths.
- Propose (do not apply) the layout mapping as ADR-0001.

## Acceptance criteria (write these as tests first)
- `git status` shows only the two new documents.
- Every factual statement in `docs/current-state.md` cites a file path (with line range where useful).
- Every phase 1–9 has a reuse / adapt / build-new line.
- A security findings section exists, even if the result is "none found" (state what was scanned).

## Deliverables
- `docs/current-state.md`
- `docs/decisions/ADR-0001-repo-layout.md` (status: Proposed)
- `docs/steps/STEP-01.md` (step report)

## Execution rule (mandatory, adapted for a read-only step)
1. Modify nothing except the deliverables listed above.
2. Verify every statement by opening the file or running a read-only command, and cite the path.
3. Re-read both documents against the task list line by line; anything missing, add it and re-check.
4. Only when complete, write the step report and stop. Do not start STEP 02.

## Step report: write to `docs/steps/STEP-01.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
