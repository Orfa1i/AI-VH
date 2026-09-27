# STEP 37 of 54 | P6.2: Review API with overlap sampling

- **Phase 6:** Doctor Review & Feedback Store
- **Run after:** STEP 36 (P6.1) report shows Status: DONE.
- **Next:** STEP 38 (P6.3): `plan/prompts/phase-6-feedback/STEP-38_P6.3_review-ui.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Some reports are reviewed by two doctors independently, so agreement can be measured before the data is trusted for training.

## Task
- Authentication with a reviewer role (reuse existing auth if `docs/current-state.md` shows one).
- Endpoints: review queue; get report (with evidence text and verification flags); submit approve / correct / reject / comment; per-claim ratings.
- Assignment: flagged reports first; overlap sampling so that `review.overlap_fraction` of reports get two independent reviewers who cannot see each other's review.
- Input validation against the taxonomy.

## Acceptance criteria (write these as tests first)
- Contract and authorisation tests (non-reviewers blocked; an overlap reviewer cannot see the other review).
- Overlap fraction within tolerance over 1,000 simulated assignments.

## Deliverables
- `src/vh/feedback/api.py`
- `docs/steps/STEP-37.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-37.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
