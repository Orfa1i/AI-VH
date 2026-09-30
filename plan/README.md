# Virtual Hospital AI: Phased Development Plan

A 3D AI-powered virtual hospital where specialised medical agents work through synthetic patients, reason over trusted medical knowledge, produce evidence-linked clinical reports, pass automated verification, and improve through structured feedback from real doctors.

**Core principle:** RAG is the knowledge source, MedGemma is the generation engine, Verification is the checking layer, Doctor Feedback is the learning source, and Fine-tuning is how the model improves. Each has its own job and its own phase.

## How to use this pack

**One-time setup**
- Copy this folder into your repository as `plan/`.
- Move `plan/CLAUDE.md` to the repository root. Claude Code reads it automatically; for other agents rename it `AGENTS.md` or paste it at the start of each session.
- Decide the three golden-set specialties before STEP 05 (defaults: ACS, community-acquired pneumonia, DKA).

**For every step**
- Start a fresh agent session at the repository root.
- Paste the step file's full contents, or tell the agent: `Read and execute plan/prompts/<phase>/STEP-NN_....md`.
- Let the agent complete the loop: tests first, implement, full regression, fix, re-test, gap review, step report.
- Read `docs/steps/STEP-NN.md`. Continue only if Status is DONE and the open-questions list is empty (or you have accepted each item).
- Tick the box in the execution order below.

**At every gate**
- PASS: the agent tags `phase-N-pass`; move to the next phase.
- FAIL: paste `prompts/_templates/FIX-LOOP.md` together with the gate report, then run the same gate prompt again. Repeat until PASS.

**Human checkpoints ([HUMAN])** are things only you or a physician can do. The agent will not mark them done; it only checks that the sign-off file exists. Use `prompts/_templates/SIGNOFF.md`.

## Pack structure

```
plan/
├── README.md
├── CLAUDE.md                 → move to repo root
└── prompts/
    ├── _templates/
    │   ├── FIX-LOOP.md
    │   └── SIGNOFF.md
    ├── phase-0-foundations/
    ├── phase-1-synthetic-patients/
    ├── phase-2-rag/
    ├── phase-3-generation/
    ├── phase-4-verification/
    ├── phase-5-agents/
    ├── phase-6-feedback/
    ├── phase-7-fine-tuning/
    ├── phase-8-virtual-hospital/
    └── phase-9-advanced/
```

## Target repository layout

```
<repo>/
├── CLAUDE.md                  standing rules for the agent (from this pack)
├── plan/                      this pack: README, prompts, templates
├── src/vh/
│   ├── common/                config, logging, tracing, artifacts, LLM wrapper
│   ├── golden/                golden-set authoring CLI
│   ├── synthea/               Synthea wrapper
│   ├── cases/                 patient repo, CaseSpec/AgentView, builder, validation
│   ├── rag/                   sources, chunking, indexing, retrieval (kg/ later)
│   ├── generation/            report schema, MedGemma adapter, pipeline
│   ├── verification/          rules, grounding judge, guardrails, router
│   ├── agents/                environment, roles, orchestrator, scoring, tools
│   ├── feedback/              data model, review API, agreement, snapshots
│   ├── training/              curation, SFT, DPO, registry
│   ├── events/                read-only event stream
│   └── prompt_templates/      versioned LLM prompts (name/version.md)
├── web/                       existing Clinical AI OS shell (review UI, dashboard, 3D)
├── synthea/modules/custom/    custom Synthea modules + clinical assumptions
├── configs/                   thresholds.yaml, safety/, agents/, feedback/, leakage_terms/
├── schemas/                   exported JSON Schemas
├── eval/                      schema/, golden/, harness/, faults/, reports/
├── tests/                     unit/, integration/, regression/
├── docs/                      current-state.md, decisions/, steps/, phase-reports/, signoffs/
├── data/                      (gitignored) generated data, sources, indexes
└── Makefile, pyproject.toml, docker-compose.yml, .env.example, .github/workflows/
```
If your existing code lives elsewhere, ADR-0001 (STEP 01–02) maps it onto this layout instead of moving working code unnecessarily.

## The gate rule

