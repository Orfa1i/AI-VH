# Current State Audit: AI Virtual Hospital (AI-VH)

**Audit Date**: 2026-09-28  
**Auditor**: Antigravity (Advanced Agentic Coding Assistant)  
**Governing Plan**: `plan/README.md` (Step 01 / P0.1)  
**Audit Scope**: Read-only codebase inspection of architecture, runtimes, dependencies, models, data stores, tests, and security posture.

---

## 1. Executive Summary

The AI-VH repository hosts a functional autonomous multi-agent clinical simulation and reinforcement learning platform. It comprises:
1. A **FastAPI** backend runtime (`backend/main.py:22-26`) with event-driven simulation orchestration (`backend/simulation/orchestrator.py:20-65`), 6 specialized clinical agents (`backend/agents/`), clinical decision tools (`backend/clinical/`), and SQLite database persistence (`backend/database/repository.py:15-45`).
2. An **on-device MedGemma 4-bit NF4 foundation model engine** (`backend/llm/medgemma_service.py:22-76`) running on a local NVIDIA GeForce RTX 4060 GPU (8 GB VRAM), augmented with a trained DPO LoRA adapter (`models/medgemma-dpo-lora/`).
3. A **Harrison's 21st Edition Medical Knowledge Vector RAG subsystem** (`backend/rag/` and `data/knowledge/`) containing 47,806 dense text chunks and 768-dimensional embeddings (`data/knowledge/harrison_embeddings.npy`).
4. A **Reinforcement Learning from Physician Feedback (RL / DPO) subsystem** (`backend/rl/`) with clinical reward scoring (`backend/rl/reward_model.py:15-60`), pair generation (`backend/rl/dpo_generator.py:20-80`), policy benchmarking (`backend/rl/evaluator.py:15-55`), and LoRA training scripts (`backend/rl/train_dpo.py:20-75`).
5. A **React 19 + TypeScript + Tailwind CSS 4 web portal shell** (`frontend/src/App.tsx:36-120`) styled in high-contrast clinical light mode (`frontend/src/index.css:1-60`), featuring an interactive 2D Patient Journey Graph (`frontend/src/components/diagram/PatientJourneyFlowPage.tsx:1-95`), telemetry HUDs, and physician review dashboards.
6. A **67-test automated test suite** (`backend/tests/`) passing 100% via `pytest`.

---

## 2. Technology Inventory

### 2.1 Languages and Frameworks
- **Python**: Version 3.13.5 (`py -3.13`)
  - Web Framework: FastAPI 0.139.2 (`pip list`), Starlette 1.3.1, Uvicorn 0.51.0
  - Data Validation & Settings: Pydantic 2.13.4, Pydantic-Settings 2.15.0
  - Deep Learning & Inference: PyTorch 2.6.0+cu124, Torchvision 0.21.0+cu124, BitsAndBytes (4-bit NF4)
  - NLP & Model Tuning: HuggingFace Transformers 5.17.0, PEFT 0.20.0, TRL 1.13.0, Tokenizers 0.23.1, Safetensors 0.8.0
  - Scientific Computing: NumPy 2.4.4, SciPy 1.18.0, Pandas 3.0.2, Scikit-Learn 1.9.0
  - Database & Storage: SQLite3 (built-in standard library), DuckDB 1.5.5, Psycopg2-binary 2.9.12
  - Testing: Pytest 9.0.2, Pytest-Asyncio 1.4.0, Hypothesis 6.156.6
- **Frontend / JavaScript Runtime**: Node.js v22
  - Core Library: React 19.2.8 (`frontend/package.json:16`), React-DOM 19.2.8
  - Language: TypeScript 6.0.2 (`frontend/package.json:27`)
  - Build Tool & Bundler: Vite 8.3.0 (`frontend/package.json:28`)
  - Styling: Tailwind CSS 4.3.3 (`frontend/package.json:19`), `@tailwindcss/vite` 4.3.3
  - Iconography: Lucide React 1.45.0 (`frontend/package.json:15`)
  - Linter: Oxlint 1.81.0 (`frontend/package.json:26`)

### 2.2 Entry Points and Operational Commands
- **Backend API & WebSockets**:
  - Entry point: `backend/main.py:22`
  - Run command: `py -3.13 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
- **Frontend Development Server**:
  - Entry point: `frontend/src/main.tsx:1-12`
  - Run command: `pnpm run dev` (executed inside `frontend/`, binds to `http://localhost:5173`)
- **Frontend Production Build**:
  - Script: `frontend/package.json:8` (`tsc -b && vite build`)
  - Run command: `pnpm run build` (executed inside `frontend/`, bundles to `frontend/dist/`)
