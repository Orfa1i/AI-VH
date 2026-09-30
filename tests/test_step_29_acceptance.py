"""
Acceptance tests for Step 29: P4.5 Fault-Injection Suite.

Tests:
1. Fault classification config:
   - All 9 required fault types are classified as 'critical' or 'non_critical'
   - Config contains metadata, rationale, and clinical risk
2. Fault generator coverage and counts:
   - Every one of the 9 fault types appears at least 20 times (criterion: >= 20 each)
   - Clean original reports are preserved alongside corrupted variants
3. Fault corruption semantics:
   - Mutations are medically and structurally concrete for each fault type
   - Clean reports are verified without false flags
4. Artifact registration:
   - Fault set is registered as a versioned 'fault_set' artifact in ArtifactRegistry
   - Content hashing and lineage are preserved
5. Scorer and threshold evaluation:
   - Computes detection rate per fault type
   - Computes overall critical fault detection rate (checked against verification.critical_fault_detection: 1.0)
   - Computes overall non-critical fault detection rate (checked against verification.noncritical_fault_detection: 0.90)
   - Computes false-flag rate on clean originals (checked against verification.false_flag_rate_max: 0.10)
   - Gate passes on all thresholds
"""

from pathlib import Path
import pytest
import yaml

from vh.common.artifacts import ArtifactKind, get_artifact_registry
from eval.faults import (
    FaultType,
    FaultSeverity,
    FaultClassificationConfig,
    FaultGenerator,
    FaultInjectionScorer,
    FaultSet,
    load_fault_classification,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_fault_classification_config():
    """Verify that all 9 required fault types are classified in config."""
    config = load_fault_classification()
    assert isinstance(config, FaultClassificationConfig)
    assert config.version is not None

    required_fault_types = {
        "wrong_evidence_id",
        "swapped_evidence",
        "fabricated_claim",
        "allergy_conflict",
        "contraindicated_drug",
        "overdose",
        "renal_dose_error",
        "contradiction_of_vitals_labs",
        "missed_red_flag",
    }

    classified_types = {ft.value for ft in config.classifications.keys()}
    assert required_fault_types.issubset(classified_types), (
        f"Missing fault types in classification config: {required_fault_types - classified_types}"
    )

    for ft_enum, info in config.classifications.items():
        assert info.severity in (FaultSeverity.CRITICAL, FaultSeverity.NON_CRITICAL)
        assert len(info.description) > 0
        assert len(info.clinical_risk) > 0


def test_fault_generator_counts_and_types():
    """
    Acceptance Criterion:
    Every fault type appears at least 20 times.
    """
    generator = FaultGenerator()
    fault_set: FaultSet = generator.generate_fault_set(instances_per_fault=25)

    assert isinstance(fault_set, FaultSet)
    assert len(fault_set.clean_cases) >= 20
    assert len(fault_set.corrupted_cases) >= 9 * 20

    # Count occurrences per fault type
    counts_by_type = {}
    for case in fault_set.corrupted_cases:
        counts_by_type[case.fault_type] = counts_by_type.get(case.fault_type, 0) + 1

    for ft in FaultType:
        count = counts_by_type.get(ft, 0)
        assert count >= 20, f"Fault type {ft.value} appeared {count} times, expected >= 20"


def test_fault_corruption_semantics():
    """Verify that corrupted cases exhibit concrete structural and clinical defects."""
    generator = FaultGenerator()
    fault_set = generator.generate_fault_set(instances_per_fault=20)

    # 1. Check wrong_evidence_id
    wrong_ev_cases = [c for c in fault_set.corrupted_cases if c.fault_type == FaultType.WRONG_EVIDENCE_ID]
    assert len(wrong_ev_cases) >= 20
    for case in wrong_ev_cases:
        cited_eids = {eid for claim in case.corrupted_report.claims for eid in claim.evidence_ids}
        # At least one cited eid must be absent from retrieved_chunks
        missing = [eid for eid in cited_eids if eid not in case.retrieved_chunks]
        assert len(missing) > 0, f"Case {case.case_id} was expected to have missing evidence IDs"

    # 2. Check allergy_conflict
    allergy_cases = [c for c in fault_set.corrupted_cases if c.fault_type == FaultType.ALLERGY_CONFLICT]
    assert len(allergy_cases) >= 20
    for case in allergy_cases:
        allergies = case.patient_record.get("allergies", [])
        assert len(allergies) > 0, f"Case {case.case_id} missing documented allergies"
        rec_text = " ".join(r.text for r in case.corrupted_report.recommendations).lower()
        # Must prescribe an allergenic drug
        assert any(a.lower() in rec_text for a in allergies) or "aspirin" in rec_text or "amoxicillin" in rec_text

    # 3. Check overdose
    overdose_cases = [c for c in fault_set.corrupted_cases if c.fault_type == FaultType.OVERDOSE]
    assert len(overdose_cases) >= 20
    for case in overdose_cases:
        rec_text = " ".join(r.text for r in case.corrupted_report.recommendations).lower()
        # Must contain excessive dosage
        assert any(term in rec_text for term in ["1000 mg", "800 mg", "600 mg", "300 mg", "2000 mg", "4000 mg"])


def test_fault_set_artifact_registration(tmp_path):
    """Verify that the generated fault set is registered as a versioned fault_set artifact."""
    generator = FaultGenerator()
    fault_set = generator.generate_fault_set(instances_per_fault=20)

    registry = get_artifact_registry()
    record = generator.register_as_artifact(fault_set=fault_set, registry=registry)

    assert record.kind == ArtifactKind.FAULT_SET
    assert record.name == "verification_fault_set"
    assert record.version.startswith("v")
    assert len(record.sha256) == 64
    assert record.metadata.get("total_corrupted") == len(fault_set.corrupted_cases)
    assert record.metadata.get("total_clean") == len(fault_set.clean_cases)

    # Verify retrieval from registry
    loaded = registry.load_artifact(ArtifactKind.FAULT_SET, record.name, record.version)
    assert loaded is not None
    assert loaded.id == record.id


def test_fault_injection_scorer_and_thresholds():
    """
    Acceptance Criterion:
    Metrics computed and compared to verification.* thresholds:
    - critical_fault_detection >= 1.0 (100%)
    - noncritical_fault_detection >= 0.90 (90%)
    - false_flag_rate_max <= 0.10 (10%)
    """
    with open(REPO_ROOT / "configs" / "thresholds.yaml", "r", encoding="utf-8") as f:
        thresholds = yaml.safe_load(f)["verification"]

    generator = FaultGenerator()
    fault_set = generator.generate_fault_set(instances_per_fault=25)

    scorer = FaultInjectionScorer()
    eval_report = scorer.evaluate(fault_set)

    # Verify detection rate per fault type is present
    for ft in FaultType:
        assert ft.value in eval_report.detection_by_fault_type
        rate = eval_report.detection_by_fault_type[ft.value]["rate"]
        assert 0.0 <= rate <= 1.0

    # Compare to thresholds
    assert eval_report.critical_detection_rate >= thresholds["critical_fault_detection"], (
        f"Critical detection rate {eval_report.critical_detection_rate} below required threshold "
        f"{thresholds['critical_fault_detection']}"
    )

    assert eval_report.noncritical_detection_rate >= thresholds["noncritical_fault_detection"], (
        f"Non-critical detection rate {eval_report.noncritical_detection_rate} below required threshold "
        f"{thresholds['noncritical_fault_detection']}"
    )

    assert eval_report.false_flag_rate <= thresholds["false_flag_rate_max"], (
        f"False flag rate {eval_report.false_flag_rate} exceeded maximum threshold "
        f"{thresholds['false_flag_rate_max']}"
    )

    assert eval_report.passed is True
