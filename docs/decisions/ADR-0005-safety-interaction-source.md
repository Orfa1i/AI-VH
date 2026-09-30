# ADR-0005: Clinical Drug Interaction and Deterministic Safety Knowledge Source

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-4-verification/STEP-25_P4.1_safety-rules-engine.md`, `configs/thresholds.yaml`

---

## 1. Context and Problem Statement

Step 25 implements the deterministic clinical safety rules engine (`DeterministicSafetyEngine`) for AI Virtual Hospital (AI-VH). Deterministic safety rules serve as the authoritative last line of defense against adverse drug events (ADEs), contraindications, dosage miscalculations, patient-data contradictions, and unaddressed physiological emergencies.

A primary requirement is drug-drug interaction (DDI) verification. Previously, open-source clinical projects relied on the National Library of Medicine (NLM) RxNav interaction API (`rxnav.nlm.nih.gov/REST/interaction`). However, the NLM permanently retired the RxNav interaction API in January 2024. Consequently, an alternative, deterministic, reproducible, and verifiable source of drug interaction knowledge must be selected and established for AI-VH.

---

## 2. Decision Drivers

1. **Strict Determinism and Zero LLM Dependency**: Safety rules must execute as pure deterministic functions without probabilistic LLM calls, temperature variation, or network latency.
2. **Offline Resilience and Data Sovereignty**: Rules must execute reliably in hermetic or offline clinical environments without runtime third-party API dependencies.
3. **Clinical Grounding and Verifiability**: Every interaction pair, contraindication, and renal dosage adjustment must cite authoritative medical provenance (e.g. FDA DailyMed Section 7, AHA/ACC guidelines, or KDIGO recommendations).
4. **Physician Governance (Checkpoint H4 Gate)**: Safety knowledge tables must support explicit versioning and human physician sign-off (`status: draft` vs `status: verified`), failing closed in production if unapproved.

---

## 3. Evaluated Options

### Option A: External Commercial API (Lexicomp / Micromedex / First Databank)
- *Pros*: Comprehensive clinical interaction coverage, continuous commercial curation.
- *Cons*: Expensive per-seat licensing, proprietary vendor lock-in, recurring external network dependencies, non-trivial API latency in real-time verification pipelines.

### Option B: Pre-parsed DailyMed SPL Section 7 and Curated Reference Tables (Selected)
- *Pros*: High-fidelity clinical grounding directly from FDA package insert labels (Section 7: Drug Interactions).
- *Pros*: Stored as structured, human-readable YAML tables under version control in `configs/safety/`.
- *Pros*: Zero external network dependencies, instant in-memory lookup (< 1 ms latency), 100% reproducible and audit-friendly.
- *Cons*: Requires curated ingestion and mandatory human physician review at Checkpoint H4.

---

## 4. Decision

We decide to **adopt Option B: Structured DailyMed-derived SPL Section 7 and Curated Reference Tables** as the primary knowledge source for the AI-VH deterministic safety rules engine.

### Implementation Architecture
1. **Safety Tables Storage**:
   - `configs/safety/drug_interactions.yaml`: Pre-extracted severe and moderate drug-drug interactions with FDA DailyMed Section 7 provenance.
   - `configs/safety/contraindications.yaml`: Documented contraindications mapped to ICD-10 clinical conditions.
   - `configs/safety/dose_ranges.yaml`: Standard dosing and eGFR-based renal dose adjustment rules.
   - `configs/safety/red_flags.yaml`: Physiological emergency thresholds (hypoxemia, profound hypotension, severe tachycardia, hyperkalemia) derived from Surviving Sepsis and AHA ACLS guidelines.

2. **Draft Rejection Guard (Checkpoint H4 Enforcement)**:
   - All safety tables are initialized with `status: draft`.
   - In `dev` mode, the engine issues explicit warning logs while allowing local development and testing.
   - In `production` mode, `DeterministicSafetyEngine` raises `SafetyConfigurationError` if any table possesses `status: draft`, guaranteeing unreviewed clinical tables cannot reach production.

3. **Rule Interface Contract**:
   - Each safety rule implements the pure interface: `evaluate(report: ClinicalReport, patient_record: dict, knowledge: dict) -> list[Finding]`.
   - Each `Finding` contains: `rule_id`, `severity` (critical | major | minor), `claim_ids`, `message`, and `evidence`.

---

## 5. Consequences

- **Positive**: Absolute reproducibility with 0.0 ms network overhead.
- **Positive**: Strict regulatory compliance; clinical decisions can be audited directly against version-controlled YAML tables.
- **Positive**: Fail-closed deployment safety via automated production draft table rejection.
- **Traceability**: All interaction findings provide direct citation to FDA package insert sections and established clinical consensus guidelines.
