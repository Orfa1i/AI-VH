# Step Report: STEP-39 (P6.4 Reviewer Agreement and Feedback Snapshots)

- **Phase:** Phase 6: Doctor Review & Feedback Store
- **Step:** STEP 39 of 54 (P6.4)
- **Status:** DONE
- **Timestamp:** 2026-09-30T15:00:00Z
- **Tag:** `step-39-pass`

---

## 1. Built: Files Created or Changed

1. `src/vh/feedback/agreement.py` (new): `cohens_kappa` (degenerate-safe),
   `claim_kappa` / `decision_kappa` over first-two-decided overlap sessions,
   `per_taxonomy_error_rates`, `reviewer_throughput`, `agreement_report`.
2. `src/vh/feedback/snapshot.py` (new): `build_snapshot` exporting canonical
   `originals/evidence/edits/finals/ratings` JSONL + `agreement.json` +
   manifest with counts, dataset sha, and lineage; registers a versioned
   `dataset` artifact via the existing `ArtifactRegistry`.
3. `src/vh/feedback/cli.py` (new): `vh feedback snapshot --db --output
   --version [--registry-db]`; routed through `src/vh/cli.py`.
4. `src/vh/feedback/models.py` (extended, backward compatible): store getters
   `list_originals`, `all_claim_ratings`, `decided_sessions_for_original`,
   `decision_latencies` (all thread-synchronized).
5. `tests/test_step_39_acceptance.py` (new): 5 acceptance tests.
6. `docs/decisions/ADR-0010-agreement-snapshots.md` (new).
7. `.gitignore`: ignores `data/feedback_snapshots/` (generated artifacts).

---

## 2. Tests Added and Full Regression Results

### New Tests (`tests/test_step_39_acceptance.py`, 5 tests):
- `test_kappa_known_value`: hand-computed kappa 0.6, perfect 1.0, empty 0.0.
- `test_claim_and_decision_agreement`: end-to-end store overlap (claim 0.0,
  decision 1.0) plus full `agreement_report` shape.
- `test_taxonomy_rates_and_throughput`: 5/8 error rate; 2 reviewers × 1 decision.
- `test_snapshot_reproducible_and_lineage`: two snapshots byte-identical on
  data files with equal dataset sha; manifest counts/lineage/artifact link;
  agreement flags present.
- `test_snapshot_cli`: `vh feedback snapshot` exits 0 with versioned output.

### Test Suite Execution:
- `tests/test_step_39_acceptance.py`: 5 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **279 of 279
  tests passed (100% green)** in 470.70s (274 pre-existing + 5 new Step 39).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

None on implementation (5/5 first run). One test-hygiene fix during writing:
removed a vacuous tautological assertion line before first execution.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Cohen's kappa on overlap pairs (claims + decisions) | `agreement.py`; known-value + store tests | PASS |
| Per-taxonomy error rates; reviewer throughput | Same module; rates/throughput test | PASS |
| Versioned dataset snapshot (originals, evidence, edits, finals, ratings, agreement flags) | `snapshot.py`; snapshot tests | PASS |
| Kappa correct on known-value fixture | `test_kappa_known_value` (0.6) | PASS |
| Snapshots reproducible + lineage recorded | Reproducibility test (byte-identical, registry artifact) | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither | PASS |

---

## 5. Open Questions / Assumptions

- Only decided sessions enter agreement metrics; undecided work is invisible
  by design. No other open questions.
