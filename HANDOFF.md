# Project Handoff: AI Virtual Hospital (AI-VH)

## 1. Project Overview & Context
AI-VH is an autonomous multi-agent healthcare simulation and reinforcement learning platform designed to study whether autonomous medical AI agents (Doctors, Nurses, Patients, Laboratory Scientists, Radiologists, Pharmacists) can improve clinical decision-making through expert physician feedback and reinforcement learning. The system is backed by local 4-bit quantized MedGemma running on an RTX 4060 GPU, Harrison's Principles of Internal Medicine (21st Ed) textbook RAG, an asynchronous event bus, an interactive 3D virtual hospital environment (Three.js / React Three Fiber), and a structured physician review dashboard.

## 2. Accomplished This Session
- **Phase 0 Baseline (Commit `7e46e58`)**:
  - Structured the 50-section project specification into 14 architectural documents in `docs/` and root `README.md`.
- **Phase 1 MVP Implementation (Commit `8930f70`)**:
  - Built core clinical simulation engine, Harrison's RAG index, Patient/Nurse/Doctor agents, 3D hospital world, and Physician Review Dashboard.
- **Phase 2 Multi-Agent Hospital (Commit `840a04f`)**:
  - Implemented `LaboratoryAgent` and `RadiologyAgent` with 3D avatars and clinical test routing.
- **Internal Medicine Specialist & Dedicated RAG Agent (Commit `5aa6cd0`)**:
  - Implemented `InternalMedicineSpecialistAgent` (`Dr. Marcus Vance, MD, FACP`) and `InternalMedicineRAGAgent` with query expansion, BM25 indexing over Harrison's 21st Edition, and formal `EvidenceBrief` synthesis.
  - Added `POST /api/specialists/internal-medicine/consult` and `InternalMedicineConsultModal.tsx`.
- **UI Stacking Context & Drei Z-Index Fix (Commit `dc6c1ee`)**:
  - Clamped `zIndexRange={[10, 0]}` and added `isolate z-0` to prevent 3D HTML badges from bleeding through modal containers.
- **Phase 6: RL / Direct Preference Optimization (DPO) Preference Generator (Commit `a542916`)**:
  - Built `ClinicalRewardModel`, `DPOPreferenceGenerator`, REST endpoints `GET /api/rl/dataset` and `POST /api/rl/dataset/export`, exported `data/dpo_preference_dataset.jsonl`, and built `RLDatasetModal.tsx` UI.
- **AutoCAD Floor Plan (Sheet A-1) 1:1 Architectural Implementation & Light Clinic Aesthetic (Commit `4aa3e5b`)**:
  - Reconstructed the complete 3D virtual hospital following AutoCAD layout (`Gemini_Generated_Image_vcok6pvcok6pvcok.jpg`): West Entrance/Waiting/ER, Central Rotunda Nurse Station, North Doctor/Lab, Central Doctor/Pharmacy, South Exam/Radiology, and East Inpatient Wing.
- **Phase 7 Scale: Clinical Pharmacist Agent (`Dr. Elena Rostova, PharmD, BCPS`)**:
  - Implemented `PharmacistAgent` in `backend/agents/pharmacist.py` with multi-tier pharmacology screening:
    - Allergen cross-reactivity mapping (penicillin beta-lactams, sulfa, aspirin, opiates).
    - Drug-class contraindication detection (NSAIDs in ACS/AKI, beta-blockers in cardiogenic shock, sliding-scale monotherapy).
    - Renal dose adjustments (flagging nephrotoxicity and enoxaparin dose adjustments when creatinine >= 1.5 mg/dL or BUN >= 30).
  - Integrated into simulation loop in `backend/simulation/orchestrator.py` with `MedicationSafetyReport` generation.
  - Added REST endpoint `POST /api/pharmacy/review` with full request validation.
  - Implemented interactive `PharmacistModal.tsx` with clinical benchmark scenario presets.
  - Added Pharmacist 3D avatar with teal/emerald badge in the Hospital Pharmacy room.
  - Added 5 unit/integration tests in `backend/tests/test_pharmacist.py`.
- **Interactive Proximity Triggers System (`[E]` Key & HUD Banner)**:
  - Added dynamic proximity detector in `FirstPersonControls.tsx` calculating Euclidean distance to all 5 specialist stations: Dr. Vance (Internal Med), Dr. Rostova (Pharmacy), David Chen (Laboratory), Dr. Hayes (Radiology), and Sarah Jenkins (Rotunda Triage).
  - Implemented interactive HUD banner in `FirstPersonHUD.tsx` with animated prompt `[E] to Interact`.
  - Built `DepartmentStationModal.tsx` for interactive inspection of Automated Biomarker Analyzers, CT PACS Console, and Triage Queues.
- **Phase 6 Reinforcement Learning / DPO Training Pipeline (`train_dpo.py`)**:
  - Implemented HuggingFace `trl.DPOTrainer` / `peft.LoraConfig` training pipeline in `backend/rl/train_dpo.py` with 4-bit LoRA adapter configuration.
  - Added auto-hardware detection with live GPU fine-tuning and simulated verification mode for CPU/CI/CD.
  - Exported verified LoRA configuration (`models/medgemma-dpo-lora/adapter_config.json`) and training summary log.
  - Added unit test suite in `backend/tests/test_dpo_training.py`.
- **Live Deployment & Verification**:
  - Backend FastAPI server running live on `http://127.0.0.1:8000` with `--reload` (Task 278).
  - Frontend Vite dev server running live on `http://localhost:5173` (Task 280).
  - 21/21 automated backend tests passing (`py -3.13 -m pytest backend/tests/ -v`).
  - Production frontend build clean (`pnpm build` -> exit code 0).

## 3. Current State of the Work
- Both backend and frontend servers are active in the background.
- The 3D clinic renders the exact AutoCAD layout with all 6 healthcare agents active.
- First-person walking dynamically prompts `[E] to Interact` when approaching any specialist station.
- RL DPO training pipeline is executable directly via `python -m backend.rl.train_dpo`.

## 4. Next Steps
- Integrate speech audio synthesis (Web Speech API / TTS) for agent verbal responses during consultations.
- Add multi-patient simultaneous inpatient monitoring in the East Inpatient Wing (Rooms 1-4).
- Add automated policy evaluation benchmarking script comparing base MedGemma vs RL DPO LoRA adapter.
