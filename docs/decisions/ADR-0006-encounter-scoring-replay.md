# ADR-0006: Encounter Scoring Weights and Deterministic Replay Design

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-5-agents/STEP-34_P5.4_encounter-scoring-replay.md`, `configs/thresholds.yaml`

---

## 1. Context and Problem Statement

STEP 34 (P5.4) requires whole-encounter judging (diagnosis, workup, red flags,
time, verification, budget) plus deterministic replay (`vh replay <run_id>`)
that reproduces the event log exactly, and registration of the encounter
pipeline in the evaluation harness.

## 2. Decision

### 2.1 Composite encounter score (0-1)

`EncounterScorer` (`src/vh/agents/scoring.py`) computes eight axes and a
weighted composite:

| Axis | Weight | Definition |
| :--- | :--- | :--- |
| `dx_top1` | 0.35 | Top differential matches primary dx or acceptable differential |
| `dx_top3` | 0.20 | Any of top-3 differentials matches |
| `workup_recall` | 0.12 | Expected tests ordered / expected tests |
| `workup_precision` | 0.08 | Appropriate ordered / all ordered |
| `red_flags_addressed` | 0.08 | Red-flag phrases mentioned in report/history |
| `verification_score` | 0.07 | 1.0 iff verification status is `verified` and passed |
| `time_efficiency` | 0.05 | 1.0 at <= 60 sim-min, linear decay to 0 at 360 sim-min |
| `budget_efficiency` | 0.05 | 1 minus weighted step/token/cost/time fractions |

Diagnosis matching mirrors the `eval/harness/scorers/diagnostic.py` semantics
(normalization, substring, token overlap with substring tolerance) but is
self-contained in `src/vh/agents/scoring.py` so `src/` never depends on `eval/`.
Workup matching adds a small documented `WORKUP_ALIASES` panel/component map
(e.g. "Cardiac Enzymes" ~ troponin, ECG ~ electrocardiogram), same precedent.

Deliberate edge rules (avoid rewarding do-nothing encounters): empty ordered
workup with non-empty expected workup yields recall 0.0 and precision 0.0;
empty red-flag lists yield 1.0 (nothing to address).

### 2.2 Deterministic replay

`src/vh/agents/replay.py`: `RecordingAdapter` wraps `MedGemmaAdapter` and
records every generation output in call order; `ReplayAdapter` serves recorded
outputs back deterministically. `record_encounter` persists a `ReplayBundle`
(run_id, seed, transcript, event log, terminal state, canonical hash) to
`data/replays/` (gitignored generated artifacts). `replay_encounter`
re-executes with the same run_id/seed and transcript.

Canonical hashing (`hash_event_log`) compares actor, action, sim_time, payload
content, and result references, normalizing volatile identifiers
(`rep_/cns_/evt_/enc_/run_<hex>`) and excluding `event_id`, `wall_time`, and
`run_id` envelope fields, which carry no clinical content. Any clinical
divergence fails the comparison.

`HospitalOrchestrator.run_encounter` accepts optional `run_id`/`seed`/
`event_store` (defaults preserve prior behavior) so replay can observe the
same event stream. `vh replay <run_id>` is routed through `src/vh/cli.py`.

### 2.3 FIX-LOOP defect found in STEP 33 (fixed here, gate re-run)

The P5.3 workup scheduler filtered hidden diagnostics by LAB/DX code prefix,
silently ordering **zero** tests for golden v1 cases using natural order names
("Cardiac Enzymes", "ECG"), leaving every encounter with an empty workup and
all workup metrics at 0. Fixed in `src/vh/agents/orchestrator.py`: every
`HiddenResult` is orderable; routing is lab-like via `order_lab`,
imaging-like via `order_imaging` (category, code prefix, or imaging-name
heuristics), uncategorized items defaulting to `order_lab` since the
environment resolves orders by code-or-name either way. Regression test
`test_orders_natural_named_hidden_tests_regression` added to
`tests/test_step_33_acceptance.py`; the Step 33 suite (10 tests) was re-run
green before the Step 34 suite.

### 2.4 Harness registration

`eval/harness/encounter.py` provides `EncounterPipeline` (harness `Pipeline`
protocol; resolves the full `CaseSpec` from the frozen golden set, exposes
only `CaseView` to the caller path) and `EncounterHarnessScorer` (`Scorer`
protocol returning the aggregated encounter distribution).
`eval/harness/runner.py` supports `pipeline_name="encounter"`.

## 3. Measured Baseline (60 verified golden cases, seed 42)

60/60 encounters `completed`; 60/60 replays byte-identical on canonical hash
(0 mismatches). Score distribution: mean 0.3596, min 0.1644, max 0.9944;
dx_top1 0.1667, dx_top3 0.3333; workup recall 0.2403, precision 0.2667;
red-flags 0.25; verification pass 1.0. Low dx/workup values reflect the
deterministic heuristic generation baseline and golden naming gaps, not the
scorer: diagnostic uplift is Phase 7 fine-tuning work, per layer separation.

## 4. Consequences

- H5 proposal: `agents.encounter_score_min = 0.30` (below the current 0.36
  mean, above the floor; gates regressions without blocking Phase 5 on
  fine-tuning gains). The project owner sets the value; it is NOT written here.
- Replay bundles are reproducible generated artifacts and stay out of git.
