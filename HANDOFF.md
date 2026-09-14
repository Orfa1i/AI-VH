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
  - Clamped `zIndexRange={[10, 0]}` and added `isolate z-0` to prevent 3D HTML badges from bleeding through modal containers.
- **Phase 6: RL / Direct Preference Optimization (DPO) Preference Generator (Commit `a542916`)**:
  - Built `ClinicalRewardModel`, `DPOPreferenceGenerator`, REST endpoints `GET /api/rl/dataset` and `POST /api/rl/dataset/export`, exported `data/dpo_preference_dataset.jsonl`, and built `RLDatasetModal.tsx` UI.
- **AutoCAD Floor Plan (Sheet A-1) 1:1 Architectural Implementation & Light Clinic Aesthetic (Commit pending)**:
  - **1:1 Blueprint Geometric Alignment**: Reconstructed the entire 3D virtual hospital according to the AutoCAD layout (`Gemini_Generated_Image_vcok6pvcok6pvcok.jpg`):
    - **West Zone**: Main entrance double glass doors, Patient Waiting Area with 13 waiting chairs, Reception with curved counter & admin stations, Emergency Department (ED) with 7 acute stretcher bays & privacy divider rails, Triage desk with vitals monitor, and dedicated South Ambulance Entrance with docking markers.
    - **Central Rotunda**: Semicircular curved twin nurse counters forming a circular command station island with 4-way outward-facing diagnostic terminals.
    - **North Wing**: Examination Room 1, Examination Room 2, Doctor Station (Physician Office with executive desk and dual displays), and large Clinical Laboratory with double-sided central workbench, automated analyzers, and centrifuge.
    - **Central Core**: Doctor Station (Conference consultation suite) and Pharmacy with dispensing counter, prescription pickup, and tiered pharmaceutical shelving.
    - **South Wing**: 4 Examination Rooms (Exam 3, 4, 5, 6) and Radiology Suite (CT scanner gantry ring with sky-blue bore illumination, motorized scan couch, lead-shielded console, and patient ensuite).
    - **East Inpatient Wing**: 4 private patient rooms (Patient Rooms 1, 2, 3, 4) with electric inpatient beds, cyan safety rails, IV infusion poles, and private ensuite bathrooms.
  - **Light Clinical Color Palette**:
    - Replaced dark environment with medical daylight illumination: `#f0f9ff` ambient sky, 5000K daylight lighting with soft shadows.
    - Off-white porcelain tile floor plate (`#f8fafc`), clean gray tile grout grid (`#e2e8f0`), and soft cyan clinical corridor runners (`#e0f2fe`) with deep blue guide border ribbons (`#0284c7`).
    - Crisp clinical drywall partitions (`#ffffff`) with medical sky-blue chair-rail accent trims.
  - **1st-Person Navigation & Collision Update**:
    - Updated `FirstPersonControls.tsx` to detect all 20+ rooms and zones dynamically as the physician walks across the clinic floor.
    - Boundary constraints calibrated to the building footprint ($X \in [-17.2, 17.0], Z \in [-9.8, 9.8]$).
- **Live Deployment & Verification**:
  - Backend FastAPI server running live on `http://127.0.0.1:8000` with `--reload` (Task 596).
  - Frontend Vite dev server running live on `http://127.0.0.1:5173` (Task 282).
  - 14/14 automated backend tests passing (`pytest backend/tests/ -v`).
  - Production frontend build clean (`pnpm build` -> exit code 0).

## 3. Current State of the Work
- Both servers are active in the background.
- The 3D clinic renders the exact AutoCAD layout in daylight medical styling.
- Both 1st-Person Walkthrough and Overhead Orbit View are fully functional.

## 4. Next Steps
- Add interactive proximity triggers in first-person mode (e.g. press [E] to consult doctor at desk or inspect laboratory analyzers).
- Implement training loop script using HuggingFace `trl.DPOTrainer` with local 4-bit LoRA adapter for MedGemma.
