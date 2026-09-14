# Project Handoff: AI Virtual Hospital (AI-VH)

## 1. Project Overview & Context
AI-VH is an autonomous multi-agent healthcare simulation and reinforcement learning platform designed to study whether autonomous medical AI agents (Doctors, Nurses, Patients, Laboratory Scientists, Radiologists) can improve clinical decision-making through expert physician feedback and reinforcement learning. The system is backed by local 4-bit quantized MedGemma running on an RTX 4060 GPU, Harrison's Principles of Internal Medicine (21st Ed) textbook RAG, an asynchronous event bus, an interactive 3D virtual hospital environment (Three.js / React Three Fiber), and a structured physician review dashboard.

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
  - **Identified and resolved 3D badge bleed-through**: `@react-three/drei`'s `<Html>` components by default assign astronomical 24-bit CSS `z-index` values (`zIndexRange: [16777271, 0]`) to depth-sort 3D DOM labels. Because departments and avatars on the left side of the hospital (`Reception & Intake`, `Examination Room 1`, `Clinical Laboratory`, `Patient`, and `David Chen, MLS`) had coordinates $x \in [-8, -7]$, their projected 2D HTML badges rendered with `z-index ~16,777,000`, punching straight through the modal container (`z-50`).
  - **Resolution**:
    1. Clamped `zIndexRange={[10, 0]}` on `<Html>` in `DepartmentRoom.tsx` and `AgentAvatar.tsx`.
    2. Added `isolate z-0` to the Canvas container in `HospitalCanvas.tsx` to trap all 3D HTML elements within their own isolated stacking context.
    3. Verified via production build (`tsc -b && vite build`) and hot module reload.
- **3D First-Person Perspective & Clinical Interior Walkthrough (Commit `66d72e7`)**:
  - Built `FirstPersonControls.tsx`: Camera control locked at realistic human eye-level (1.7m), WASD movement with sprint (`Shift`), mouse-drag pitch/yaw look with vertical clamping, room boundary constraints, and dynamic coordinate-based room identification.
  - Built `HospitalFurnishings.tsx`: Comprehensive 3D clinical models including examination beds with rails, IV drip poles with fluid bags, physician workstations with dual diagnostic monitors, triage desks with vitals carts, clinical laboratory analyzer benches and centrifuges, and a radiology CT scanner gantry ring and scan table.
  - Built `FirstPersonHUD.tsx`: Interactive heads-up display with central precision reticle, active room banner, walking control helper bar, and instant perspective toggle button between **1st-Person Walkthrough** and **Overhead Orbit View**.
  - Integrated into `HospitalCanvas.tsx` and verified clean production compilation with `pnpm build`.
- **Phase 6: RL / Direct Preference Optimization (DPO) Preference Generator (Commit pending)**:
  - Built `ClinicalRewardModel` (`backend/rl/reward_model.py`): Multi-dimensional rubric evaluation weighting diagnosis accuracy (+0.35 to -0.40), evidence reasoning (+0.25 to -0.35), test appropriateness (+0.20 to -0.30), treatment safety (+0.25 to -0.65), physician Likert scaling, and Harrison's textbook citation fidelity bonus (+0.10).
  - Built `DPOPreferenceGenerator` (`backend/rl/dpo_generator.py`): Transforms physician review feedback (including corrected diagnoses and treatments) into standard HuggingFace / PyTorch DPO training pairs `(prompt, chosen, rejected)`.
  - Added cold-start Harrison's calibrated benchmark pairs for NSTEMI, DKA, and AKI prerenal azotemia.
  - Added REST API endpoints `GET /api/rl/dataset` and `POST /api/rl/dataset/export`.
  - Exported training dataset to `data/dpo_preference_dataset.jsonl` compatible with `trl.DPOTrainer`.
  - Built interactive glassmorphism UI modal `RLDatasetModal.tsx` with side-by-side prompt, chosen, rejected cards, reward margins, citation grounding, filter pills, and instant JSONL export.
- **Live Deployment & Verification**:
  - Backend FastAPI server running live on `http://127.0.0.1:8000` with `--reload` (Task 596).
  - Frontend Vite dev server running live on `http://127.0.0.1:5173` (Task 282).
  - 14/14 automated backend tests passing (`pytest backend/tests/ -v`).
  - Production frontend build clean (`pnpm build` -> exit code 0).

## 3. Current State of the Work
- Both servers are active in the background.
- First-person 3D navigation is active by default in the 3D Hospital tab.
- RL / DPO Alignment Corpus viewer is active via the top bar `RL / DPO Corpus` button.

## 4. Next Steps
- Add interactive proximity triggers in first-person mode (e.g. press [E] to consult doctor or inspect lab analyzer).
- Implement training loop script using HuggingFace `trl.DPOTrainer` with local 4-bit LoRA adapter for MedGemma.
