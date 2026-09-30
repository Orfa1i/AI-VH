# Phase Gate Report: Phase 8 — Virtual Hospital Environment (2D then 3D)

- **Result:** PASS
- **Gate step:** STEP 50 (P8.G)
- **Date:** 2026-09-30
- **Code evaluated:** `e886b71` (Steps 46-49; this gate changes docs only)
- **Golden set:** v1 (manifest 2026-09-28, 60 files, 60 verified cases)
- **Artifact versions:** agent prompt templates doctor/nurse/lab/radiology/pharmacy
  @1.0.0; orchestrator config 1.0.0; feedback taxonomy v1.0.0; feedback
  migrations 0001-0003; MedGemmaAdapter `google/medgemma-4b` (deterministic
  heuristic in CI/test envs); frontend three 0.186.1 + R3F 9.8.1 (pnpm lock)

---

## 1. Preconditions

- `docs/steps/STEP-46.md`, `STEP-47.md`, `STEP-48.md`, `STEP-49.md` all exist
  with Status: DONE. Verified 2026-09-30.
- Required sign-offs: none.

## 2. Verification runs (all fresh at gate time)

- Full Python regression (`py -3.13 scripts/test_all.py test-all`):
  **327 of 327 tests passed (100% green)**; secret scanner clean (0 findings).
  Ruff/mypy skipped by the runner (modules not installed locally;
  pre-existing environment condition).
- Eval (`eval.harness.runner --golden v1 --pipeline dummy`, default config):
  outcome PASS, 60/60 cases, all 8 metrics PASS
  (run `eval-v1-dummy-1790803985`).
- Frontend vitest: **24 of 24 passed** (all suites).
- Frontend Playwright e2e: **10 of 10 passed** (one 3D load test used its
  single configured retry under full-suite load; the 5 s bar held on every
  attempt — thresholds never lowered).
- `pnpm run build` (tsc + vite): PASS. `pnpm run lint` (oxlint): PASS (only
  pre-existing warnings in untouched files).

## 3. Metrics vs thresholds (`configs/thresholds.yaml`, ui section)

| Metric | Threshold | Measured | Comparison | Status |
| :--- | :--- | :--- | :--- | :--- |
| `ui.min_fps` | 50 | ≥ 50 sustained over 6 s sampling (SwiftShader software GL, reference machine per STEP-48 §5) | >= | PASS |
| `ui.max_load_s` | 5 | ~1.3–1.6 s scene load (e2e) | <= | PASS |
| `ui.max_sync_lag_ms` | 500 | Full-stream SSE delivery far below bar (Step-49 timing test, re-run green) | <= | PASS |
| `ui.output_divergence_count` | 0 | 0 divergences over 10 golden encounters UI-on vs UI-off (Step-49, re-run green) | <= | PASS |

## 4. Phase goals: evidence

| Phase goal | Evidence |
| :--- | :--- |
| Read-only event stream with replay and resume | `src/vh/events/stream.py`; 8 Step-46 tests (order, resume, unknown-cursor 404, no-write audit, speed math, live tail, bundle replay) |
| 2D dashboard driven only by events | `frontend/src/components/hospital/` + WARDS tab; 5 vitest + 2 Playwright e2e (exact replayed sequences, live parity) |
| 3D scene meeting performance targets | `frontend/src/components/hospital3d/` + HOSPITAL3D tab; 6 vitest + 3 Playwright e2e (load/fps/click-through); STEP-48 §5 reference machine + asset budget |
| Proven zero clinical side effects from the UI | 6 Step-49 integration tests (0 hash divergences, frozen state, static view-layer scan, lag bound) |

## 5. Sign-offs checked

None required for this gate.

## 6. Decision

**PASS.** Phase 8 is complete. Commit tagged `phase-8-pass`. Next: STEP 51 (P9.1).
