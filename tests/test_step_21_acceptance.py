"""
Acceptance tests for Step 21: P3.2 MedGemma Adapter.
Verifies retry logic with feedback, failure on retry exhaustion, prompt versioning,
call logging, timeout enforcement, concurrency throttling, and real endpoint integration.
"""

import json
import logging
import time
import pytest
from typing import Any, Dict, List
from unittest.mock import MagicMock

from vh.generation.report import (
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ClaimItem,
    AbstentionItem,
    ReportProvenance,
    validate_clinical_report,
)
from vh.generation.medgemma import (
    MedGemmaAdapter,
    MedGemmaConfig,
    GenerationFailed,
    GenerationTimeoutError,
    MissingPromptVersionError,
)


def _make_valid_report_dict(evidence_id: str = "CHUNK-001") -> Dict[str, Any]:
    """Helper to produce a schema-valid ClinicalReport dictionary."""
    return {
        "patient_summary": "62-year-old male with progressive retrosternal chest tightness.",
        "findings": [
            "ECG demonstrates ST depressions in inferior leads",
            "High-sensitivity troponin I elevated at 450 ng/L",
        ],
        "differential": [
            DifferentialItem(
                dx="Acute Non-ST-Elevation Myocardial Infarction (NSTEMI)",
                likelihood="high",
                claim_ids=["CLM-001", "CLM-002"],
            ).model_dump(),
            DifferentialItem(
                dx="Unstable Angina",
                likelihood="low",
                claim_ids=["CLM-001"],
            ).model_dump(),
        ],
        "recommendations": [
            RecommendationItem(
                text="Administer chewable aspirin 325 mg immediately.",
                claim_ids=["CLM-003"],
            ).model_dump()
        ],
        "claims": [
            ClaimItem(
                claim_id="CLM-001",
                text="Patient symptoms and ischemic changes indicate acute myocardial ischemia.",
                type="diagnostic",
                evidence_ids=[evidence_id],
            ).model_dump(),
            ClaimItem(
                claim_id="CLM-002",
                text="Elevated troponin confirms myocardial infarction rather than unstable angina.",
                type="diagnostic",
                evidence_ids=[evidence_id],
            ).model_dump(),
            ClaimItem(
                claim_id="CLM-003",
                text="Early antiplatelet therapy reduces recurrent ischemic events and mortality.",
                type="therapeutic",
                evidence_ids=[evidence_id],
            ).model_dump(),
        ],
        "abstentions": [
            AbstentionItem(
                question="Long-term dual antiplatelet therapy duration in renal impairment.",
                reason="Patient renal panel is pending and outside active guideline scope.",
            ).model_dump()
        ],
        "provenance": ReportProvenance(
            run_id="run-step21-test",
            model_id="google/medgemma-4b",
            prompt_name_version="clinical_report@1.0.0",
            index_version="idx-v1",
            case_id="CASE-101",
        ).model_dump(),
    }


def test_retry_logic_invalid_then_valid():
    """Verifies that invalid JSON on attempt 1 triggers retry with feedback, resolving on attempt 2."""
    valid_data = _make_valid_report_dict("CHUNK-001")
    valid_json_text = json.dumps(valid_data)

    calls: List[str] = []

    def mock_model_runner(prompt: str, **kwargs: Any) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            # First attempt returns malformed JSON
            return "```json\n{ malformed_json_here: true, \n```"
        # Second attempt returns valid schema JSON
        return f"```json\n{valid_json_text}\n```"

    config = MedGemmaConfig(max_retries=3, model_id="medgemma-mock")
    adapter = MedGemmaAdapter(config=config, runner=mock_model_runner)

    inputs = {
        "patient_summary": "62yo male with retrosternal chest pain",
        "retrieved_evidence": [{"chunk_id": "CHUNK-001", "text": "Aspirin reduces mortality in NSTEMI."}],
        "active_evidence_ids": ["CHUNK-001"],
        "case_id": "CASE-101",
        "run_id": "run-step21-test",
    }

    report = adapter.generate(
        prompt_name_version="clinical_report@1.0.0",
        inputs=inputs,
        response_schema=ClinicalReport,
    )

    assert isinstance(report, ClinicalReport)
    assert len(calls) == 2
    assert "VALIDATION ERROR ON PREVIOUS ATTEMPT" in calls[1]
    assert report.differential[0].dx.startswith("Acute Non-ST")


def test_retry_logic_exhaustion_raises_generation_failed():
    """Verifies that repeated schema or JSON failures raise GenerationFailed after max_retries."""
    calls: List[str] = []

    def mock_broken_runner(prompt: str, **kwargs: Any) -> str:
        calls.append(prompt)
        # Always return missing required fields
        return json.dumps({"patient_summary": "Incomplete report without required differential"})

    config = MedGemmaConfig(max_retries=3, model_id="medgemma-mock")
    adapter = MedGemmaAdapter(config=config, runner=mock_broken_runner)

    inputs = {
        "patient_summary": "Patient data",
        "active_evidence_ids": ["CHUNK-001"],
    }

    with pytest.raises(GenerationFailed) as exc_info:
        adapter.generate(
            prompt_name_version="clinical_report@1.0.0",
            inputs=inputs,
            response_schema=ClinicalReport,
        )

    assert len(calls) == 3
    assert "failed after 3 attempts" in str(exc_info.value).lower()


def test_missing_prompt_version_raises():
    """Verifies that attempting generation without a valid name@version specification raises."""
    adapter = MedGemmaAdapter()

    with pytest.raises(MissingPromptVersionError):
        adapter.generate(prompt_name_version="", inputs={})

    with pytest.raises(MissingPromptVersionError):
        adapter.generate(prompt_name_version="no_version_tag", inputs={})


