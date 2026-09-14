# 10. Backend, Orchestrator & Memory

## Backend

Recommended: **Python**.

Use: FastAPI, Pydantic, SQLAlchemy, PostgreSQL, pgvector, Redis where useful.

Potential architecture:

```
Frontend
   ↓
API Gateway
   ↓
Agent Orchestrator
   ↓
Simulation Engine
   ↓
Agent Services
   ↓
Clinical Tools
   ↓
Database / RAG
```

## Agent Orchestrator

A major component. Manages:

- Which agent acts?
- What does the agent know?
- What tools can it use?
- What is the current environment state?
- What happened previously?
- Who should receive the next event?

Example:

```
Patient arrives
       ↓
Orchestrator
       ↓
Nurse Agent
       ↓
Vital signs
       ↓
Orchestrator
       ↓
Doctor Agent
       ↓
Clinical decision
```

## Memory

Separate memory into different categories — do not mix these together:

- **Patient memory**: medical history, previous encounters, medications, allergies
- **Agent episodic memory**: previous actions, previous cases, previous feedback
- **Knowledge memory**: medical books, guidelines, references
