# STEP 05 of 54 | P0.5: Golden-set authoring tools and draft seed cases

- **Phase 0:** Foundations, Governance & Evaluation Harness
- **Run after:** STEP 04 (P0.4) report shows Status: DONE.
- **Next:** Human checkpoint(s) H0.1, H0.2, then STEP 06 (P0.G): `plan/prompts/phase-0-foundations/STEP-06_P0.G_gate.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
You may draft golden cases but you cannot verify them. Only a physician can, through a sign-off file. Default starting specialties: acute coronary syndrome (chest pain), community-acquired pneumonia, diabetic ketoacidosis. (Project owner: change these here before running this step if you want different ones.)

## Task
- CLI `vh golden new | validate | export | import-signoff | release`.
- `export` renders draft cases into a reviewer packet (Markdown and PDF) with a checkbox per field and space for corrections.
- `import-signoff` reads `docs/signoffs/golden-v{N}.md` (format: `plan/prompts/_templates/SIGNOFF.md`) and sets `status: verified` only for case ids listed as approved there, recording reviewer and date.
- `release --version N` creates a frozen `eval/golden/vN/` containing verified cases only.
- Draft 60 seed cases (20 per specialty) with `status: draft`. Supporting references must point to open sources (PubMed IDs, DailyMed set ids, published guideline sections). If you cannot identify a real reference, leave it empty and flag it. Never invent a citation.

## Acceptance criteria (write these as tests first)
- The validator rejects missing required fields and invalid enum values.
- Setting `status: verified` without a matching sign-off entry is rejected.
- A release contains only verified cases and its manifest hashes are correct.
- Every drafted reference is real and resolvable, or explicitly empty and flagged (list the flagged ones in the step report).

## Deliverables
- `src/vh/golden/` CLI
- 60 draft cases in `eval/golden/drafts/`
- Reviewer packet in `docs/signoffs/golden-v1-packet.md` (+ PDF)
- `docs/steps/STEP-05.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-05.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
