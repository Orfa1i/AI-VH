# ADR-0018: Phase 2 Grounded Generation (v2 schema, system prompt, flag)

- **Status**: Accepted (Phase 2 only)
- **Date**: 2026-10-04
- **Deciders**: Project Owner (conditions) & 5-agent workflow (implementation)
- **Governing Documents**: `prompt FOR UPDATE/02_Phase2_*`, owner conditions 1–6
- **Owner**: AI Engineer (schema/prompt/pipeline); Software Engineer (compat/shim)

---

## 1. File ownership (exclusive; no two agents edit the same file)

| File | Owner | Change |
|---|---|---|
| `src/vh/generation/v2_report.py` (new) | AI Engineer | Phase 2 `AssessmentReport` schema + validators |
| `src/vh/prompt_templates/internal_medicine_assessment/1.0.0.md` (new) | AI Engineer | Verbatim system prompt (§3), `[PLATFORM NAME]` → `AI Virtual Hospital (AI-VH)` |
| `src/vh/prompt_templates/internal_medicine_differential/1.0.0.md` (new) | AI Engineer | Pass 1 candidate micro-call prompt |
| `src/vh/generation/flag.py` (new) | AI Engineer | `VH_PIPELINE` flag, default grounded after tests pass |
| `src/vh/generation/medgemma.py` (v2 hunks) | AI Engineer | `Phase2GenerationConfig`, strict parse/retry, raw capture, heuristic v2 |
| `src/vh/generation/pipeline.py` (grounded hunk) | AI Engineer | `run_grounded_assessment()`; legacy `run()`/`run_with_log()` untouched |
| `src/vh/generation/compat.py` (new) | Software Engineer | TEMPORARY v2 → legacy response fields (removed in Phase 4) |
| `backend/simulation/grounded_shim.py` (new) | Software Engineer | Flag-gated seam; fail-safe None → legacy |
| `backend/agents/specialists/internal_medicine.py` (step-5/8 hunk) | Software Engineer | Grounded decision + citations, else legacy call unchanged |
| `tests/test_phase2_update_acceptance.py` + fixtures use | QA Engineer | 19 acceptance tests |
| `eval/retrieval_validation_v1/` (Phase 1 set) | Medical Expert (review pending) | Untouched by Phase 2 |

## 2. Constrained decoding: NOT supported (condition 4)

No constrained/grammar decoding library (outlines, guidance,
lm-format-enforcer or equivalent) is installed or wired anywhere in the repo;
both serving paths call `transformers` `generate()` directly (or an injected
runner). `guided_decoding_available()` returns `False` and tests assert it, so
the documented path cannot silently drift. All v2 generation uses strict JSON
parsing with retry (`extract_json_from_text` + pydantic validation, max 2
retries / 3 attempts). Measured parse-failure rate on scripted cases:
clean-runner **0/1 failed** (0 json + 0 schema failures, success on attempt 1);
adversarial-runner (unparseable every attempt) **1/1 failed after 3 attempts**
with `GenerationFailed` and all raw attempts stored. Live-model rate will be
measured in Phase 3 on the 20-case set.

## 3. Tokenizer length finding (condition 5)

- Tokenizer `model_max_length` **as configured is 512** (both `backend/rag/vector_embedder.py`
  and `vh/rag/indexing.py` pass `max_length=512`; model has 512 positions). The
  owner's 256 figure is sentence-transformers' `max_seq_length` default in their
  pooling modules — our code calls the tokenizer directly, so effective truncation is 512.
- Chunk token census (31,427 texts, counted without truncation): min 43, max 734,
  mean 265.1. **Exceeding 256: 19,011 (60.49%). Exceeding 512: 72 (0.23%).**
- Consequence: embeddings (built with max_length=512) and queries share identical
  truncation, so retrieval is self-consistent; only 72 chunks lose tail content.
  No action in Phase 2; proposal: re-chunk the 72 outliers (>512) in a later phase.

## 4. Flag and rollout (condition 1)

- `VH_PIPELINE=legacy|grounded`, default **legacy**. Rollback is `VH_PIPELINE=legacy` — a flag change only.
- The default was briefly flipped to grounded after the 19 Phase 2 tests passed,
  then **reverted on full-suite evidence**: with grounded default, 2 legacy
  encounter tests failed (`test_specialist_in_hospital_encounter`,
  `test_clinical_simulation_end_to_end`: CASE-101 NSTEMI mis-routed to
  community-acquired pneumonia by the offline heuristic fallback, which keys off
  the word "dyspnoea" in the HPI). Root cause fixed in the fallback (cardiac
  red flags route first; isolated dyspnoea no longer triggers a respiratory
  shortlist; regression test added). The default still flips to grounded only
  after Phase 3 proves grounded parity on the benchmark — never by weakening
  the legacy tests.
- The grounded shim fail-safes to legacy on ANY grounded-path exception, so even
  with the flag set, a broken grounded call cannot take down encounters.
- Legacy `run()`, `generate_clinical_decision()` and `medgemma_service` paths are
  byte-untouched and survive until at least Phase 6.

## 5. Backward compatibility (condition 2)

- Existing frontend keeps working: grounded decisions map onto the exact legacy
  `decision` dict keys; citations keep `{id, book, chapter, topic, page, specialty,
  text}` shapes; all pre-existing routes respond (contract tests).
- `compat.py` is explicitly temporary and dies in Phase 4. Known gap carried to
  Phase 4: `investigations_ordered` stays free-text (backend `LabTestType` enum
  cannot be coerced without inventing mappings).

## 6. Raw-output provenance (condition 3)

- Every generation stores all raw attempts: `AssessmentResult.raw_attempts` →
  `PipelineResult.metadata["raw_model_output"]` (+ `parse_stats`). Phase 3 retries
  consume these verbatim; nothing is re-generated from memory.

## 7. Generation settings applied

`temperature=0.2`, `repetition_penalty=1.1` (passed to live-model generate calls;
heuristic path is deterministic), `max_new_tokens=4096`, text-only (no image
inputs anywhere on this path), `box_2d`/coordinate/code-fence output fails the
attempt with retry feedback, chunks passed as `<harrison_chunk id chapter page>`
tags, `prompt_version` stored on every report.
