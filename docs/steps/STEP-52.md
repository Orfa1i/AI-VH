# Step Report: STEP-52 (P9.2 Knowledge Graph Experiment)

- **Phase:** Phase 9: Advanced Intelligence
- **Step:** STEP 52 of 54 (P9.2)
- **Status:** DONE
- **Timestamp:** 2026-09-30T22:00:00Z
- **Tag:** `step-52-pass`

---

## 1. Built: Files Created or Changed

1. `src/vh/rag/kg/graph.py` (new): typed nodes, provenance-mandatory edges,
   resolution checks.
2. `src/vh/rag/kg/build.py` (new): deterministic construction from RxNorm
   formulary, safety tables, reviewed chunk map, and local chunker (same
   chunker config as the harness so ids align); `verify_graph` provenance audit.
3. `src/vh/rag/kg/retrieval.py` (new): term matching, reachable-chunk
   resolution, boost/append merge, `retrieve_with_kg` with `kg_enabled` flag,
   `is_kg_enabled` config reader.
4. `src/vh/rag/kg/evaluate.py` (new): full-golden-set A/B with the STEP-18
   methodology plus the strict adoption rule.
5. `configs/rag.yaml`: `kgraph.enabled: true` (measured adoption).
6. `tests/test_step_52_acceptance.py` (new): 7 acceptance tests.
7. `docs/decisions/ADR-0015-knowledge-graph.md` (new; prompt said ADR-0007,
   which is already taken — collision noted in the ADR).

---

## 2. Tests Added and Full Regression Results

### New Tests (7):
- Edge provenance resolution + required node/relation coverage.
- Augmentation determinism; resolvable-only additions (index + locator checks).
- A/B reproducibility (metrics identical sans wall-clock).
- Adoption-rule unit cases (improve→adopt; tie/regress/unsafe→reject).
- Full-60 A/B with flag-vs-decision consistency + flag-off plumbing.

### Test Suite Execution:
- `tests/test_step_52_acceptance.py`: 7 passed.
- Full verification suite (`py -3.13 scripts/test_all.py test-all`): **342 of 342
  tests passed (100% green)** in 493.04s (335 pre-existing + 7 new Step 52).
  Ruff/mypy skipped by the runner (modules not installed locally; pre-existing
  environment condition).
- Secret scanner: 0 findings.

---

## 3. Failures Found and Resolved

1. **Repo-root depth bug** (`kg/` one level deeper than assumed): A/B measured
   0 cases; fixed depth, re-measured 60/60.
2. **Latency in determinism assert**: wall-clock excluded, bounded separately.
3. **Syntax slips** (`from typing` import, bad conditional import): fixed.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
| :--- | :--- | :--- |
| Graph from normalised sources, provenance per edge | `build.py` + resolution/coverage tests | PASS |
| KG retrieval behind feature flag | `kgraph.enabled` + flag tests | PASS |
| A/B on golden set vs RAG-only | `evaluate.py`; full-60 measured | PASS |
| Adopt only on improvement without safety regression | Rule + measured ADOPT (MRR +0.2155, all guards held) | PASS |
| Every edge resolves to its source | Resolution test, 0 unresolved | PASS |
| Full regression green | Below | PASS |
| Thresholds/golden sets untouched | `git diff` shows neither (`rag.yaml` is not thresholds) | PASS |

---

## 5. Open Questions / Assumptions

- Dose/red-flag tables excluded (no graph relations by nature); documented.
- Condition term lists are retrieval heuristics, not clinical claims.
- No other open questions.

## 6. Mini-gate (STEP 52 §8)

| Acceptance criterion | Result |
| :--- | :--- |
| Every edge resolves to its source | PASS (0 unresolved) |
| Adopt only if primary metrics improve with no safety regression | PASS (adopted on +0.2155 MRR, guards held) |
| Full regression suite of all phases passes | PASS (see below) |
| **Mini-gate** | **PASS** |