- Acceptance criteria are written as tests before implementation.
- Every step ends with the full regression suite of all phases so far, not just its own tests.
- Every failure gets a root cause, a fix, and a regression test; then everything re-runs.
- A gap review maps every goal to evidence; an unmet goal is a failure.
- A phase starts only after the previous phase's gate reports PASS.
- A defect found later in an earlier phase reopens that phase's gate, and every later gate re-runs in order.
- Thresholds live in `configs/thresholds.yaml`. They start provisional; only you edit them. A `null` threshold fails its gate until you set it.

## Phases

**Phase 0: Foundations, Governance & Evaluation Harness**
- Purpose: Build the testing, tracing and versioning infrastructure every later gate depends on.
- Repository layout applied; CI blocks merges on any failure.
- Secrets scanning active locally and in CI.
- Tracing with run_id and versioned artifacts working.
- Evaluation harness working; golden set v1 released and frozen.
- Governance sign-off recorded.

**Phase 1: Synthetic Patients & Case Builder**
- Purpose: Produce realistic, reproducible clinical cases with hidden ground truth that agents can never see.
- Reproducible Synthea generation with valid FHIR output.
- Custom modules only where built-ins were insufficient, clinically documented.
- Patient store loaded idempotently and queryable.
- AgentView isolation proven; zero leakage.
- Case Builder deterministic, consistent and plausible; physician spot-check passed.

**Phase 2: Multi-Source RAG**
- Purpose: Reliable, licence-checked, traceable retrieval across all knowledge sources.
- All sources ingested through licence-checked adapters; NABD still works.
- Structure-aware chunks, each traceable to exact source text.
- Versioned dense + keyword indexes; superseded content excluded.
- Unified hybrid retrieval API with diversity and filters.
- Retrieval configuration chosen by measurement (ADR-0003).

**Phase 3: Grounded Clinical Generation (MedGemma)**
- Purpose: MedGemma produces structured reports built only from retrieved evidence, and abstains when evidence is insufficient.
- Report schema enforces claim-evidence links and referential integrity.
- MedGemma adapter with constrained output and no partial reports.
- Grounded pipeline with working abstention and zero fabricated citations.
- RAG proven better than no-RAG; production variant chosen (ADR-0004).

**Phase 4: Verification Layer**
- Purpose: Catch unsupported, inconsistent or unsafe output before anyone relies on it.
- Deterministic safety rules with physician-reviewed tables.
- Grounding judge calibrated against physician labels.
- Runtime guardrails that fail closed; verified/flagged routing with reasons.
- DeepEval metrics enforced in CI.
- Fault-injection suite proves detection without excessive false flags.

**Phase 5: Agents & Orchestration (headless)**
- Purpose: Specialised agents working through a simulated hospital as text and events, with no graphics yet.
- Environment releases hidden data only via orders; never invents data.
- Five specialised agents with tool-layer permissions.
- Orchestrator with budgets, loop detection and explicit termination states.
- Encounter scoring and exact replay.

**Phase 6: Doctor Review & Feedback Store**
- Purpose: Capture structured expert corrections without ever losing the original AI output.
- Original AI reports provably immutable; edits reconstruct finals exactly.
- Review API with authorisation and independent overlap reviews.
- Review UI in the existing shell, tested end-to-end.
- Agreement measured; versioned snapshots are the only training input.
- Doctor usability test passed.

**Phase 7: Fine-Tuning & Model Lifecycle**
- Purpose: Improve MedGemma from curated feedback; production changes only through evidence-gated promotion.
- Curated dataset split by patient, zero contamination.
- Reproducible LoRA fine-tuning with full lineage.
- Registry with evidence-gated promotion, shadow mode and rollback.
- Candidate beats production with zero safety regressions and blinded physician preference.

**Phase 8: Virtual Hospital Environment (2D then 3D)**
- Purpose: A visual hospital driven entirely by the event log, with proven zero clinical side effects.
- Read-only event stream with replay and resume.
- 2D dashboard driven only by events.
- 3D scene meeting performance targets.
- Proven zero clinical side effects from the UI.

**Phase 9: Advanced Intelligence**
- Purpose: Extend capability once the core is proven. Each item carries its own mini-gate.
- Imaging models as Radiology agent tools (mini-gate)
- Knowledge graph experiment (mini-gate)
- Preference optimisation (DPO) (mini-gate)
- New agent / department scaffold (mini-gate)

