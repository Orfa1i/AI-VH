"""
Acceptance tests for Phase 0 | STEP 03 (P0.3: Observability and artifact versioning).
Written before implementation to verify red-to-green TDD cycle.
"""

import json
import logging
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


@pytest.mark.unit
def test_structured_json_logging():
    """Verify structured JSON logging outputs valid JSON with run_id and step fields."""
    from vh.common.logging import JSONFormatter, set_log_context, clear_log_context

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_step_03.py",
        lineno=25,
        msg="Clinical audit event test",
        args=(),
        exc_info=None
    )

    # Without context
    clear_log_context()
    raw_json_no_ctx = formatter.format(record)
    parsed_no_ctx = json.loads(raw_json_no_ctx)
    assert parsed_no_ctx["message"] == "Clinical audit event test"
    assert parsed_no_ctx["level"] == "INFO"
    assert parsed_no_ctx["run_id"] is None
    assert parsed_no_ctx["step"] is None

    # With context
    set_log_context(run_id="run-42-cardio", step="p03-audit")
    raw_json_ctx = formatter.format(record)
    parsed_ctx = json.loads(raw_json_ctx)
    assert parsed_ctx["run_id"] == "run-42-cardio"
    assert parsed_ctx["step"] == "p03-audit"
    clear_log_context()


@pytest.mark.unit
def test_opentelemetry_tracing_run_id_propagation():
    """Verify that a sample request produces a trace whose spans all share the same run_id."""
    from vh.common.tracing import trace_span, get_current_run_id, get_tracer_provider, get_recorded_spans

    run_id_test = "run-trace-specialist-99"

    with trace_span("parent_consult", run_id=run_id_test) as parent_span:
        assert get_current_run_id() == run_id_test
        with trace_span("child_lab_retrieval") as child_span:
            assert get_current_run_id() == run_id_test
            with trace_span("grandchild_evidence_verify") as grandchild_span:
                assert get_current_run_id() == run_id_test

    # Inspect captured spans
    spans = get_recorded_spans()
    recent = [s for s in spans if s.attributes.get("run_id") == run_id_test]
    assert len(recent) >= 3
    assert all(s.attributes.get("run_id") == run_id_test for s in recent)
    span_names = {s.name for s in recent}
    assert {"parent_consult", "child_lab_retrieval", "grandchild_evidence_verify"}.issubset(span_names)


@pytest.mark.unit
def test_artifact_registry_hashing_and_lineage(tmp_path):
    """Verify artifact hash is identical for identical content, changes when altered, and tracks lineage."""
    from vh.common.artifacts import ArtifactRegistry, ArtifactKind

    registry = ArtifactRegistry(db_path=str(tmp_path / "artifacts.db"), storage_dir=str(tmp_path / "store"))

    content_v1 = b"Heart failure clinical guideline corpus text version 1"
    content_v1_identical = b"Heart failure clinical guideline corpus text version 1"
    content_v2 = b"Heart failure clinical guideline corpus text version 2 (updated)"

    art1 = registry.register_artifact(
        kind=ArtifactKind.DATASET,
        name="hf_corpus",
        version="1.0.0",
        content=content_v1,
        metadata={"author": "Cardiology Panel"}
    )

    art1_copy = registry.register_artifact(
        kind=ArtifactKind.DATASET,
        name="hf_corpus_copy",
        version="1.0.0",
        content=content_v1_identical
    )

    art2 = registry.register_artifact(
        kind=ArtifactKind.DATASET,
        name="hf_corpus",
        version="2.0.0",
        content=content_v2,
        parent_ids=[art1.id]
    )

    # Identical content yields identical sha256 hash
    assert art1.sha256 == art1_copy.sha256
    # Altered content yields different sha256 hash
    assert art1.sha256 != art2.sha256

    # Lineage is retrievable
    lineage = registry.get_lineage(art2.id)
    lineage_ids = [a.id for a in lineage]
    assert art1.id in lineage_ids
    assert art2.id in lineage_ids


@pytest.mark.unit
def test_prompt_template_loader_exact_bytes_and_raises():
    """Verify loading name@version returns exact bytes/text, and unknown version raises."""
    from vh.common.prompts import load_prompt_template, PromptTemplateNotFoundError

    # Known existing template
    content = load_prompt_template("clinical_report@1.0.0")
    assert "CLINICAL REPORT TEMPLATE" in content or "Chief Complaint" in content
    assert len(content) > 20

    # Non-existent version raises PromptTemplateNotFoundError
    with pytest.raises(PromptTemplateNotFoundError):
        load_prompt_template("clinical_report@99.99.99")

    # Missing template name raises PromptTemplateNotFoundError
    with pytest.raises(PromptTemplateNotFoundError):
        load_prompt_template("non_existent_specialist@1.0.0")

    # Invalid spec format raises ValueError
    with pytest.raises(ValueError):
        load_prompt_template("clinical_report_without_at_symbol")


@pytest.mark.unit
def test_llm_wrapper_enforces_prompt_version_and_logs():
    """Verify LLM wrapper refuses calls without prompt version and logs required audit fields."""
    from vh.common.llm import llm_call, LLMCallRecord, MissingPromptVersionError

    # Refuses call without prompt version
    with pytest.raises((MissingPromptVersionError, ValueError)):
        llm_call(prompt="Analyze patient symptoms", model_id="medgemma-4b")

    with pytest.raises((MissingPromptVersionError, ValueError)):
        llm_call(prompt="Analyze patient symptoms", prompt_version=None, model_id="medgemma-4b")

    # Call with prompt version succeeds and produces audit record with all mandatory fields
    record, response = llm_call(
        prompt="Analyze patient with crushing substernal chest pain",
        prompt_version="clinical_report@1.0.0",
        model_id="medgemma-4b"
    )

    assert isinstance(record, LLMCallRecord)
    assert record.model_id == "medgemma-4b"
    assert record.prompt_version == "clinical_report@1.0.0"
    assert len(record.input_hash) == 64  # sha256 hex string
    assert len(record.output_hash) == 64  # sha256 hex string
    assert record.latency >= 0.0
    assert isinstance(record.token_counts, dict)
    assert "prompt_tokens" in record.token_counts
    assert "completion_tokens" in record.token_counts
    assert "total_tokens" in record.token_counts
    assert len(response) > 0
