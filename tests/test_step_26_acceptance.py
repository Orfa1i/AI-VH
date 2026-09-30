"""
Acceptance tests for Step 26: P4.2 Claim Grounding and Citation Checker.
Tests:
- Claim-level grounding verdicts (supported, partial, unsupported) with rationales
- Evidence citation validation (detects unretrieved/missing evidence IDs)
- Strict judge isolation (judge context receives only claim and cited chunk text)
- Determinism and zero-temperature repeatability
- Cohen's kappa calibration scoring on known fixture distributions
- Calibration export and scoring CLI workflows
"""

from pathlib import Path
import pytest

from vh.generation.report import (
    ClaimItem,
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ReportProvenance,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def make_dummy_report(
    claims: list[ClaimItem],
    recommendations: list[str] = None,
    differential: list[str] = None,
) -> ClinicalReport:
    """Helper to assemble a ClinicalReport instance for grounding verification."""
    diff_items = [
        DifferentialItem(dx=d, likelihood="high", claim_ids=[claims[0].claim_id] if claims else [])
        for d in (differential or ["Acute Coronary Syndrome"])
    ]
    rec_items = [
        RecommendationItem(text=r, claim_ids=[claims[0].claim_id] if claims else [])
        for r in (recommendations or ["Administer dual antiplatelet therapy."])
    ]
    return ClinicalReport(
        patient_summary="62-year-old presenting with acute chest pressure.",
        findings=["Elevated cardiac troponin I", "Anterior ST-elevation"],
        differential=diff_items,
        recommendations=rec_items,
        claims=claims,
        abstentions=[],
        provenance=ReportProvenance(
            run_id="run-step-26-test",
            model_id="medgemma-4b",
            prompt_name_version="clinical_report@1.0.0",
            index_version="idx-v1",
            case_id="CASE-GROUNDING-01",
        ),
    )


# -----------------------------------------------------------------------------
# 1. Grounding Judgments: Supported, Partial, Unsupported
# -----------------------------------------------------------------------------

def test_grounding_checker_supported_claim():
    """Verify that a claim directly substantiated by cited evidence is judged 'supported'."""
    from vh.verification.grounding import ClaimGroundingChecker, GroundingVerdict

    checker = ClaimGroundingChecker()
    claim = ClaimItem(
        claim_id="CLM-SUPP-01",
        text="Aspirin 325 mg should be administered immediately upon suspected acute coronary syndrome.",
        type="therapeutic",
        evidence_ids=["CHUNK-ACC-001"],
    )
    retrieved_chunks = {
        "CHUNK-ACC-001": (
            "ACC/AHA Guidelines for STEMI: Non-enteric-coated chewable aspirin 162 mg to 325 mg "
            "should be administered promptly to all patients with suspected acute coronary syndromes."
        )
    }

    judgment = checker.judge_claim(claim, retrieved_chunks)
    assert judgment.claim_id == "CLM-SUPP-01"
    assert judgment.citation_valid is True
    assert judgment.verdict == GroundingVerdict.SUPPORTED
    assert judgment.verdict == "supported"
    assert len(judgment.rationale) > 5


def test_grounding_checker_unsupported_contradicted_claim():
    """Verify that a claim refuted or contradicted by cited evidence is judged 'unsupported'."""
    from vh.verification.grounding import ClaimGroundingChecker, GroundingVerdict

    checker = ClaimGroundingChecker()
    claim = ClaimItem(
        claim_id="CLM-UNSUPP-01",
        text="Nitrates are strongly recommended in patients with hypotension (systolic BP < 90 mmHg).",
        type="therapeutic",
        evidence_ids=["CHUNK-ACC-002"],
    )
    retrieved_chunks = {
        "CHUNK-ACC-002": (
            "ACC/AHA STEMI Guidelines: Nitrates are strictly contraindicated in patients with "
            "hypotension (systolic blood pressure < 90 mmHg or >= 30 mmHg below baseline) or bradycardia."
        )
    }

    judgment = checker.judge_claim(claim, retrieved_chunks)
    assert judgment.citation_valid is True
    assert judgment.verdict == GroundingVerdict.UNSUPPORTED
    assert judgment.verdict == "unsupported"
    assert len(judgment.rationale) > 5


def test_grounding_checker_partial_claim():
    """Verify that a claim with true core premise but ungrounded extra details is judged 'partial'."""
    from vh.verification.grounding import ClaimGroundingChecker, GroundingVerdict

    checker = ClaimGroundingChecker()
    claim = ClaimItem(
        claim_id="CLM-PARTIAL-01",
        text="Metformin reduces HbA1c and guarantees total reversal of diabetic retinopathy within 6 months.",
        type="diagnostic",
        evidence_ids=["CHUNK-ADA-001"],
    )
    retrieved_chunks = {
        "CHUNK-ADA-001": (
            "ADA Standards of Care: Metformin remains the preferred initial pharmacologic agent "
            "for the treatment of type 2 diabetes and effectively lowers HbA1c levels."
        )
    }

    judgment = checker.judge_claim(claim, retrieved_chunks)
    assert judgment.citation_valid is True
    assert judgment.verdict == GroundingVerdict.PARTIAL
    assert judgment.verdict == "partial"
    assert len(judgment.rationale) > 5


# -----------------------------------------------------------------------------
# 2. Citation Check: Unretrieved or Missing Evidence IDs
# -----------------------------------------------------------------------------

def test_citation_check_detects_unretrieved_evidence_id():
    """Verify that citing an evidence ID that was not retrieved in this encounter fails closed as unsupported."""
    from vh.verification.grounding import ClaimGroundingChecker, GroundingVerdict

    checker = ClaimGroundingChecker()
    claim = ClaimItem(
        claim_id="CLM-MISS-01",
        text="Statins should be prescribed for secondary prevention.",
        type="therapeutic",
        evidence_ids=["CHUNK-GHOST-999"],
    )
    # Retrieved chunks does not contain CHUNK-GHOST-999
    retrieved_chunks = {
        "CHUNK-VALID-001": "Lifestyle modifications are indicated."
    }

    judgment = checker.judge_claim(claim, retrieved_chunks)
    assert judgment.citation_valid is False
    assert judgment.verdict == GroundingVerdict.UNSUPPORTED
    assert "not retrieved" in judgment.rationale.lower() or "missing" in judgment.rationale.lower()


def test_report_evaluation_aggregates_grounding_metrics():
    """Verify evaluate_report aggregates total claims, verdicts, and grounding ratio."""
    from vh.verification.grounding import ClaimGroundingChecker

    checker = ClaimGroundingChecker()
    claims = [
        ClaimItem(
            claim_id="C1",
            text="Aspirin 325 mg indicated.",
            type="therapeutic",
            evidence_ids=["CHUNK-1"],
        ),
        ClaimItem(
            claim_id="C2",
            text="Nitrates recommended in severe shock.",
            type="therapeutic",
            evidence_ids=["CHUNK-2"],
        ),
        ClaimItem(
            claim_id="C3",
            text="Uncited assertion without retrieved evidence.",
            type="diagnostic",
            evidence_ids=["CHUNK-NONEXISTENT"],
        ),
    ]
    report = make_dummy_report(claims)
    retrieved_chunks = {
        "CHUNK-1": "Aspirin 325 mg should be administered for ACS.",
        "CHUNK-2": "Nitrates are contraindicated in hypotension and cardiogenic shock.",
    }

    res = checker.evaluate_report(report, retrieved_chunks)
    assert res.total_claims == 3
    assert res.supported_count == 1
    assert res.unsupported_count == 2
    assert res.invalid_citation_count == 1
    assert res.passed is False


# -----------------------------------------------------------------------------
# 3. Judge Isolation: Only Claim and Cited Chunk Visible
# -----------------------------------------------------------------------------

def test_judge_isolation_only_sees_claim_and_cited_chunk():
    """Verify that judge receives only the claim and its cited evidence text."""
    from vh.verification.grounding import ClaimGroundingChecker

    checker = ClaimGroundingChecker()
    claim = ClaimItem(
        claim_id="C-ISO-01",
        text="Target blood pressure is below 130/80 mmHg.",
        type="therapeutic",
        evidence_ids=["CHUNK-ISO-1"],
    )
    retrieved_chunks = {
        "CHUNK-ISO-1": "Target blood pressure in hypertensive patients is < 130/80 mmHg.",
        "CHUNK-SECRET-2": "HIDDEN DIAGNOSIS: Pheochromocytoma secret case truth.",
    }

    payload = checker.build_judge_prompt_inputs(claim, retrieved_chunks)
    assert "Target blood pressure is below 130/80 mmHg." in payload["claim_text"]
    assert "Target blood pressure in hypertensive patients is < 130/80 mmHg." in payload["evidence_text"]
    # Secret or irrelevant chunks must NOT appear in the judge payload
    assert "Pheochromocytoma" not in payload["evidence_text"]
    assert "CHUNK-SECRET-2" not in payload["evidence_text"]


# -----------------------------------------------------------------------------
# 4. Determinism Property Test
# -----------------------------------------------------------------------------

def test_grounding_checker_determinism_property():
    """Property test: Repeated evaluations on identical claim-evidence pairs yield bit-for-bit identical results."""
    from vh.verification.grounding import ClaimGroundingChecker

    checker = ClaimGroundingChecker()
    claim = ClaimItem(
        claim_id="C-DET-01",
        text="Aspirin 325 mg should be administered immediately.",
        type="therapeutic",
        evidence_ids=["CHUNK-DET-1"],
    )
    chunks = {"CHUNK-DET-1": "Aspirin 162-325 mg should be given immediately in ACS."}

    judgments = [checker.judge_claim(claim, chunks) for _ in range(5)]
    first = judgments[0]
    for j in judgments[1:]:
        assert j.verdict == first.verdict
        assert j.citation_valid == first.citation_valid
        assert j.rationale == first.rationale


# -----------------------------------------------------------------------------
# 5. Cohen's Kappa & Calibration Scoring Fixture Test
# -----------------------------------------------------------------------------

def test_cohens_kappa_calculation_known_fixture():
    """Verify Cohen's kappa calculation on known synthetic distributions."""
    from vh.verification.grounding import compute_cohens_kappa

    # Case A: Perfect agreement -> Kappa = 1.0
    r1 = ["supported", "partial", "unsupported", "supported"]
    r2 = ["supported", "partial", "unsupported", "supported"]
    assert pytest.approx(compute_cohens_kappa(r1, r2), rel=1e-4) == 1.0

    # Case B: Standard 2x2 known textbook example
    # rater1: 10 yes, 10 no
    # rater2: 8 yes when rater1 yes, 2 no when rater1 yes; 3 yes when rater1 no, 7 no when rater1 no
    # Po = (8 + 7) / 20 = 15/20 = 0.75
    # Pe = (10/20)*(11/20) + (10/20)*(9/20) = 0.5*0.55 + 0.5*0.45 = 0.275 + 0.225 = 0.50
    # Kappa = (0.75 - 0.50) / (1 - 0.50) = 0.25 / 0.50 = 0.50
    t1 = ["yes"] * 10 + ["no"] * 10
    t2 = ["yes"] * 8 + ["no"] * 2 + ["yes"] * 3 + ["no"] * 7
    assert pytest.approx(compute_cohens_kappa(t1, t2), rel=1e-4) == 0.50


# -----------------------------------------------------------------------------
# 6. Calibration Export and Score CLI Workflows
# -----------------------------------------------------------------------------

def test_calibration_export_and_score_cli(tmp_path):
    """Verify vh verify calibration-export and calibration-score CLI commands."""
    from vh.verification.cli import run_calibration_export, run_calibration_score

    export_file = tmp_path / "calibration_pairs_100.csv"
    ret = run_calibration_export(n=100, output_path=export_file)
    assert ret == 0
    assert export_file.exists()

    content = export_file.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    # 1 header + 100 data rows = 101 lines
    assert len(lines) == 101
    assert "pair_id" in lines[0]
    assert "physician_label" in lines[0]

    # Score against the generated file (which has expected categories pre-populated for testing)
    score_ret, metrics = run_calibration_score(labels_path=export_file)
    assert score_ret == 0
    assert "cohens_kappa" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["total_pairs"] == 100
