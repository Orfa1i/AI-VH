# AI Virtual Hospital (AI-VH) 🏥
### Autonomous Multi-Agent Healthcare Simulation & Reinforcement Learning Platform

AI-VH is a cutting-edge, autonomous multi-agent clinical simulation platform where AI agents (Doctors, Nurses, Patients, Radiologists, and Laboratory Staff) collaborate in a simulated clinical healthcare environment. The platform bridges the gap between static LLM medical benchmarks and real-world clinical decision-making by placing autonomous agents into dynamic clinical loops with human physician review and reinforcement learning.

---

## 🌟 Core Research Question
> **Can autonomous medical AI agents improve their clinical decision-making, diagnostic accuracy, and workflow behavior through expert human feedback and Reinforcement Learning?**

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────┐
                    │       VIRTUAL HOSPITAL PLATFORM       │
                    └──────────────────┬───────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
      ┌─────────▼─────────┐                         ┌─────────▼─────────┐
      │  3D Visual World  │                         │ Simulation Engine │
      │ (Three.js / R3F)  │                         │  & Event Bus      │
      └─────────┬─────────┘                         └─────────┬─────────┘
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Agent Orchestrator │
                            └──────────┬──────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────▼───────┐              ┌───────▼───────┐              ┌───────▼───────┐
│ Patient Agent │              │  Nurse Agent  │              │ Doctor Agent  │
│ (Dynamic State│              │(Triage, Vitals│              │(Differential, │
│  & Progression│              │ & Monitoring) │              │ Orders, Dx)   │
└───────┬───────┘              └───────┬───────┘              └───────┬───────┘
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │   Clinical Tools    │
                            │ (EHR, Labs, Imaging)│
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │ Medical RAG Engine  │
                            │ (pgvector + Books)  │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │ Local MedGemma 4-Bit│
                            │ (RTX 4060 NF4)      │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │   Clinical Report   │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Physician Review   │
                            │ (Structured Feedback│
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │ RL / DPO / Eval     │
                            │ (Policy Improvement)│
                            └─────────────────────┘
```

---

## 📋 Project Structure

```
AI-VH/
├── backend/                  # FastAPI simulation backend & orchestrator
│   ├── agents/               # Doctor, Nurse, Patient, Lab agents
│   ├── clinical/             # Clinical tools, EHR, vitals, lab & imaging models
│   ├── simulation/           # Event bus, state machine, encounter lifecycle
│   ├── rag/                  # Textbook chunking, pgvector embeddings & retrieval
│   ├── evaluation/           # Metrics, case benchmarks, physician review schemas
│   └── api/                  # REST & WebSocket endpoints for real-time telemetry
├── docs/                     # Detailed architectural specifications (Phases 0–7)
│   ├── 00-INDEX.md
│   ├── 01-vision-and-final-system.md
│   ├── 02-virtual-hospital-3d.md
│   ├── 03-agent-architecture.md
│   ├── 04-medical-knowledge-rag.md
│   ├── 05-clinical-workflow-and-tools.md
│   ├── 06-data-architecture.md
│   ├── 07-clinical-reports-and-review.md
│   ├── 08-reinforcement-learning.md
│   ├── 09-evaluation-and-safety.md
│   ├── 10-backend-and-orchestration.md
│   ├── 11-frontend-architecture.md
│   ├── 12-project-folder-structure.md
│   └── 13-roadmap-phases.md
├── MedGemma Model/           # Local MedGemma weights & 4-bit RTX 4060 inference
├── Medical Books/            # Primary medical textbooks (Harrison's, etc.)
└── frontend/                 # Next.js / Vite dashboard & Three.js 3D hospital (Phases 3+)
```

---

## 🚦 Roadmap

- [x] **Phase 0: Research & Architecture** — Core specifications, agent protocols, clinical data schemas, and research goals documented.
- [ ] **Phase 1: Clinical MVP** — End-to-end loop: 1 Patient Agent + 1 Nurse Agent + 1 Doctor Agent (MedGemma) + Event Bus + Clinical Tools + EHR + Clinical Report + Human Review.
- [ ] **Phase 2: Multi-Agent Hospital** — Laboratory, Radiology, multiple specialty physicians, concurrent encounters.
- [ ] **Phase 3: 3D Hospital Visualization** — React Three Fiber interactive 3D hospital rooms, agent pathfinding, and real-time visual events.
- [ ] **Phase 4: Physician Feedback Engine** — Structured clinical annotations, delta comparisons, preference dataset generation.
- [ ] **Phase 5: Evaluation & Safety Gate** — Standardized case benchmarks, halluncination detection, diagnostic concordance scoring.
- [ ] **Phase 6: Reinforcement Learning (RL / DPO)** — Policy optimization from physician preference data.
- [ ] **Phase 7: Full Scale Hospital Simulation** — Comprehensive departments (ICU, Surgery, OB/GYN, Pediatrics).

---

## 💻 Hardware & Local Execution
- **GPU**: NVIDIA GeForce RTX 4060 (8GB VRAM)
- **Quantization**: BitsAndBytes 4-bit NF4 (`bnb_4bit_compute_dtype=torch.bfloat16`)
- **Foundation Model**: MedGemma (local weights in `./MedGemma Model/model`)
