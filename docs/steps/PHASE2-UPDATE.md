# Phase 2 Update Report — MedGemma Generation Settings, Schema & System Prompt

- **Status**: DONE (implementation + tests green). Phase 3 NOT started per instruction.
- **Scope**: `prompt FOR UPDATE/02_Phase2_*` only (+ owner conditions 1–6).
- **Date**: 2026-10-04
- **ADR**: `docs/decisions/ADR-0018-phase2-grounded-generation.md`

---

## 1. What changed (files touched)

| File | Owner | Change |
|---|---|---|
| `src/vh/generation/v2_report.py` (new) | AI Engineer | `AssessmentReport` schema (all §2 fields, evidence objects, prob-sum/confidence validators) |
| `src/vh/prompt_templates/internal_medicine_assessment/1.0.0.md` (new) | AI Engineer | Verbatim §3 system prompt (`[PLATFORM NAME]` → `AI Virtual Hospital (AI-VH)`) |
| `src/vh/prompt_templates/internal_medicine_differential/1.0.0.md` (new) | AI Engineer | Pass 1 candidate micro-call prompt |
| `src/vh/generation/flag.py` (new) | AI Engineer | `VH_PIPELINE` flag (default grounded; `legacy` rollback) |
| `src/vh/generation/medgemma.py` (v2 hunks) | AI Engineer | `Phase2GenerationConfig` (0.2 / 1.1 / 4096 / 2 retries), strict parse+retry, `box_2d` attempt-fail, raw capture, heuristic v2 |
| `src/vh/generation/pipeline.py` (grounded hunk) | AI Engineer | `run_grounded_assessment()` (two-pass → candidates → v2 → raw+log stored) |
| `src/vh/generation/compat.py` (new, TEMPORARY) | Software Engineer | v2 → legacy response fields (dies in Phase 4) |
| `backend/simulation/grounded_shim.py` (new) | Software Engineer | Flag-gated seam, fail-safe None → legacy |
| `backend/agents/specialists/internal_medicine.py` (step-5/8 hunk) | Software Engineer | Grounded decision + citations else unchanged legacy call |
| `tests/test_phase2_update_acceptance.py` (new, 19 tests) | QA Engineer | Schema, prompt, settings, parse/retry, raw, flag, compat, contracts, shim |
| `src/vh/generation/report.py`, legacy `run()`, `medgemma_service` | — | Untouched (deletion banned before Phase 6) |

## 2. Test results (final full-suite verification)

- New: **20/20 passed** (`tests/test_phase2_update_acceptance.py`, incl. CASE-101 routing regression test).
- Regression: Phase 1 **16/16** still green.
- Full backend: **365 passed** (`tests` + `backend/tests`, slow/eval deselected) + **7 passed** (`test_step_23/28`) = **372 passed, 0 failed**. Secret scan: clean.
- Frontend: **10 files, 39/39 vitest passed** (incl. new 503 test).
- Endpoints (TestClient): 15 GET endpoints 200, `POST /api/rl/train` **503** with Phase 5 detail, 7 slow routes asserted present.
- Charles Brown end-to-end (real semantic search, 14 queries, 24 chunks): `Community-acquired pneumonia`, prompt_version stored, 0 `box_2d`, raw stored, compat-mapped (0.5/0.25/0.15).
- Parse-failure rate (condition 4): clean-runner 0/1; adversarial-runner 1/1 FAILED after 3 attempts with raws stored.
- Rollout incident: flipping default to grounded broke 2 legacy encounter tests (offline heuristic mis-route); root cause fixed, default reverted to legacy pending Phase 3 parity proof. No test was weakened — full suite is green unmodified.

## 3. Condition answers

1. **Flag**: `VH_PIPELINE` default **legacy** (rollback = flag change). The default was briefly flipped to grounded after the 19 Phase 2 tests passed, then reverted on full-suite evidence: 2 legacy encounter tests failed (offline heuristic mis-routed CASE-101 on the word "dyspnoea"; root cause fixed, regression test added). Default flips to grounded only after Phase 3 proves parity. Shim fail-safes to legacy on any exception. Legacy paths untouched.
2. **Compat**: `compat.py` maps every frontend-required field (verified incl. likelihood ranges + for/against). Contract tests: 15 GET endpoints 200, `POST /api/rl/train` 503, 7 slow routes asserted present. Known gap → Phase 4: free-text `investigations_ordered`.
3. **Raw output**: `metadata["raw_model_output"]` (all attempts) + `parse_stats` on every generation.
4. **Constrained decoding**: NOT supported (no library installed/wired; `guided_decoding_available() is False` asserted). Strict parsing + retry used.
5. **Tokenizer**: `model_max_length` as configured = **512** (not 256; 256 is sentence-transformers' module default, our code truncates at 512). Chunks over 256: **19,011 (60.49%)**; over 512: **72 (0.23%)**, max 734. Self-consistent (build + query share 512); propose re-chunking the 72 outliers later.
6. **Push**: `phase1-case-extraction-retrieval` branch + `phase1-done` tag pushed to private `github.com/mohamadorfali2006/AI-VH` and verified via ls-remote.

## 4. How to test / rollback

```powershell
py -3.13 -m pytest tests/test_phase2_update_acceptance.py tests/test_phase1_update_acceptance.py -q
$env:VH_PIPELINE="legacy"   # rollback: pre-Phase-2 behavior, no code change
$env:VH_PIPELINE="grounded" # grounded assessment path
```

## 5. Open issues for owner

1. Phase 4 must replace `compat.py` with chip rendering (and resolve enum coercion).
2. 72 chunks exceed 512 tokens — re-chunk proposal for a later phase.
3. Live-model parse-failure rate to be measured on the 20-case set in Phase 3.
4. Retrieval validation labels still pending your review (no tuning done).
