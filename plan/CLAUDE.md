# CLAUDE.md: standing instructions for the coding agent

> Place this file at the repository root. Claude Code loads it automatically. For other agents (Codex, Cursor, etc.) copy it as `AGENTS.md` or paste it at the start of each session.

## 1. Project

Virtual Hospital AI: synthetic patients (Synthea), Case Builder, multi-source RAG, MedGemma generation, verification, clinical report, doctor review, feedback store, periodic fine-tuning. Specialised agents operate in a simulated hospital, visualised in 2D and then 3D.

**Core principle: each layer has one job, and the jobs are never merged.**
- RAG is the source of medical knowledge.
- MedGemma is the generation engine.
- Verification is the checking layer.
- Doctor feedback is the source of learning.
- Fine-tuning improves format, reasoning style and evidence use. It is not for memorising books.

Full plan: `plan/README.md`. Current state of the codebase: `docs/current-state.md`.

## 2. The gate loop (every step, no exceptions)

1. Read the step prompt, this file, `docs/current-state.md` and the previous step report.
2. Write the step's acceptance criteria as tests first; confirm they fail.
3. Implement only what the step asks.
4. Run the full regression suite (`make test-all`; `make eval` when relevant).
5. For each failure: root cause, fix, a regression test that reproduces it, then re-run everything.
6. Gap review: every task bullet and criterion must map to a file or test. Anything unmet: back to 5.
7. Write `docs/steps/STEP-NN.md`. Status DONE only when everything passes.
8. Stop. Never begin the next step on your own.

A defect found later in an earlier phase reopens that phase's gate: fix it there, re-run that gate and every gate after it, in order (`plan/prompts/_templates/FIX-LOOP.md`).

## 3. Hard rules

- Never skip, weaken, xfail or delete a test to make a suite pass.
- Never edit `configs/thresholds.yaml`. Propose values in the step report; the project owner edits it.
- Never modify a released golden set (`eval/golden/vN/`). New content means a new version.
- Never mark anything as physician-verified, reviewed or signed off on your own judgement. Sign-offs are human-written files in `docs/signoffs/`; you may read them but never write or edit them. A status changes only through an import command (`vh golden import-signoff`, `vh golden chunkmap-import`, `vh safety import-signoff`) that applies exactly what the sign-off file lists.
- Synthetic data only. No real patient data anywhere: repo, fixtures, logs or prompts. No real identifiable images.
- Never invent a citation, reference, clinical code (LOINC, SNOMED CT, RxNorm) or source. If unsure, leave it empty and flag it.
- Agents and pipelines receive only `AgentView`. Only the environment and the evaluation scorers may read `CaseSpec.hidden` or `ground_truth`.
- Every LLM call goes through `src/vh/common/llm.py` with a prompt `name@version`.
- Every clinical claim carries `evidence_ids`. Verification fails closed.
- No clinical logic in the frontend or the 3D layer.
- No secrets in code, fixtures or logs. No live network calls inside `make test-all`; use recorded fixtures.
- Record every significant technical choice as an ADR in `docs/decisions/`.
- If something is ambiguous or blocked, stop with Status: BLOCKED and ask in the step report. Never guess on clinical content.

## 4. Conventions (defaults; ADR-0001 may override them to match existing code)

- Python 3.11+, type hints, ruff, mypy strict in `src/vh`, pytest markers: unit, integration, regression, eval, slow.
- FastAPI services; pydantic v2 models; pydantic-settings configuration; `.env.example` always complete.
- Postgres via docker compose; a migration for every schema change.
- Structured JSON logs with `run_id`; OpenTelemetry tracing.
- Versioned artifacts (datasets, indexes, prompt templates, models, golden and fault sets) via `src/vh/common/artifacts.py`.
- Frontend work uses the existing Clinical AI OS shell and its design tokens.

## 5. Where things go

See "Target repository layout" in `plan/README.md`. Step reports: `docs/steps/`. Phase gate reports: `docs/phase-reports/`. Sign-offs: `docs/signoffs/`. ADRs: `docs/decisions/`.
