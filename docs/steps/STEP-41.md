# Step Report: STEP-41 (P7.1 Training Dataset Curation)

- **Phase:** Phase 7: Fine-Tuning & Model Lifecycle
- **Step:** STEP 41 of 54 (P7.1)
- **Status:** BLOCKED (waiting for data — 0 of 500 automated-reviewed cases)
- **Timestamp:** 2026-09-30T16:00:00Z
- **Tag:** (none — gate unblocks on data, not on this report)

---

## 1. Gate check performed

- Read the step prompt, `CLAUDE.md`, `docs/current-state.md`, and the Phase 6
  gate report (`docs/phase-reports/phase-6.md` PASS).
- `training.min_reviewed_cases` = 500 (owner-set, unchanged).
- Automated-reviewed counter over all registered snapshots/live stores: **0**.
  0 < 500, so per the prompt ("If there are fewer, stop with Status: BLOCKED")
  and the plan rule ("waiting for data is not a test failure"), no dataset is
  curated and no training starts.

## 2. Track readiness (approved automated-review design, implemented + tested)

- Predicate, independent evaluator, deletion-only repair with mandatory
  revalidation: `src/vh/training/auto_review.py` (19 acceptance tests in
  `tests/test_auto_review_track.py`, all passing).
- Storage: migration 0003 (`automated_reviews`, `automated_targets`),
  thread-safe writers/readers, human-path write gates both directions.
- Counter (distinct patients), stratified patient splits, contamination and
  dedup checks, honest labeling: `src/vh/training/curation.py` (+
  `configs/training/curation.yaml`, agent-owned tunables).
- Snapshot export sections + manifest counts: `src/vh/feedback/snapshot.py`.
- Full regression suite green (see below). Secret scanner clean.

## 3. Failures found and resolved

- Phase-4 DDI engine-shape defect (spurious critical on every evaluation):
  fixed in `src/vh/verification/rules/interaction.py` with Step-25 regression
  test; full suite re-run green. Details in ADR-0013 §4.

## 4. Gap review

| Step 41 criterion | Status / evidence |
| :--- | :--- |
| ≥500 reviewed cases in a feedback snapshot | **UNMET: 0/500** — BLOCKED, correctly |
| Zero patient overlap across splits | Code + tests ready (`split_by_patient`); no live data to split |
| Zero golden-set contamination | Code + tests ready (`contamination_check`); nothing to check |
| Reproducible dataset from snapshot + config | Code ready; nothing to reproduce yet |
| Dataset artifact + card | Not produced (no data — producing empty artifacts would be theater) |

## 5. Open questions / assumptions

- The 500 counts **automated-reviewed** cases per the approved track (distinct
  `patient_ref`s, approve/correct only). No threshold change was needed.
- H7 (blinded physician comparison) still needs the owner ruling flagged in
  the approved design: physician vs optional/external under the doctor-free
  policy. Unblocks Phase 7's end, not its start.
- Accumulation path forward: encounter runner → `store_original` ingestion
  bridge (not yet built) → automated evaluation → snapshots → counter.
  The ingestion bridge is the concrete next implementation step once approved.
