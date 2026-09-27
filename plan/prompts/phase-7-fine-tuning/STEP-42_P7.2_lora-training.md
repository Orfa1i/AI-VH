# STEP 42 of 54 | P7.2: LoRA / QLoRA fine-tuning pipeline

- **Phase 7:** Fine-Tuning & Model Lifecycle
- **Run after:** STEP 41 (P7.1) report shows Status: DONE.
- **Next:** STEP 43 (P7.3): `plan/prompts/phase-7-fine-tuning/STEP-43_P7.3_model-registry.md`

> Read `CLAUDE.md`, `docs/current-state.md` (once it exists) and the previous step report before starting. Work only on this step.

## Context
Fine-tuning teaches format, reasoning style and evidence use. Medical knowledge stays in the RAG layer.

## Task
- First check that `docs/signoffs/H0.1-governance.md` confirms fine-tuning is permitted. If not, stop with Status: BLOCKED.
- LoRA / QLoRA SFT with PEFT/TRL on the production MedGemma variant (ADR-0004). Config-driven, fixed seeds; hardware and memory plan in ADR-0006.
- Log loss curves and validation loss; register the adapter as a `model` artifact at stage `candidate`, with lineage to the dataset and base model.

## Acceptance criteria (write these as tests first)
- CI smoke test trains a few steps on a tiny fixture and saves / reloads the adapter.
- The reloaded adapter produces schema-valid output on one fixture case.
- Lineage complete.

## Deliverables
- `src/vh/training/sft.py`, training config, ADR-0006
- `docs/steps/STEP-42.md`

## Execution rule (mandatory, see CLAUDE.md section 2)
1. Write the acceptance criteria above as tests first and confirm they fail.
2. Implement only what this step asks until they pass.
3. Run the full regression suite: `make test-all` (every phase so far), plus `make eval` if this step touches anything the harness measures.
4. For every failure: find the root cause, fix it, add a regression test that reproduces it, then re-run the full suite.
5. Gap review: go through every task bullet and acceptance criterion one by one and cite the file or test that satisfies it. Anything unmet means the step is not done: go back to 4.
6. Do not start any other step. Do not skip, weaken or delete tests. Do not edit `configs/thresholds.yaml`.
7. Only when everything passes, write the step report and stop.

## Step report: write to `docs/steps/STEP-42.md`
- **Status:** DONE | BLOCKED (reason)
- **Built:** files created or changed
- **Tests:** tests added; full-suite result (passed / total)
- **Failures found:** symptom, root cause, fix, regression test
- **Gap review:** each acceptance criterion, with the file or test that proves it
- **Open questions / assumptions:** must be empty, or explicitly accepted by the project owner before the next step