- **Backend Automated Test Suite**:
  - Directory: `backend/tests/`
  - Run command: `py -3.13 -m pytest backend/tests`
- **Offline Textbook Ingestion & Embedding**:
  - Full Harrison's embedder: `backend/rag/full_book_embedder.py:20-60`
  - Run command: `py -3.13 -m backend.rag.full_book_embedder`
  - Specialty Braunwald embedder: `backend/rag/specialty_book_embedder.py:20-60`
  - Run command: `py -3.13 -m backend.rag.specialty_book_embedder`
- **DPO LoRA Training Script**:
  - Entry point: `backend/rl/train_dpo.py:15-80`
  - Run command: `py -3.13 -m backend.rl.train_dpo`

---

## 3. Subsystem Deep-Dive

### 3.1 MedGemma Foundation Model Service
- **Model Variant**: Gemma-based medical foundation model stored locally at `MedGemma Model/model/` (`backend/llm/medgemma_service.py:18`).
- **Quantization & Runtime**: Configured in 4-bit NF4 format with `bfloat16` compute type using `BitsAndBytesConfig` (`backend/llm/medgemma_service.py:57-61`). Loaded via `AutoModelForImageTextToText` and `AutoProcessor` (`backend/llm/medgemma_service.py:62-67`).
- **LoRA Adapter**: Trained Direct Preference Optimization (DPO) LoRA weights stored at `models/medgemma-dpo-lora/` (`backend/llm/medgemma_service.py:19`), loaded via `PeftModel.from_pretrained` (`backend/llm/medgemma_service.py:87-92`).
- **Hardware Footprint**: Executes locally on NVIDIA GeForce RTX 4060 Laptop GPU. Dedicated VRAM consumption is ~4.15 GB out of 8.00 GB.
- **Serving Architecture**: Loaded asynchronously into GPU memory during server startup (`backend/main.py:29-43`). Fallback to deterministic heuristic clinical engine occurs if CUDA is unavailable (`backend/llm/medgemma_service.py:51-54, 219-350`).
- **Endpoints Exposing MedGemma**:
  - `POST /api/chat/doctor`: Doctor conversational consults (`backend/api/router.py:48-93`).
  - `POST /api/rl/inference`: Live comparative side-by-side inference benchmark (`backend/api/router.py:284-332`).
  - `POST /api/simulation/run`: Autonomous agent encounter synthesis (`backend/api/router.py:34-46`).
- **System Prompt Location**:
  - Primary MedGemma system prompt is embedded in `backend/llm/medgemma_service.py:153-183`.
  - Specialist reasoning directives are seeded in `backend/database/seed_knowledge.py:15-45` and stored in SQLite `hospital_staff` table.

### 3.2 External Knowledge Sources & RAG Subsystem
- **Status of `knowledge_sources.py`**:
  - *Verification finding*: `knowledge_sources.py` (incorporating RxNorm, DailyMed, openFDA, PubMed, and NABD drug search) does NOT exist in this repository.
  - *Current state*: The repository's medical knowledge foundation currently relies exclusively on local textbook RAG (`backend/rag/`) derived from:
    1. *Harrison's Principles of Internal Medicine* (21st Edition, Vols 1 & 2, 299.9 MB PDF in `Medical Books/Agent for (Internal-medicine)/`).
    2. *Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine* (297.6 MB PDF in `Medical Books/Agent for (Cardiology)/`).
- **Textbook Ingestion & Vector Indexing**:
  - Document parsing: `backend/rag/book_parser.py:15-80` extracts chapters, sub-headings, page numbers, and clinical paragraphs.
  - Chunking & Embeddings: `backend/rag/full_book_embedder.py:40-120` produces 47,806 structured chunks. Embeddings are stored in dense NumPy format at `data/knowledge/harrison_embeddings.npy` (48.2 MB) and JSON collections at `data/knowledge/harrison_full_collection.json` (43.4 MB).
  - Vector search: `backend/rag/vector_index.py:20-95` computes cosine similarity over normalized embeddings, returning top-k citations with book, chapter, page, and excerpt metadata.
  - Search API: Exposing vector retrieval through `GET /api/knowledge/search` (`backend/api/router.py:180-210`).

