# STEP 03 Report: P0.3 Observability and artifact versioning

- **Status:** DONE
- **Date:** 2026-09-28
- **Phase:** Phase 0: Foundations, Governance & Evaluation Harness
- **Governing Prompt:** `plan/prompts/phase-0-foundations/STEP-03_P0.3_observability-versioning.md`
- **Governing Standard:** `plan/CLAUDE.md` (Sections 1 to 5)

---

## 1. Built and Modified Deliverables

1. **Structured JSON Logging (`src/vh/common/logging.py`)**:
   - `JSONFormatter`: Serializes log events to single-line JSON with timestamps, log levels, logger names, line numbers, and context fields.
   - Context propagation: Provides `set_log_context`, `clear_log_context`, and `log_context` context manager scoped across threads and async tasks via `contextvars`.
   - Automatic injection of `run_id` and `step` fields into all application and service log records.

2. **OpenTelemetry Tracing (`src/vh/common/tracing.py`)**:
   - Native integration with `opentelemetry-api` and `opentelemetry-sdk`.
   - Propagates `run_id` down the entire call stack across root and child spans via baggage and context variables.
   - Automatically synchronizes span `run_id` with structured JSON logging context.
   - Provides `get_recorded_spans()` and `InMemorySpanExporter` for telemetry verification.
   - Added configuration hook for optional Langfuse tracing exporter behind `ENABLE_LANGFUSE_TRACING`.

3. **Artifact Registry (`src/vh/common/artifacts.py`)**:
   - Manages versioned artifacts across all specified kinds: `dataset`, `index`, `prompt_template`, `model`, `golden_set`, `fault_set`.
   - SHA-256 content hashing guarantees identical hashes for identical content and distinct hashes when altered.
   - Lineage graph tracking: Records `parent_ids` and supports recursive retrieval via `get_lineage(artifact_id)`.
   - Dual-persistence storage: SQLite/PostgreSQL schema metadata table (`artifacts`) paired with structured filesystem binary storage.

4. **Prompt Templates & Versioned Loader (`src/vh/prompt_templates/`, `src/vh/common/prompts.py`)**:
   - Standard directory layout: `src/vh/prompt_templates/<name>/<version>.md`.
   - Seed templates authored: `clinical_report@1.0.0.md` and `triage@1.0.0.md`.
   - Loader `load_prompt_template(spec)` strictly enforces the `name@version` specification, loads exact bytes, and raises `PromptTemplateNotFoundError` on missing templates or versions.

5. **LLM Call Wrapper (`src/vh/common/llm.py`)**:
   - `llm_call()` strictly refuses invocations without an explicit prompt `name@version` (raising `MissingPromptVersionError`).
   - Produces an audit record (`LLMCallRecord`) capturing `model_id`, `prompt_version`, `input_hash` (sha256), `output_hash` (sha256), `latency`, and `token_counts` (`prompt_tokens`, `completion_tokens`, `total_tokens`).
   - Emits structured JSON audit log records for every inference call.

6. **Documentation & Plan Updates**:
   - Marked STEP 03 complete in `plan/README.md`.
   - Exported all symbols cleanly in `src/vh/common/__init__.py`.

---

## 2. Tests Added and Full Suite Verification

- **Tests Added**: `tests/test_step_03_acceptance.py` (5 test cases):
  - `test_structured_json_logging`: Validates JSON formatting, run_id and step propagation.
  - `test_opentelemetry_tracing_run_id_propagation`: Validates trace span creation and run_id inheritance across parent and child spans.
  - `test_artifact_registry_hashing_and_lineage`: Proves content hash determinism and lineage retrieval.
  - `test_prompt_template_loader_exact_bytes_and_raises`: Proves exact template byte loading and unknown version exceptions.
  - `test_llm_wrapper_enforces_prompt_version_and_logs`: Proves prompt version enforcement and complete audit field generation.

- **Full Suite Result**:
  - `pytest`: **82 passed out of 82** (100% pass rate in 276.11s).
  - Breakdown: 5 Step 03 tests + 10 Step 02 tests + 67 existing backend tests.
  - Secret scan (`py -3.13 scripts/scan_secrets.py`): **0 secrets detected**.

---

## 3. Failures Found and Resolved

1. **InMemorySpanExporter Module Path in OpenTelemetry SDK**:
   - *Symptom:* `from opentelemetry.sdk.trace.export import InMemorySpanExporter` raised `ImportError`.
   - *Root Cause:* In recent OpenTelemetry SDK versions, `InMemorySpanExporter` is located in `opentelemetry.sdk.trace.export.in_memory_span_exporter`.
   - *Fix:* Updated import to load from `in_memory_span_exporter` with a graceful fallback `SpanExporter` implementation.
   - *Regression Test:* `tests/test_step_03_acceptance.py::test_opentelemetry_tracing_run_id_propagation`.

---

## 4. Gap Review

| Acceptance Criterion | Evidence / Proof File | Status |
| :--- | :--- | :--- |
| Sample request produces one trace whose spans all share the same run_id | `tests/test_step_03_acceptance.py::test_opentelemetry_tracing_run_id_propagation` | SATISFIED |
| Artifact hash identical for identical content, changes when altered, lineage retrievable | `tests/test_step_03_acceptance.py::test_artifact_registry_hashing_and_lineage` | SATISFIED |
| Loading name@version returns exact bytes, unknown version raises | `tests/test_step_03_acceptance.py::test_prompt_template_loader_exact_bytes_and_raises` | SATISFIED |
| LLM wrapper raises without prompt version; with one, log record has all listed fields | `tests/test_step_03_acceptance.py::test_llm_wrapper_enforces_prompt_version_and_logs` | SATISFIED |

---

## 5. Open Questions and Assumptions

- *Open questions:* None.
- *Assumptions:* Default artifact registry stores metadata in `data/artifacts.db` and files in `data/artifact_store/`, compatible with PostgreSQL migrations when docker compose is active.