def test_every_call_is_logged_with_prompt_version(caplog):
    """Verifies that every adapter call logs telemetry including prompt version."""
    valid_data = _make_valid_report_dict("CHUNK-001")
    runner = MagicMock(return_value=json.dumps(valid_data))

    adapter = MedGemmaAdapter(runner=runner)

    with caplog.at_level(logging.INFO, logger="vh.generation.medgemma"):
        adapter.generate(
            prompt_name_version="clinical_report@1.0.0",
            inputs={"active_evidence_ids": ["CHUNK-001"]},
            response_schema=ClinicalReport,
        )

    log_messages = [record.message for record in caplog.records]
    assert any("clinical_report@1.0.0" in msg for msg in log_messages)


def test_timeout_raises_generation_timeout_error():
    """Verifies that a call exceeding the configured timeout raises GenerationTimeoutError."""
    def slow_runner(prompt: str, **kwargs: Any) -> str:
        time.sleep(0.5)
        return json.dumps(_make_valid_report_dict())

    config = MedGemmaConfig(timeout_s=0.1, max_retries=1)
    adapter = MedGemmaAdapter(config=config, runner=slow_runner)

    with pytest.raises(GenerationTimeoutError):
        adapter.generate(
            prompt_name_version="clinical_report@1.0.0",
            inputs={"active_evidence_ids": ["CHUNK-001"]},
            response_schema=ClinicalReport,
        )


def test_concurrency_limit_enforced():
    """Verifies that concurrent requests are limited by the configured concurrency semaphore."""
    active_concurrent = 0
    max_observed_concurrent = 0

    def concurrent_runner(prompt: str, **kwargs: Any) -> str:
        nonlocal active_concurrent, max_observed_concurrent
        active_concurrent += 1
        if active_concurrent > max_observed_concurrent:
            max_observed_concurrent = active_concurrent
        time.sleep(0.05)
        active_concurrent -= 1
        return json.dumps(_make_valid_report_dict())

    config = MedGemmaConfig(max_concurrency=2, max_retries=1)
    adapter = MedGemmaAdapter(config=config, runner=concurrent_runner)

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(
                adapter.generate,
                "clinical_report@1.0.0",
                {"active_evidence_ids": ["CHUNK-001"]},
                ClinicalReport,
            )
            for _ in range(6)
        ]
        results = [f.result() for f in futures]

    assert len(results) == 6
    assert max_observed_concurrent <= 2


@pytest.mark.integration
def test_real_endpoint_integration_fixture_case():
    """
    Integration test against the MedGemma generation service using a realistic clinical fixture.
    Proves that a schema-valid report is generated and referential integrity passes.
    """
    adapter = MedGemmaAdapter()

    fixture_inputs = {
        "case_id": "CASE-101",
        "run_id": "run-step21-integration",
        "patient_summary": (
            "62-year-old male presenting with 3-hour history of severe retrosternal "
            "chest pressure radiating to left shoulder and jaw, diaphoresis, and nausea. "
            "Past history of hypertension and hyperlipidemia."
        ),
        "findings": [
            "ECG: 2 mm ST-segment depression in leads II, III, and aVF",
            "High-sensitivity cardiac troponin I: 480 ng/L (reference < 14 ng/L)",
            "Blood pressure: 154/92 mmHg, Heart rate: 98 bpm",
        ],
        "retrieved_evidence": [
            {
                "chunk_id": "CHUNK-AHA-ACS-01",
                "source": "guideline_aha_acc_nstemi",
                "title": "AHA/ACC Guideline for Non-ST-Elevation Acute Coronary Syndromes",
                "text": (
                    "In patients with suspected NSTEMI, chewable aspirin (162 to 325 mg) should be "
                    "administered immediately. Anticoagulation with unfractionated heparin or enoxaparin "
                    "is recommended. Ischemic symptoms combined with cardiac biomarker elevation confirm "
                    "acute myocardial infarction."
                ),
            }
        ],
        "active_evidence_ids": ["CHUNK-AHA-ACS-01"],
    }

    report = adapter.generate(
        prompt_name_version="clinical_report@1.0.0",
        inputs=fixture_inputs,
        response_schema=ClinicalReport,
    )

    assert isinstance(report, ClinicalReport)
    assert len(report.differential) >= 1
    assert len(report.recommendations) >= 1
    assert len(report.claims) >= 1

    # Referential integrity verification
    validate_clinical_report(report, valid_evidence_ids=["CHUNK-AHA-ACS-01"])

    # Provenance audit verification
    assert report.provenance.prompt_name_version == "clinical_report@1.0.0"
    assert report.provenance.case_id == "CASE-101"


def test_generation_rest_api_endpoint():
    """Verifies that the FastAPI POST /api/generation/generate endpoint produces a schema-valid response."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    payload = {
        "prompt_name_version": "clinical_report@1.0.0",
        "inputs": {
            "case_id": "CASE-101",
            "run_id": "run-step21-api",
            "patient_summary": "62-year-old male with acute coronary syndrome symptoms.",
            "findings": ["Elevated troponin", "ST depression"],
            "retrieved_evidence": [
                {
                    "chunk_id": "CHUNK-AHA-01",
                    "source": "guidelines",
                    "title": "AHA ACS",
                    "text": "Administer aspirin immediately for NSTEMI.",
                }
            ],
            "active_evidence_ids": ["CHUNK-AHA-01"],
        },
    }

    response = client.post("/api/generation/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "differential" in data
    assert len(data["differential"]) >= 1
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    assert "claims" in data
    assert len(data["claims"]) >= 1
    assert data["provenance"]["prompt_name_version"] == "clinical_report@1.0.0"

