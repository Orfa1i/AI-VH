"""
Acceptance criteria tests for STEP 20 (P3.1):
Clinical report schema with claim-evidence links, referential integrity validation,
and JSON Schema export for MedGemma constrained decoding.
"""

from pathlib import Path
import json
import pytest
from pydantic import ValidationError

from vh.generation.report import (
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ClaimItem,
    AbstentionItem,
    ReportProvenance,
    validate_clinical_report,
    IntegrityValidationError,
    MissingClaimError,
    UnresolvedEvidenceError,
    EmptyClaimsError,
    export_clinical_report_json_schema,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def valid_report_data():
    return {
        "patient_summary": "58-year-old male presenting with acute crushing substernal chest discomfort radiating to left arm and diaphoresis.",
        "findings": [
            "12-Lead ECG demonstrates 2.5mm ST-segment elevation in leads V1-V4",
            "High-sensitivity cardiac troponin I elevated at 450 ng/L",
        ],
        "differential": [
            {
                "dx": "Acute Anterior ST-Elevation Myocardial Infarction",
                "likelihood": "high",
                "claim_ids": ["claim-001"],
            },
            {
                "dx": "Acute Pericarditis",
                "likelihood": "low",
                "claim_ids": ["claim-002"],
            },
        ],
        "recommendations": [
            {
                "text": "Immediate cardiac catheterization laboratory activation for primary percutaneous coronary intervention (PCI).",
                "claim_ids": ["claim-003"],
            },
            {
                "text": "Administer chewable non-enteric-coated aspirin 325 mg immediately.",
                "claim_ids": ["claim-004"],
            },
        ],
        "claims": [
            {
                "claim_id": "claim-001",
                "text": "ST-segment elevation in contiguous precordial leads with elevated troponin indicates acute myocardial infarction.",
                "type": "diagnostic",
                "evidence_ids": ["v1.0:4905f8261347e3a5"],
            },
            {
                "claim_id": "claim-002",
                "text": "Focal ST elevation without PR depression and positive troponin makes acute pericarditis less probable than STEMI.",
                "type": "diagnostic",
                "evidence_ids": ["v1.0:4905f8261347e3a5"],
            },
            {
                "claim_id": "claim-003",
                "text": "Primary PCI is the preferred reperfusion strategy for STEMI presenting within 12 hours of symptom onset.",
                "type": "therapeutic",
                "evidence_ids": ["v1.0:06b83d3a88aa2a25"],
            },
            {
                "claim_id": "claim-004",
                "text": "Non-enteric aspirin 162 to 325 mg administered promptly reduces acute coronary mortality.",
                "type": "therapeutic",
                "evidence_ids": ["v1.0:06b83d3a88aa2a25"],
            },
        ],
        "abstentions": [
            {
                "question": "Immediate beta-blocker administration route",
                "reason": "Patient hemodynamic stability parameters (Killip class) not yet determined in emergency triage.",
            }
        ],
        "provenance": {
            "run_id": "run-test-gen-001",
            "model_id": "medgemma-27b-it-4bit",
            "prompt_name_version": "clinical_report@1.0.0",
            "index_version": "v1.0",
            "case_id": "GOLDEN-DRAFT-ACS-001",
        },
    }


@pytest.fixture
def retrieval_context_ids():
    return {
        "v1.0:4905f8261347e3a5",
        "v1.0:06b83d3a88aa2a25",
        "v1.0:9759b42651a3557c",
        "v1.0:f4e73a22c150cdcb",
    }


def test_valid_clinical_report_fixture_passes_validation(valid_report_data, retrieval_context_ids):
    """Verify that a syntactically valid and referentially intact report passes validation."""
    report = ClinicalReport(**valid_report_data)
    is_valid = validate_clinical_report(report, valid_evidence_ids=retrieval_context_ids)
    assert is_valid is True


def test_integrity_violation_missing_claim(valid_report_data, retrieval_context_ids):
    """Verify that referencing a non-existent claim_id in differential or recommendations raises MissingClaimError."""
    # Corrupt differential reference
    bad_data = dict(valid_report_data)
    bad_data["differential"] = [
        {
            "dx": "Acute Coronary Syndrome",
            "likelihood": "high",
            "claim_ids": ["claim-nonexistent"],
        }
    ]
    report = ClinicalReport(**bad_data)
    with pytest.raises(MissingClaimError) as exc_info:
        validate_clinical_report(report, valid_evidence_ids=retrieval_context_ids)
    assert "claim-nonexistent" in str(exc_info.value)

    # Corrupt recommendation reference
    bad_rec_data = dict(valid_report_data)
    bad_rec_data["recommendations"] = [
        {
            "text": "Administer nitroglycerin sublingual.",
            "claim_ids": ["claim-ghost-id"],
        }
    ]
    report2 = ClinicalReport(**bad_rec_data)
    with pytest.raises(MissingClaimError) as exc_info2:
        validate_clinical_report(report2, valid_evidence_ids=retrieval_context_ids)
    assert "claim-ghost-id" in str(exc_info2.value)


def test_integrity_violation_unresolved_evidence(valid_report_data, retrieval_context_ids):
    """Verify that referencing an evidence_id not present in retrieval context raises UnresolvedEvidenceError."""
    bad_data = dict(valid_report_data)
    bad_data["claims"] = [
        {
            "claim_id": "claim-001",
            "text": "Diagnostic claim with hallucinated citation",
            "type": "diagnostic",
            "evidence_ids": ["v1.0:hallucinated_chunk_id_999"],
        }
    ]
    bad_data["differential"] = [
        {
            "dx": "STEMI",
            "likelihood": "high",
            "claim_ids": ["claim-001"],
        }
    ]
    bad_data["recommendations"] = [
        {
            "text": "Immediate catheterization",
            "claim_ids": ["claim-001"],
        }
    ]
    report = ClinicalReport(**bad_data)
    with pytest.raises(UnresolvedEvidenceError) as exc_info:
        validate_clinical_report(report, valid_evidence_ids=retrieval_context_ids)
    assert "hallucinated_chunk_id_999" in str(exc_info.value)


def test_integrity_violation_empty_claims(valid_report_data, retrieval_context_ids):
    """Verify that differential or recommendation entries with empty claim_ids raise EmptyClaimsError."""
    # Empty claim_ids in recommendation
    bad_data = dict(valid_report_data)
    bad_data["recommendations"] = [
        {
            "text": "Unsupported therapy without grounding claims",
            "claim_ids": [],
        }
    ]
    report = ClinicalReport(**bad_data)
    with pytest.raises(EmptyClaimsError) as exc_info:
        validate_clinical_report(report, valid_evidence_ids=retrieval_context_ids)
    assert "claim_ids" in str(exc_info.value)

    # Empty claim_ids in differential
    bad_diff = dict(valid_report_data)
    bad_diff["differential"] = [
        {
            "dx": "Unsupported Diagnosis",
            "likelihood": "moderate",
            "claim_ids": [],
        }
    ]
    report2 = ClinicalReport(**bad_diff)
    with pytest.raises(EmptyClaimsError) as exc_info2:
        validate_clinical_report(report2, valid_evidence_ids=retrieval_context_ids)
    assert "claim_ids" in str(exc_info2.value)


def test_schema_type_constraints(valid_report_data):
    """Verify schema constraints on likelihood and claim types."""
    # Invalid likelihood
    bad_data = dict(valid_report_data)
    bad_data["differential"] = [
        {
            "dx": "ACS",
            "likelihood": "possible",  # invalid literal
            "claim_ids": ["claim-001"],
        }
    ]
    with pytest.raises(ValidationError):
        ClinicalReport(**bad_data)

    # Invalid claim type
    bad_claim = dict(valid_report_data)
    bad_claim["claims"] = [
        {
            "claim_id": "claim-001",
            "text": "Speculative assessment",
            "type": "speculation",  # invalid literal
            "evidence_ids": ["v1.0:4905f8261347e3a5"],
        }
    ]
    with pytest.raises(ValidationError):
        ClinicalReport(**bad_claim)


def test_exported_json_schema_matches_model():
    """Verify that exported schemas/clinical_report.json exists and strictly matches the Pydantic model schema."""
    schema_path = REPO_ROOT / "schemas" / "clinical_report.json"
    # Ensure export function runs
    exported_schema = export_clinical_report_json_schema(output_path=schema_path)

    assert schema_path.exists(), "schemas/clinical_report.json must exist"
    disk_schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Assert exact model schema parity
    model_schema = ClinicalReport.model_json_schema()
    assert disk_schema == model_schema
    assert exported_schema == model_schema
    assert "properties" in disk_schema
    assert "differential" in disk_schema["properties"]
    assert "recommendations" in disk_schema["properties"]
    assert "claims" in disk_schema["properties"]
    assert "abstentions" in disk_schema["properties"]
    assert "provenance" in disk_schema["properties"]
