# STEP 02 of 54 | P0.2: Project skeleton, configuration, CI

- **Phase 0:** Foundations, Governance & Evaluation Harness
- **Run after:** STEP 01 (P0.1) report shows Status: DONE.
- **Next:** STEP 03 (P0.3): `plan/prompts/phase-0-foundations/STEP-03_P0.3_observability-versioning.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
ADR-0001 was proposed in the previous step. Default stack, unless `docs/current-state.md` shows an existing choice (then keep the existing one and note it in the ADR): Python 3.11+, FastAPI, pydantic v2 + pydantic-settings, pytest, ruff, mypy, Postgres via docker compose, GitHub Actions.

## Task
- Apply ADR-0001: create the new directories; move existing code only where the ADR says so, and keep existing apps running. Mark the ADR Accepted.
- `pyproject.toml` with ruff, mypy (strict for `src/vh`), pytest config and markers: unit, integration, regression, eval, slow.
- Configuration via pydantic-settings; `.env.example` listing every variable; `.env` gitignored.
- Secret scanning as a pre-commit hook (gitleaks or detect-secrets) and the same check in CI.
- Makefile targets: `lint`, `typecheck`, `test-unit`, `test-integration`, `test-regression`, `eval`, `test-all` (= lint + typecheck + all tests), `up` / `down` (docker compose).
- CI workflow running `make test-all` on every push and PR; merges blocked on failure.
- Create `configs/thresholds.yaml` with exactly the values below, plus a loader that raises on a missing key and reports `null` as NOT SET (a gate using a NOT SET value fails).
- Smoke tests proving the existing MedGemma service and frontend still start.

```yaml
# PROVISIONAL starting values. Only the project owner edits this file.
# null = not yet set -> any gate that uses it FAILS until it is set.
golden:
  min_verified_cases: 50
cases:
  fhir_valid_rate: 1.0
  leakage_count: 0
  plausibility_pass_rate: 1.0
  spotcheck_defect_rate_max: 0.05
retrieval:
  recall_at_10: 0.85
  mrr_min: 0.60
  traceability_rate: 1.0
  stale_retrieval_count: 0
  p95_latency_s: 1.5
generation:
  schema_valid_rate: 1.0
  fabricated_citation_rate: 0.0
  abstention_correct_rate: 0.90
  dx_top3_min: null
  rag_beats_baseline: true
verification:
  critical_fault_detection: 1.0
  noncritical_fault_detection: 0.90
  false_flag_rate_max: 0.10
  judge_kappa_min: 0.70
  faithfulness_min: 0.90
  contextual_relevancy_min: 0.80
  p95_latency_s: 5.0
agents:
  permission_violations: 0
  runaway_loops: 0
  replay_mismatch_count: 0
  encounter_score_min: null
review:
  kappa_min: 0.60
  overlap_fraction: 0.15
training:
  min_reviewed_cases: 500
  safety_regressions: 0
  must_beat_production: true
  min_preference_pairs: null   # set before STEP 53 (P9.3)
ui:
  min_fps: 50
  max_load_s: 5
  max_sync_lag_ms: 500
  output_divergence_count: 0
```

## Acceptance criteria (write these as tests first)
- `make test-all` passes on a clean clone.
- A deliberately failing test makes CI fail (demonstrate on a throwaway branch, then delete it).
- A planted fake key in a test fixture is caught by the secret scanner.
- Thresholds loader: missing key raises; `null` is reported as NOT SET.
- Smoke tests for the existing apps pass.

## Deliverables
- Directory layout, `pyproject.toml`, `Makefile`, `docker-compose.yml`, `.env.example`, CI workflow
- `configs/thresholds.yaml` + loader in `src/vh/common/`
- ADR-0001 marked Accepted
- `docs/steps/STEP-02.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-02.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
