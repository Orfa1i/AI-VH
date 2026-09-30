"""
Acceptance tests for Step 25: P4.1 Deterministic Safety Rules Engine.
Tests deterministic clinical safety rules (allergy, contraindication, drug interaction,
dose/renal adjustment, patient data contradiction, and red-flag coverage),
ensuring zero LLM dependency, strict determinism, and production-mode draft table rejection.
"""

from pathlib import Path
from typing import Any, Dict, List
import pytest

from vh.generation.report import (
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ClaimItem,
    AbstentionItem,
    ReportProvenance,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def make_dummy_report(
    recommendations: List[str],
    differential: List[str] = None,
    patient_summary: str = "60-year-old presenting with acute chest discomfort.",
    findings: List[str] = None,
) -> ClinicalReport:
    """Helper to assemble a valid ClinicalReport instance for safety testing."""
    diff_items = [
        DifferentialItem(dx=d, likelihood="high", claim_ids=["CLM-01"])
        for d in (differential or ["Acute Coronary Syndrome"])
    ]
    rec_items = [
        RecommendationItem(text=r, claim_ids=["CLM-01"])
        for r in recommendations
    ]
    return ClinicalReport(
        patient_summary=patient_summary,
        findings=findings or ["Elevated troponin", "ST depression"],
        differential=diff_items,
        recommendations=rec_items,
        claims=[
            ClaimItem(
                claim_id="CLM-01",
                text="Standard guideline therapy indicated.",
                type="therapeutic",
                evidence_ids=["CHUNK-EVID-01"],
            )
        ],
        abstentions=[],
        provenance=ReportProvenance(
            run_id="run-test",
            model_id="medgemma-4b",
            prompt_name_version="clinical_report@1.0.0",
            index_version="idx-v1",
            case_id="CASE-SAFE-01",
        ),
    )


# -----------------------------------------------------------------------------
# 1. Production Mode Draft Table Rejection
# -----------------------------------------------------------------------------

def test_engine_refuses_draft_tables_in_production():
    """Verify engine raises SafetyConfigurationError when loaded with draft tables in production mode."""
    from vh.verification.rules.engine import (
        DeterministicSafetyEngine,
        SafetyConfigurationError,
    )

    # In production mode, tables containing 'status: draft' MUST trigger failure
    with pytest.raises(SafetyConfigurationError) as exc_info:
        engine = DeterministicSafetyEngine(mode="production")
        report = make_dummy_report(["Administer Aspirin 325 mg po"])
        engine.evaluate(report=report, patient_record={})

    assert "draft" in str(exc_info.value).lower()


def test_engine_allows_draft_tables_in_dev_with_warning(caplog):
    """Verify engine permits draft tables in dev mode with explicit warning logs."""
    from vh.verification.rules.engine import DeterministicSafetyEngine

    engine = DeterministicSafetyEngine(mode="dev")
    report = make_dummy_report(["Administer Aspirin 325 mg po"])
    result = engine.evaluate(report=report, patient_record={})

    assert result is not None
    assert any("draft" in record.message.lower() for record in caplog.records)


# -----------------------------------------------------------------------------
# 2. Allergy Rule: Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_allergy_rule_positive_and_negative():
    """Positive: Flags recommended drug when patient has documented allergy. Negative: Permits safe drugs."""
    from vh.verification.rules.allergy import AllergyRule

    rule = AllergyRule()

    # Patient allergic to Penicillin and Aspirin
    patient_record = {
        "allergies": [
            {"substance": "Aspirin", "reaction": "Anaphylaxis", "severity": "severe"},
            {"substance": "Penicillin", "reaction": "Urticaria", "severity": "moderate"},
        ]
    }

    # POSITIVE: Recommending Aspirin must trigger critical finding
    unsafe_report = make_dummy_report(["Administer Aspirin 325 mg orally immediately"])
    findings_unsafe = rule.evaluate(unsafe_report, patient_record, {})
    assert len(findings_unsafe) >= 1
    assert any(f.severity == "critical" and "aspirin" in f.message.lower() for f in findings_unsafe)

    # POSITIVE: Recommending Amoxicillin (Penicillin class) must trigger critical finding
    unsafe_amox_report = make_dummy_report(["Prescribe Amoxicillin 500 mg orally every 8 hours"])
    findings_amox = rule.evaluate(unsafe_amox_report, patient_record, {})
    assert len(findings_amox) >= 1
    assert any("penicillin" in f.message.lower() or "amoxicillin" in f.message.lower() for f in findings_amox)

    # NEGATIVE: Recommending safe drug (e.g. Clopidogrel or Azithromycin) produces no allergy findings
    safe_report = make_dummy_report(["Administer Clopidogrel 300 mg loading dose"])
    findings_safe = rule.evaluate(safe_report, patient_record, {})
    assert len(findings_safe) == 0


# -----------------------------------------------------------------------------
# 3. Contraindication Rule: Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_contraindication_rule_positive_and_negative():
    """Positive: Flags drug contraindicated by active condition. Negative: Permits concordant therapy."""
    from vh.verification.rules.contraindication import ContraindicationRule

    rule = ContraindicationRule()

    patient_record = {
        "active_conditions": ["Active Peptic Ulcer Disease", "Gastrointestinal Bleeding"],
    }

    # POSITIVE: Recommending NSAID / Ketorolac with active GI bleed is contraindicated
    unsafe_report = make_dummy_report(["Administer Ketorolac 30 mg IV for severe pain"])
    findings_unsafe = rule.evaluate(unsafe_report, patient_record, {})
    assert len(findings_unsafe) >= 1
    assert any(f.severity == "critical" and "bleeding" in f.message.lower() for f in findings_unsafe)

    # NEGATIVE: Recommending Acetaminophen produces no contraindication finding
    safe_report = make_dummy_report(["Administer Acetaminophen 650 mg orally for mild pain"])
    findings_safe = rule.evaluate(safe_report, patient_record, {})
    assert len(findings_safe) == 0


# -----------------------------------------------------------------------------
# 4. Drug-Drug Interaction Rule: Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_drug_interaction_rule_positive_and_negative():
    """Positive: Flags severe DDI between recommended drug and current medications. Negative: Permits safe pairs."""
    from vh.verification.rules.interaction import DrugInteractionRule

    rule = DrugInteractionRule()

    # Patient on high-dose Simvastatin
    patient_record = {
        "current_medications": ["Simvastatin 40 mg daily", "Aspirin 81 mg daily"]
    }

    # POSITIVE: Recommending Amiodarone or Clarithromycin with Simvastatin causes severe interaction
    unsafe_report = make_dummy_report(["Initiate Amiodarone 400 mg daily for rhythm control"])
    findings_unsafe = rule.evaluate(unsafe_report, patient_record, {})
    assert len(findings_unsafe) >= 1
    assert any("simvastatin" in f.message.lower() for f in findings_unsafe)

    # NEGATIVE: Recommending Metoprolol produces no interaction findings
    safe_report = make_dummy_report(["Initiate Metoprolol Tartrate 25 mg twice daily"])
    findings_safe = rule.evaluate(safe_report, patient_record, {})
    assert len(findings_safe) == 0


# -----------------------------------------------------------------------------
# 5. Dose Range and Renal Adjustment Rule: Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_dose_range_and_renal_adjustment_rule_positive_and_negative():
    """Positive: Flags supratherapeutic dose or unadjusted dose in renal failure. Negative: Permits renal dose."""
    from vh.verification.rules.dose import DoseRangeRule

    rule = DoseRangeRule()

    # Patient with severe renal impairment (eGFR 20 mL/min)
    patient_record = {
        "egfr": 20.0,
        "creatinine": 3.4,
    }

    # POSITIVE: Enoxaparin 1 mg/kg twice daily is unsafe in eGFR < 30 (requires once-daily reduction)
    unsafe_report = make_dummy_report(["Administer Enoxaparin 80 mg subcutaneously every 12 hours"])
    findings_unsafe = rule.evaluate(unsafe_report, patient_record, {})
    assert len(findings_unsafe) >= 1
    assert any("renal" in f.message.lower() or "egfr" in f.message.lower() for f in findings_unsafe)

    # NEGATIVE: Appropriate renal adjusted dose (1 mg/kg once daily)
    safe_report = make_dummy_report(["Administer Enoxaparin 80 mg subcutaneously once daily (renally adjusted)"])
    findings_safe = rule.evaluate(safe_report, patient_record, {})
    assert len(findings_safe) == 0


# -----------------------------------------------------------------------------
# 6. Patient Data Contradiction Rule: Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_patient_data_contradiction_rule_positive_and_negative():
    """Positive: Flags hallucinated vitals/labs contradicting patient record. Negative: Concordant summary."""
    from vh.verification.rules.contradiction import PatientDataContradictionRule

    rule = PatientDataContradictionRule()

    patient_record = {
        "vitals": {"hr": 130, "bp": "85/55", "spo2": 88},
        "labs": {"potassium": 6.4, "glucose": 420},
    }

    # POSITIVE: Report claims patient has normal heart rate 72 bpm and normal potassium 4.0
    contradicting_report = make_dummy_report(
        recommendations=["Routine care"],
        patient_summary="Patient is comfortable with heart rate 72 bpm and normal potassium of 4.0 mEq/L.",
    )
    findings_contradict = rule.evaluate(contradicting_report, patient_record, {})
    assert len(findings_contradict) >= 1
    assert any(f.severity in ("critical", "major") for f in findings_contradict)

    # NEGATIVE: Report accurately reflects tachycardia and hyperkalemia
    concordant_report = make_dummy_report(
        recommendations=["Treat hyperkalemia and tachycardia"],
        patient_summary="Patient presents with severe tachycardia (HR 130 bpm) and hyperkalemia (K 6.4 mEq/L).",
    )
    findings_concordant = rule.evaluate(concordant_report, patient_record, {})
    assert len(findings_concordant) == 0


# -----------------------------------------------------------------------------
# 7. Red Flag Coverage Rule: Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_red_flag_coverage_rule_positive_and_negative():
    """Positive: Flags omission of critical red-flag addressing. Negative: Report addresses physiological red flag."""
    from vh.verification.rules.red_flags import RedFlagCoverageRule

    rule = RedFlagCoverageRule()

    # Patient has profound hypotension (SBP 80) and severe hypoxemia (SpO2 86%)
    patient_record = {
        "vitals": {"sbp": 80, "dbp": 50, "spo2": 86, "hr": 95},
    }

    # POSITIVE: Report fails to recommend oxygen or hemodynamic resuscitation
    unaddressed_report = make_dummy_report(
        recommendations=["Order routine lipid panel", "Schedule outpatient stress test"],
        differential=["Chronic Stable Angina"],
    )
    findings_unaddressed = rule.evaluate(unaddressed_report, patient_record, {})
    assert len(findings_unaddressed) >= 1
    assert any(f.severity == "critical" and ("hypoxemia" in f.message.lower() or "hypotension" in f.message.lower()) for f in findings_unaddressed)

    # NEGATIVE: Report actively addresses hypoxemia and hypotension
    addressed_report = make_dummy_report(
        recommendations=[
            "Administer supplemental oxygen immediately to target SpO2 >= 92%",
            "Initiate immediate isotonic IV fluid resuscitation for hypotension",
        ],
        differential=["Cardiogenic Shock", "Acute Respiratory Failure"],
    )
    findings_addressed = rule.evaluate(addressed_report, patient_record, {})
    assert len(findings_addressed) == 0


# -----------------------------------------------------------------------------
# 8. Determinism and Repeatability Property Test
# -----------------------------------------------------------------------------

def test_engine_determinism_property():
    """Property test: Repeated evaluations on identical inputs produce strictly identical results."""
    from vh.verification.rules.engine import DeterministicSafetyEngine

    engine = DeterministicSafetyEngine(mode="dev")

    patient_record = {
        "allergies": [{"substance": "Aspirin", "reaction": "Anaphylaxis", "severity": "severe"}],
        "active_conditions": ["Active Peptic Ulcer Disease"],
        "current_medications": ["Simvastatin 40 mg daily"],
        "vitals": {"sbp": 82, "dbp": 52, "spo2": 88, "hr": 135},
        "egfr": 22.0,
    }

    report = make_dummy_report([
        "Administer Aspirin 325 mg orally",
        "Administer Amiodarone 400 mg IV",
        "Administer Enoxaparin 80 mg subcutaneously every 12 hours",
    ])

    results = [engine.evaluate(report, patient_record) for _ in range(5)]

    # Confirm all 5 runs produce bit-for-bit identical findings and counts
    first_res = results[0]
    for res in results[1:]:
        assert res.passed == first_res.passed
        assert res.critical_count == first_res.critical_count
        assert res.major_count == first_res.major_count
        assert len(res.findings) == len(first_res.findings)
        for f1, f2 in zip(first_res.findings, res.findings):
            assert f1.rule_id == f2.rule_id
            assert f1.severity == f2.severity
            assert f1.message == f2.message
            assert f1.claim_ids == f2.claim_ids
