# AI Virtual Hospital — Docs Index

Source: `Full-Idea.txt` (50 sections), split by topic.

| File | Covers (orig sections) | Content |
|---|---|---|
| [01-vision-and-final-system.md](01-vision-and-final-system.md) | 1, 2, 49, 50 | Project vision, core layered architecture, key research experiment, final system diagram |
| [02-virtual-hospital-3d.md](02-virtual-hospital-3d.md) | 3, 4, 5 | 3D hospital scope (Phase 1 vs later), how 3D layer maps to agent backend, tech choice (R3F) |
| [03-agent-architecture.md](03-agent-architecture.md) | 6, 7, 8, 11, 12, 13, 14, 15 | Generic agent config, doctor/nurse/patient agents, specialties, case complexity, case generation |
| [04-medical-knowledge-rag.md](04-medical-knowledge-rag.md) | 9, 10 | Book ingestion pipeline, per-specialty RAG collections |
| [05-clinical-workflow-and-tools.md](05-clinical-workflow-and-tools.md) | 16, 17, 18, 19 | ER workflow, clinical tool functions, agent-to-agent messaging, event bus |
| [06-data-architecture.md](06-data-architecture.md) | 20, 21, 22 | PostgreSQL schema, pgvector, Obsidian as docs-only KM system |
| [07-clinical-reports-and-review.md](07-clinical-reports-and-review.md) | 23, 24, 25, 26, 27 | Report structure, physician review dashboard, feedback storage, structured feedback types |
| [08-reinforcement-learning.md](08-reinforcement-learning.md) | 28, 29, 30, 31 | RL scope, state/actions/reward, feedback→training pipeline, agent versioning |
| [09-evaluation-and-safety.md](09-evaluation-and-safety.md) | 32, 33, 34, 35 | Evaluation metrics, benchmark dataset, human physician evaluation, safety controls |
| [10-backend-and-orchestration.md](10-backend-and-orchestration.md) | 36, 37, 38 | Backend stack (FastAPI etc.), agent orchestrator, memory separation |
| [11-frontend-architecture.md](11-frontend-architecture.md) | 39, 40 | Two frontends (3D hospital vs research dashboard), dashboard metrics |
| [12-project-folder-structure.md](12-project-folder-structure.md) | 41 | Repo layout |
| [13-roadmap-phases.md](13-roadmap-phases.md) | 42–48 | Phase 0–7 development roadmap |

Key principle (from source, end of file): **build clinical simulation loop first** (Patient → Nurse → Doctor → Investigation → Diagnosis → Report → Physician Review → Feedback → Evaluation), **then** wrap the 3D hospital around it.