## Execution order

54 agent steps plus human checkpoints. Follow strictly top to bottom.

### Phase 0: Foundations, Governance & Evaluation Harness

- [x] STEP 01: P0.1 Repository audit (read-only) → `prompts/phase-0-foundations/STEP-01_P0.1_repo-audit.md`
- [x] STEP 02: P0.2 Project skeleton, configuration, CI → `prompts/phase-0-foundations/STEP-02_P0.2_skeleton-config-ci.md`
- [x] STEP 03: P0.3 Observability and artifact versioning → `prompts/phase-0-foundations/STEP-03_P0.3_observability-versioning.md`
- [x] STEP 04: P0.4 Evaluation harness and frozen golden-set mechanism → `prompts/phase-0-foundations/STEP-04_P0.4_evaluation-harness.md`
- [x] STEP 05: P0.5 Golden-set authoring tools and draft seed cases → `prompts/phase-0-foundations/STEP-05_P0.5_golden-set-authoring.md`
- [x] **[HUMAN] H0.1: Governance check** → `docs/signoffs/H0.1-governance.md`  
  Confirm and record: MedGemma licence terms (Health AI Developer Foundations) permit your intended use and fine-tuning; licences for any textbook you plan to index; whether SFDA software-as-a-medical-device rules apply to your intended use; ethics/IRB plan before real clinicians review outputs.
- [x] **[HUMAN] H0.2: Physician sign-off of golden set v1** → `docs/signoffs/golden-v1.md`  
  A physician reviews the golden-v1 packet, corrects or rejects cases, and lists approved case ids. Then ask the agent to run `vh golden import-signoff` and `vh golden release --version 1`. You need at least `golden.min_verified_cases` verified cases.
- [x] **STEP 06: P0.G Phase 0 GATE** → `prompts/phase-0-foundations/STEP-06_P0.G_gate.md`

### Phase 1: Synthetic Patients & Case Builder

- [x] STEP 07: P1.1 Synthea runner (reproducible FHIR export) → `prompts/phase-1-synthetic-patients/STEP-07_P1.1_synthea-runner.md`
- [x] STEP 08: P1.2 Custom Synthea modules for target specialties → `prompts/phase-1-synthetic-patients/STEP-08_P1.2_synthea-custom-modules.md`
- [x] STEP 09: P1.3 Patient store and FHIR loader → `prompts/phase-1-synthetic-patients/STEP-09_P1.3_patient-store.md`
- [x] STEP 10: P1.4 Case spec schema and AgentView isolation → `prompts/phase-1-synthetic-patients/STEP-10_P1.4_case-spec-schema.md`
- [x] STEP 11: P1.5 Case Builder → `prompts/phase-1-synthetic-patients/STEP-11_P1.5_case-builder.md`
- [x] STEP 12: P1.6 Case validation suite and spot-check packet → `prompts/phase-1-synthetic-patients/STEP-12_P1.6_case-validation-suite.md`
- [x] **[HUMAN] H1: Physician spot-check of 50 cases + custom-module assumptions** → `docs/signoffs/H1-spotcheck.md`  
  A physician reviews the spot-check packet and `synthea/modules/custom/README.md`, records the defect rate and any required fixes. Defect rate must be at or below `cases.spotcheck_defect_rate_max`.
- [x] **STEP 13: P1.G Phase 1 GATE** → `prompts/phase-1-synthetic-patients/STEP-13_P1.G_gate.md`

### Phase 2: Multi-Source RAG

- [x] STEP 14: P2.1 Source adapters (refactor knowledge_sources.py) → `prompts/phase-2-rag/STEP-14_P2.1_source-adapters.md`
- [x] STEP 15: P2.2 Structure-aware chunking → `prompts/phase-2-rag/STEP-15_P2.2_chunking.md`
- [x] STEP 16: P2.3 Dense + keyword indexing with versioned indexes → `prompts/phase-2-rag/STEP-16_P2.3_indexing.md`
- [x] STEP 17: P2.4 Unified hybrid retrieval API → `prompts/phase-2-rag/STEP-17_P2.4_retrieval-api.md`
- [x] STEP 18: P2.5 Retrieval evaluation and configuration choice → `prompts/phase-2-rag/STEP-18_P2.5_retrieval-evaluation.md`
- [x] **[HUMAN] H2: Confirm golden-set chunk mapping** → `docs/signoffs/H2-chunkmap.md`  
  Check that each mapped chunk genuinely contains the supporting evidence for its golden case (you can do this yourself; no physician needed). List corrections, then have the agent apply them and re-run STEP 18's evaluation.