### 3.3 Agents and Multi-Agent Simulation Engine
- **Agent Architecture**:
  - Base agent abstraction: `backend/agents/base.py:10-50` with unique ID, role, department, memory, and message handling.
  - Doctor Agent: `backend/agents/doctor.py:15-110` formulates differentials, orders diagnostic workups, and prescribes treatment.
  - Nurse Agent: `backend/agents/nurse.py:15-90` conducts emergency triage (ESI 1-5), vitals monitoring, and initial stabilization.
  - Pharmacist Agent: `backend/agents/pharmacist.py:15-180` executes multi-point safety validation: drug-allergy conflicts, drug-disease contraindications, renal clearance dosing adjustments, and antibiotic stewardship.
  - Laboratory Scientist Agent: `backend/agents/lab.py:15-85` validates sample tubes, simulates analyzer processing times, and reports abnormal panic values.
  - Radiologist Agent: `backend/agents/radiology.py:15-75` interprets imaging studies (X-ray, CT, MRI) and drafts diagnostic impressions.
  - Patient Agent: `backend/agents/patient.py:15-80` maintains physiological dynamic state, pain score, and answers physician history inquiries.
- **Simulation Orchestrator**:
  - Orchestrator: `backend/simulation/orchestrator.py:25-260` executes a 4-stage encounter state machine: `INTAKE_TRIAGE` -> `EXAMINATION_WORKUP` -> `INTERVENTION_TREATMENT` -> `DISPOSITION_REVIEW`.
  - Event Bus: `backend/simulation/event_bus.py:15-65` provides pub/sub broadcast queues connected to live WebSocket clients at `/ws/simulation` (`backend/main.py:56-65`).

### 3.4 Reinforcement Learning & Doctor Review Subsystem
- **Clinical Reward Model**: `backend/rl/reward_model.py:20-95` calculates numerical reward signals (range -5.0 to +10.0) based on diagnostic accuracy (+3.0), guideline adherence (+2.0), missed contraindications (-4.0), and dangerous interventions (-5.0).
- **Preference Pair Generator**: `backend/rl/dpo_generator.py:25-140` converts rejected physician reviews into calibrated (Prompt, Chosen, Rejected) DPO training triplets stored in `data/dpo_preference_dataset.jsonl`.
- **Policy Evaluator**: `backend/rl/evaluator.py:25-180` benchmarks base model vs. RL DPO policy across standardized clinical vignettes.
- **DPO Training Pipeline**: `backend/rl/train_dpo.py:30-150` fine-tunes base weights using HuggingFace TRL `DPOTrainer` and LoRA.

### 3.5 Database & State Persistence
- **Storage Engine**: SQLite database at `data/aivh.db` (with legacy fallback at `ai_hospital.db`). Connection handled by `backend/database/connection.py:10-40`.
- **Schema & Tables**: `backend/database/schema.py:15-90` creates 7 relational tables:
  1. `patients`: Demographic profile, blood group, allergies, past medical history.
  2. `encounters`: Clinical admission records, triage acuity, chief complaint, department.
  3. `clinical_reports`: Detailed clinical encounter reports with diagnoses, treatment plans, and evidence links.
  4. `physician_reviews`: Senior physician review scores (1-5 stars), rubric grades, and feedback text.
  5. `dpo_feedback_pairs`: HuggingFace TRL compliant DPO preference pairs with reward deltas.
  6. `knowledge_chunks`: 47,806 Harrison's textbook RAG text passages and citation metadata.
  7. `hospital_staff`: Clinical personnel directory with qualifications, bios, and system directives.
- **Pristine State**: Test and mock records have been purged; the 47,806 knowledge chunks and attending staff member Dr. Marcus Vance are strictly preserved.

### 3.6 Frontend Web Portal Shell
- **App Structure**: Modular single-page architecture (`frontend/src/App.tsx`) with stateful navigation:
  - `INTAKE`: Emergency department intake and triage admission (`CaseIntakeAdmissionSection.tsx`).
  - `PATIENTS`: Inpatient directory, active census, and EHR chart drawer (`PatientDirectorySection.tsx`).
  - `STAFF`: Hospital staff directory with credentials and shift toggles (`StaffManagementSection.tsx`).
  - `REPORTS`: Clinical reports queue and physician review console (`PhysicianReviewDashboard.tsx`).
  - `KNOWLEDGE`: Harrison's vector RAG knowledge search and evidence citations (`KnowledgeSearchSection.tsx`).
  - `BENCHMARK`: Model comparison table and live GPU comparative inference modal (`PolicyBenchmarkModal.tsx`).
  - `JOURNEY`: 2D Patient Journey Flow, Lead II ECG telemetry strip, encounter trajectory timeline, and event stream HUD (`PatientJourneyFlowPage.tsx`, `HospitalFlowDiagram.tsx`).
