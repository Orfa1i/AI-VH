# ADR-0001: Target Repository Layout and Existing Codebase Mapping Strategy

- **Status**: Accepted
- **Date**: 2026-09-28
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/CLAUDE.md` (Section 4 & Section 5), `plan/README.md` (Target repository layout)

---

## 1. Context and Problem Statement

The phased master plan (`plan/README.md`) specifies a standardized greenfield repository structure:
- `src/vh/`: Core Python library modules (common, cases, rag, generation, verification, agents, feedback, training, events).
- `web/`: Clinical AI OS web portal and 3D visual world.
- `eval/`: Golden sets, harness, fault injection, and evaluation reports.
- `configs/`: Thresholds, safety rules, and agent definitions.

However, the AI-VH repository already contains a functioning, production-tested implementation:
- `backend/`: Fully structured FastAPI application with 6 agent modules, RAG chunking and vector index, local MedGemma 4-bit GPU engine, SQLite persistence, and 67 passing tests.
- `frontend/`: Operational React 19 + TypeScript + Vite + Tailwind CSS 4 clinical portal with 2D Patient Journey Graph and real-time HUDs.
- `MedGemma Model/` & `models/`: Local quantized model weights and trained DPO LoRA adapter.
- `Medical Books/` & `data/knowledge/`: Ingested medical literature and 47,806 vector embeddings.

Moving or renaming functional code precipitously would break existing module imports, dev scripts, and running background servers. `plan/CLAUDE.md` explicitly addresses this: *"If your existing code lives elsewhere, ADR-0001 (STEP 01 to 02) maps it onto this layout instead of moving working code unnecessarily."*

---

## 2. Decision

We decide to **map existing functional directories to the target architecture via a structured transition mapping**, preserving existing code in place while establishing target layout boundaries:

1. **Backend Mapping (`backend/` -> `src/vh/`)**:
   - `backend/llm/medgemma_service.py` -> maps to `src/vh/generation/`
   - `backend/rag/` -> maps to `src/vh/rag/`
   - `backend/agents/` -> maps to `src/vh/agents/`
   - `backend/clinical/` & `backend/database/` -> maps to `src/vh/cases/`
   - `backend/rl/` -> maps to `src/vh/feedback/` and `src/vh/training/`
   - `backend/simulation/` -> maps to `src/vh/events/` and `src/vh/agents/`
   - In Step 02, we will create a top-level `src/vh` package that exports and wraps these modules, ensuring backward compatibility with existing `backend.*` imports.

2. **Frontend Mapping (`frontend/` -> `web/`)**:
   - The React 19 application in `frontend/` represents the "Clinical AI OS shell".
   - It will either remain at `frontend/` with a root-level alias/symlink or be referenced as the canonical web frontend directly in project configuration files.

3. **Evaluation & Golden Sets (`eval/`)**:
   - Create a new top-level `eval/` directory for golden sets (`eval/golden/v1/`), DeepEval harnesses (`eval/harness/`), and fault injection packets (`eval/faults/`).

4. **Configuration (`configs/`)**:
   - Create `configs/` at the repository root to house `thresholds.yaml`, safety rule tables (`configs/safety/`), and agent definitions (`configs/agents/`).

5. **Documentation & Step Records (`docs/`)**:
   - Retain existing `docs/` architecture, adding `docs/steps/` for step reports, `docs/decisions/` for ADRs, and `docs/signoffs/` for human check gates.

---

## 3. Directory Mapping Matrix

| Target Layout (`plan/README.md`) | Current Repository Path | Mapping Strategy |
| :--- | :--- | :--- |
| `src/vh/common/` | `backend/database/connection.py`, `backend/clinical/tools.py` | Wrap into `src/vh/common` (config, logging, tracing) |
| `src/vh/cases/` | `backend/clinical/cases.py`, `backend/database/repository.py` | Direct mapping; extend with Synthea FHIR loader |
| `src/vh/rag/` | `backend/rag/` | Direct mapping; extend with source adapters |
| `src/vh/generation/` | `backend/llm/medgemma_service.py` | Direct mapping; add report schema validator |
| `src/vh/verification/` | `backend/agents/pharmacist.py`, `backend/clinical/` | Direct mapping; add grounding judge and guardrails |
| `src/vh/agents/` | `backend/agents/`, `backend/simulation/orchestrator.py` | Direct mapping; add deterministic replay |
| `src/vh/feedback/` | `backend/rl/dpo_generator.py`, `backend/rl/reward_model.py` | Direct mapping; add append-only feedback store |
| `src/vh/training/` | `backend/rl/train_dpo.py` | Direct mapping; add model registry and gated promotion |
| `src/vh/events/` | `backend/simulation/event_bus.py`, `backend/simulation/events.py` | Direct mapping; read-only event stream API |
| `web/` | `frontend/` | Existing React 19 shell preserved in place |
| `eval/` | *New directory* | Created in Step 04 for evaluation harness and golden sets |
| `configs/` | *New directory* | Created in Step 02 for `thresholds.yaml` and safety tables |
| `docs/` | `docs/` | Extended with `steps/`, `decisions/`, `signoffs/` |
| `data/` | `data/`, `Medical Books/`, `MedGemma Model/`, `models/` | Preserved in place; referenced via configuration |

---

## 4. Consequences

### Positive
- **Zero Disruption**: Existing dev servers, Vite builds, and test commands (`pytest backend/tests`) continue functioning without breaking changes.
- **Strict Compliance**: Adheres to the core rule of `plan/CLAUDE.md` to avoid moving working code unnecessarily while establishing structured interfaces.
- **Incremental Migration**: Allows Phase 0 and Phase 1 to introduce new tools and tests alongside verified, operational components.

### Negative
- Requires maintaining import compatibility wrappers if external consumers import from both `src/vh` and `backend`.