- [x] **STEP 19: P2.G Phase 2 GATE** → `prompts/phase-2-rag/STEP-19_P2.G_gate.md`

### Phase 3: Grounded Clinical Generation (MedGemma)

- [x] STEP 20: P3.1 Clinical report schema with claim-evidence links → `prompts/phase-3-generation/STEP-20_P3.1_report-schema.md`
- [x] STEP 21: P3.2 MedGemma adapter → `prompts/phase-3-generation/STEP-21_P3.2_medgemma-adapter.md`
- [x] STEP 22: P3.3 Grounded generation pipeline with abstention → `prompts/phase-3-generation/STEP-22_P3.3_grounded-pipeline.md`
- [x] STEP 23: P3.4 Model benchmark and no-RAG baseline → `prompts/phase-3-generation/STEP-23_P3.4_model-benchmark.md`
- [x] **[HUMAN] H3: Set the diagnostic accuracy threshold** → `configs/thresholds.yaml`  
  Read the STEP 23 benchmark and set `generation.dx_top3_min` yourself (the gate fails while it is null).
- [x] **STEP 24: P3.G Phase 3 GATE** → `prompts/phase-3-generation/STEP-24_P3.G_gate.md`

### Phase 4: Verification Layer

- [x] STEP 25: P4.1 Deterministic safety rules engine → `prompts/phase-4-verification/STEP-25_P4.1_safety-rules-engine.md`
- [x] STEP 26: P4.2 Claim grounding and citation checker → `prompts/phase-4-verification/STEP-26_P4.2_grounding-checker.md`
- [x] STEP 27: P4.3 Runtime guardrails and verified/flagged routing → `prompts/phase-4-verification/STEP-27_P4.3_guardrails-routing.md`
- [x] STEP 28: P4.4 DeepEval metrics in CI → `prompts/phase-4-verification/STEP-28_P4.4_deepeval-ci.md`
- [x] STEP 29: P4.5 Fault-injection suite → `prompts/phase-4-verification/STEP-29_P4.5_fault-injection.md`
- [x] **[HUMAN] H4: Physician review of safety tables + judge calibration labels** → `docs/signoffs/H4-safety-and-judge.md`  
  A physician reviews every row in `configs/safety/` (approve or correct) and labels the 100 claim-evidence pairs in the calibration sheet (saved as `docs/signoffs/H4-judge-labels.csv`). Then have the agent mark approved rows as reviewed and run `vh verify calibration-score`.
- [x] **STEP 30: P4.G Phase 4 GATE** → `prompts/phase-4-verification/STEP-30_P4.G_gate.md`

### Phase 5: Agents & Orchestration (headless)

- [x] STEP 31: P5.1 Hospital environment simulator and event log → `prompts/phase-5-agents/STEP-31_P5.1_environment-simulator.md`
- [x] STEP 32: P5.2 Specialised agents and tool permissions → `prompts/phase-5-agents/STEP-32_P5.2_agents-permissions.md`
- [x] STEP 33: P5.3 Orchestrator, budgets and loop detection → `prompts/phase-5-agents/STEP-33_P5.3_orchestrator.md`
- [x] STEP 34: P5.4 Encounter scoring and deterministic replay → `prompts/phase-5-agents/STEP-34_P5.4_encounter-scoring-replay.md`
- [ ] **[HUMAN] H5: Set the encounter score threshold** → `configs/thresholds.yaml`  
  Read the STEP 34 results and set `agents.encounter_score_min` yourself (the gate fails while it is null).
- [x] **STEP 35: P5.G Phase 5 GATE** → `prompts/phase-5-agents/STEP-35_P5.G_gate.md`

### Phase 6: Doctor Review & Feedback Store

