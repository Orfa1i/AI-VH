# Project Handoff: AI Virtual Hospital (AI-VH)

## 1. Project Overview & Context
AI-VH is an autonomous multi-agent healthcare simulation platform designed to study whether autonomous medical AI agents (Doctors, Nurses, Patients, Labs) can improve clinical decision-making through expert physician feedback and reinforcement learning. The system is backed by local 4-bit quantized MedGemma running on an RTX 4060 GPU, medical textbook RAG (e.g. Harrison's Internal Medicine 21st Ed), an asynchronous event bus, and a structured physician review dashboard.

## 2. Accomplished So Far
- Extracted and systematized the 50-section specification from `Full-Idea.txt` into 14 dedicated architectural documents in `docs/`:
  - `00-INDEX.md`: Master index and core execution principle.
  - `01-vision-and-final-system.md`: Layered architecture and central research questions.
  - `02-virtual-hospital-3d.md`: 3D hospital scope (Three.js/R3F) vs backend simulation engine.
  - `03-agent-architecture.md`: Doctor (MedGemma), Nurse, Patient (dynamic hidden clinical states), and specialty configurations.
  - `04-medical-knowledge-rag.md`: Textbook ingestion, chunking metadata, and vector storage.
  - `05-clinical-workflow-and-tools.md`: ER workflow, clinical tool interfaces, structured messaging, and hospital event bus.
  - `06-data-architecture.md`: PostgreSQL schema, pgvector for RAG, and Obsidian for research documentation.
  - `07-clinical-reports-and-review.md`: Structured clinical report format, physician review UI, and structured feedback taxonomy.
  - `08-reinforcement-learning.md`: RL environment formulation, state/action/reward models, feedback-to-policy pipeline.
  - `09-evaluation-and-safety.md`: Diagnostic concordance metrics, safety bounds, and agent version benchmarks.
  - `10-backend-and-orchestration.md`: FastAPI, state machine, and separated memory tiers.
  - `11-frontend-architecture.md`: 3D hospital world vs Physician Review & Research Dashboard.
  - `12-project-folder-structure.md`: Comprehensive repository tree.
  - `13-roadmap-phases.md`: Phases 0 through 7.
- Verified hardware environment: NVIDIA GeForce RTX 4060 (8GB VRAM), CUDA active, Python 3.11 with Torch 2.6.0+cu124, Transformers, and BitsAndBytes 4-bit NF4 quantized MedGemma weights present locally.
- Configured `.gitignore` to protect multi-gigabyte model weights and PDF books while tracking code and architecture.
- Created `README.md` with system diagram, architecture breakdown, and phase tracker.

## 3. Key Decisions & Rationale
- **Clinical Simulation Loop First, 3D Later**: We strictly enforce building the Patient → Nurse → Doctor → Investigations → Diagnosis → Report → Review loop first before layering the 3D rendering world around it. This ensures the clinical AI intelligence and evaluation pipeline are robust.
- **Strict Memory Separation**: Patient memory (EHR / history / vitals), Agent episodic memory (encounter trace and previous feedback), and Knowledge memory (textbook chunks) are kept strictly segregated to prevent information leakage.
- **Structured Communication & Event Bus**: Agents communicate via typed events (`PATIENT_ARRIVED`, `VITALS_UPDATED`, `DIAGNOSIS_UPDATED`, etc.) and clinical tool calls rather than free-form chaotic chat.

## 4. Current State of the Work
- Phase 0 (Research & Architecture) is finalized and documented.
- Phase 1 (MVP: 1 Patient Agent + 1 Nurse Agent + 1 Doctor Agent + EHR + Clinical Report + Review) is queued for implementation.

## 5. Next Steps
1. Initialize git commit for Phase 0 documentation baseline.
2. Scaffold `backend/` directory structure (`simulation`, `agents`, `clinical`, `rag`, `api`).
3. Implement the Clinical Event Bus and State Machine.
4. Implement Patient Agent (with dynamic hidden clinical state and selective disclosure), Nurse Agent (triage, vitals intake), and Doctor Agent (tool-using clinical investigator).
5. Implement Clinical Tools (`get_vitals`, `order_lab_test`, `write_clinical_report`).
6. Wire end-to-end integration test running a full ER encounter through clinical report generation.