- **Styling Architecture**: Clinical light mode (`frontend/src/index.css`) utilizing crisp white surfaces (`#ffffff`), subtle slate borders (`#e2e8f0`), deep slate text (`#0f172a`), and clinical blue/sky badges.

---

## 4. Security, Credentials & Privacy Findings

### 4.1 Secrets & API Keys
- **Scan methodology**: Recursive automated pattern scan across all `.py`, `.ts`, `.tsx`, `.json`, `.sql`, `.env*` files for strings matching `api[_-]?key`, `secret`, `password`, `bearer`, `sk-[a-zA-Z0-9]`, and private keys.
- **Finding**: Zero active hardcoded API keys, JWT secrets, passwords, cloud tokens, or private certificates were identified in the codebase.
- **Note**: The codebase operates entirely on local on-device resources (local PyTorch model, local SQLite, local vector files) with zero required external cloud API keys.

### 4.2 Protected Health Information (PHI) & Patient Privacy
- **Scan methodology**: Review of all patient tables, test fixtures, benchmark cases, and CSV/JSON datasets.
- **Finding**: Zero real patient data or protected health information (PHI) exists in the repository.
- **Data Provenance**:
  - All patient profiles (`backend/clinical/cases.py:42-450`) are synthetic benchmark vignettes created for clinical reasoning validation.
  - Dynamic simulation cases in `backend/simulation/orchestrator.py:40-90` synthesize randomized synthetic names, ages, and complaints on the fly.
  - The database has been purged of test records, maintaining only synthetic knowledge chunks.

---

## 5. Phase 1 to 9 Mapping: Reuse, Adapt, or Build New

| Phase | Phase Name | Strategy | Existing Asset / Target Destination |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Synthetic Patients & Case Builder | **Adapt** | Adapt `backend/clinical/cases.py` and `backend/simulation/orchestrator.py` into reproducible Synthea FHIR pipelines and strict `AgentView` data isolation. |
| **Phase 2** | Multi-Source RAG | **Reuse & Build** | **Reuse** Harrison & Braunwald dense vector stores in `data/knowledge/` and `backend/rag/`; **Build** new `knowledge_sources.py` adapters for RxNorm, openFDA, and PubMed. |
| **Phase 3** | Grounded Clinical Generation | **Reuse & Adapt** | **Reuse** local GPU `backend/llm/medgemma_service.py` engine; **Adapt** `backend/api/router.py` report generation to enforce claim-evidence links and abstention. |
| **Phase 4** | Verification Layer | **Adapt & Build** | **Adapt** `backend/agents/pharmacist.py` allergy and contraindication engine; **Build** deterministic rule tables, DeepEval metrics, and grounding judge. |
| **Phase 5** | Agents & Orchestration (Headless) | **Reuse & Adapt** | **Reuse** 6 specialized agent classes in `backend/agents/`; **Adapt** `backend/simulation/orchestrator.py` into headless execution with deterministic replay. |
| **Phase 6** | Doctor Review & Feedback Store | **Reuse & Adapt** | **Reuse** `frontend/src/components/dashboard/PhysicianReviewDashboard.tsx`; **Adapt** `backend/rl/dpo_generator.py` into an append-only feedback store with overlap agreement. |
| **Phase 7** | Fine-Tuning & Model Lifecycle | **Reuse & Adapt** | **Reuse** `backend/rl/train_dpo.py` and LoRA weights in `models/medgemma-dpo-lora/`; **Adapt** into a versioned model registry with gated promotion. |
| **Phase 8** | Virtual Hospital Environment (2D/3D) | **Reuse** | **Reuse** `frontend/src/components/diagram/PatientJourneyFlowPage.tsx` and 2D flow diagrams; connect to read-only simulation event stream. |
| **Phase 9** | Advanced Intelligence | **Build New** | **Build** specialist imaging model tools (fracture and knee OA) and knowledge graph reasoning modules. |

---

## 6. Gap Analysis & Next Steps

1. **Missing Source Adapters**: `knowledge_sources.py` (RxNorm, DailyMed, openFDA, PubMed) must be created in Phase 2 (P2.1) to support external drug interaction and medical literature lookups.
2. **Repository Structure Alignment**: Existing working code is structured under `backend/` and `frontend/`, whereas the master plan specifies `src/vh/` and `web/`. Per ADR-0001 (Proposed), path mappings will preserve existing working code while adopting standardized CLI interfaces.
3. **Evaluation Harness**: Phase 0 requires an automated evaluation harness and frozen golden-set mechanism (`eval/golden/v1/`) to be implemented in STEP 04.