- [ ] STEP 36: P6.1 Feedback data model (append-only) → `prompts/phase-6-feedback/STEP-36_P6.1_feedback-data-model.md`
- [ ] STEP 37: P6.2 Review API with overlap sampling → `prompts/phase-6-feedback/STEP-37_P6.2_review-api.md`
- [ ] STEP 38: P6.3 Doctor review UI in the Clinical AI OS shell → `prompts/phase-6-feedback/STEP-38_P6.3_review-ui.md`
- [ ] STEP 39: P6.4 Reviewer agreement and feedback snapshots → `prompts/phase-6-feedback/STEP-39_P6.4_agreement-and-snapshots.md`
- [ ] **[HUMAN] H6: Usability test with 2-3 doctors** → `docs/signoffs/H6-usability.md`  
  Two or three doctors review real generated reports in the UI. Record findings, marking must-fix items. Must-fix items go through the FIX LOOP before you sign off.
- [ ] **STEP 40: P6.G Phase 6 GATE** → `prompts/phase-6-feedback/STEP-40_P6.G_gate.md`

### Phase 7: Fine-Tuning & Model Lifecycle

- [ ] STEP 41: P7.1 Training dataset curation → `prompts/phase-7-fine-tuning/STEP-41_P7.1_dataset-curation.md`
- [ ] STEP 42: P7.2 LoRA / QLoRA fine-tuning pipeline → `prompts/phase-7-fine-tuning/STEP-42_P7.2_lora-training.md`
- [ ] STEP 43: P7.3 Model registry, shadow mode and rollback → `prompts/phase-7-fine-tuning/STEP-43_P7.3_model-registry.md`
- [ ] STEP 44: P7.4 Candidate evaluation and blinded review packet → `prompts/phase-7-fine-tuning/STEP-44_P7.4_candidate-evaluation.md`
- [ ] **[HUMAN] H7: Blinded physician comparison** → `docs/signoffs/H7-blinded-review.md`  
  A physician compares the A/B reports without the key and records a preference per case. Unblind afterwards; the candidate must be preferred overall to pass.
- [ ] **STEP 45: P7.G Phase 7 GATE** → `prompts/phase-7-fine-tuning/STEP-45_P7.G_gate.md`

### Phase 8: Virtual Hospital Environment (2D then 3D)

- [ ] STEP 46: P8.1 Read-only event stream API → `prompts/phase-8-virtual-hospital/STEP-46_P8.1_event-stream-api.md`
- [ ] STEP 47: P8.2 2D department dashboard → `prompts/phase-8-virtual-hospital/STEP-47_P8.2_dashboard-2d.md`
- [ ] STEP 48: P8.3 3D hospital scene → `prompts/phase-8-virtual-hospital/STEP-48_P8.3_scene-3d.md`
- [ ] STEP 49: P8.4 UI integration and no-side-effect proof → `prompts/phase-8-virtual-hospital/STEP-49_P8.4_ui-integration-tests.md`
- [ ] **STEP 50: P8.G Phase 8 GATE** → `prompts/phase-8-virtual-hospital/STEP-50_P8.G_gate.md`

### Phase 9: Advanced Intelligence

- [ ] STEP 51: P9.1 Imaging models as Radiology agent tools → `prompts/phase-9-advanced/STEP-51_P9.1_imaging-tools.md`
- [ ] STEP 52: P9.2 Knowledge graph experiment → `prompts/phase-9-advanced/STEP-52_P9.2_knowledge-graph.md`
- [ ] STEP 53: P9.3 Preference optimisation (DPO) → `prompts/phase-9-advanced/STEP-53_P9.3_preference-optimization.md`
- [ ] STEP 54: P9.4 New agent / department scaffold → `prompts/phase-9-advanced/STEP-54_P9.4_new-agent-template.md`

## Decisions only you make

- Golden-set specialties (before STEP 05).
- `generation.dx_top3_min` (H3) and `agents.encounter_score_min` (H5), set from measured baselines.
- Any change to a provisional threshold. Change thresholds only for a documented reason, never to make a failing gate pass.
- When Phase 7 starts: STEP 41 stops as BLOCKED until `training.min_reviewed_cases` reviewed cases exist. Waiting for data is not a failure. While you wait, you may choose to run Phase 8, which depends only on Phase 5's event log; the default order stays strictly sequential.
- Before real doctors review outputs, and before any deployment, confirm the governance items in H0.1 are still valid.
