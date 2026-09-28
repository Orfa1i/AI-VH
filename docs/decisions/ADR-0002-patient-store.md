# ADR-0002: Patient Store and FHIR Data Persistence Architecture

- **Status**: Accepted
- **Date**: 2026-09-28
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-1-synthetic-patients/STEP-09_P1.3_patient-store.md`, `plan/CLAUDE.md`

---

## 1. Context and Problem Statement

Step 09 requires a queryable clinical patient store capable of ingesting Synthea-generated FHIR R4 bundles idempotently and serving time-windowed clinical queries to the Case Builder, verification layers, and downstream specialized agents.

The task specification provides two architectural paths:
1. A dedicated HAPI FHIR Java Server running in Docker Compose.
2. A Relational JSONB document store (PostgreSQL JSONB in production, with local SQLite fallback).

---

## 2. Alternatives Considered

### Alternative 1: Dedicated HAPI FHIR Server (Java container)
- **Pros:**
  - Full-featured FHIR R4 REST API out of the box with standard HL7 search parameters.
- **Cons:**
  - Requires a high-memory JVM container (1.5GB to 2.5GB RAM overhead), significantly increasing resource contention alongside the local MedGemma 27B GPU inference engine.
  - Introduces network serialization and HTTP roundtrip overhead for every internal clinical query during multi-agent simulation and golden evaluation runs.
  - Creates hard Docker and network dependencies that degrade local CI testing and offline developer workflows.

### Alternative 2: Relational JSONB Clinical Store (PostgreSQL JSONB with SQLite dual-mode)
- **Pros:**
  - Preserves 100% of raw FHIR R4 resource definitions in native JSON/JSONB document columns without data loss or schema truncation.
  - Extracts key query dimensions (`resource_type`, `resource_id`, `patient_id`, `encounter_id`, `effective_datetime`, `code`) into indexed relational columns for millisecond lookups.
  - Supports strict idempotent upserts via primary key `(resource_type, resource_id)`.
  - Zero heavy Java overhead; runs in-process or connects to existing PostgreSQL 16 container (`docker-compose.yml`).
  - Seamless dual-mode execution: SQLite for lightning-fast unit tests and isolated CI runners; PostgreSQL for persistent multi-container hospital deployments.
- **Cons:**
  - Does not expose a public HL7 FHIR REST server by default, but internal Python repository APIs provide faster, type-safe access directly to the Case Builder.

---

## 3. Decision

We decide to **adopt Alternative 2: Relational JSONB Clinical Store (`PatientRepository`)**.

The patient repository implementation (`src/vh/cases/patient_repo.py`) provides:
1. Standard SQL schema with composite primary key `(resource_type, resource_id)`.
2. Dedicated B-tree indexes on `patient_id`, `effective_datetime`, `resource_type`, and clinical `code`.
3. Complete idempotent loading semantics implemented in `src/vh/cases/fhir_loader.py`.
4. Dedicated query APIs for patient demographics, encounters, laboratory observations, clinical conditions, medications, and chronological clinical timelines.
