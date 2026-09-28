"""
Acceptance criteria tests for STEP 11 (P1.5):
Case Builder with leakage guard, narrative-number consistency, determinism, and LLM mode.
"""

from pathlib import Path
from typing import List
import pytest

from vh.cases.builder import (
    CaseBuilder,
    CaseBuilderConfig,
    LeakageGuard,
    NumberConsistencyChecker,
    SpecialtyCohortSpec,
)
from vh.cases.spec import CaseSpec


def test_leakage_guard_detects_forbidden_terms():
    """Verify that LeakageGuard correctly detects forbidden diagnosis terms and abbreviations."""
    guard = LeakageGuard.load_default()
    
    # Test positive detections (should flag leakage)
    assert guard.has_leakage("Patient has acute coronary syndrome with chest pain.", "acute_coronary_syndrome")
    assert guard.has_leakage("ECG shows STEMI.", "acute_coronary_syndrome")
    assert guard.has_leakage("Presentation consistent with DKA crisis.", "diabetic_ketoacidosis")
    assert guard.has_leakage("Elderly patient admitted with severe pneumonia.", "community_acquired_pneumonia")
    assert guard.has_leakage("Clinical picture suggestive of CAP.", "community_acquired_pneumonia")

    # Test negative detections (should NOT flag leakage: purely clinical signs and symptoms)
    assert not guard.has_leakage("Patient presents with substernal pressure and diaphoresis.", "acute_coronary_syndrome")
    assert not guard.has_leakage("Patient reports productive cough, fever, and dyspnea.", "community_acquired_pneumonia")
    assert not guard.has_leakage("Patient presents with nausea, vomiting, abdominal pain, and polyuria.", "diabetic_ketoacidosis")


def test_narrative_number_consistency_checker():
    """Verify that NumberConsistencyChecker validates that all narrative numbers exist in structured record."""
    checker = NumberConsistencyChecker()

    valid_narrative = (
        "A 64-year-old male presents with acute chest discomfort. "
        "Triage vitals: blood pressure 142/88 mmHg, heart rate 92 bpm, "
        "respiratory rate 18 breaths/min, and oxygen saturation 96% on room air."
    )
    structured_vitals = {"bp": "142/88", "hr": 92, "rr": 18, "spo2": 96, "temp": 37.0}
    structured_demographics = {"age": 64, "gender": "male"}

    is_valid, inconsistencies = checker.check_consistency(
        narrative=valid_narrative,
        vitals=structured_vitals,
        demographics=structured_demographics,
    )
    assert is_valid, f"Expected valid consistency, got inconsistencies: {inconsistencies}"
    assert len(inconsistencies) == 0

    # Hallucinated number test: 180 is not in the vitals or demographics
    invalid_narrative = (
        "A 64-year-old male presents with acute chest discomfort. "
        "Heart rate is 180 bpm and oxygen saturation is 96%."
    )
    is_valid_inv, inconsistencies_inv = checker.check_consistency(
        narrative=invalid_narrative,
        vitals=structured_vitals,
        demographics=structured_demographics,
    )
    assert not is_valid_inv
    assert "180" in inconsistencies_inv


def test_zero_leakage_terms_across_500_case_batch():
    """Acceptance criterion 1: Zero leakage terms across a 500-case batch."""
    config = CaseBuilderConfig(batch_size=500, seed=1337)
    builder = CaseBuilder(config=config)

    batch: List[CaseSpec] = builder.build_batch(count=500, seed=1337)
    assert len(batch) == 500

    guard = LeakageGuard.load_default()
    leakage_failures = []

    for idx, case in enumerate(batch):
        specialty_slug = case.metadata.get("specialty_slug", "")
        visible_text = f"{case.visible.presentation} {case.visible.history} {case.visible.exam or ''}"
        
        if guard.has_leakage(visible_text, specialty_slug):
            leakage_failures.append((case.case_id, specialty_slug, visible_text))

    assert len(leakage_failures) == 0, f"Found {len(leakage_failures)} cases with term leakage: {leakage_failures[:3]}"


def test_100_percent_narrative_number_consistency_across_500_cases():
    """Acceptance criterion 2: 100% narrative-number consistency across batch."""
    config = CaseBuilderConfig(batch_size=500, seed=1337)
    builder = CaseBuilder(config=config)

    batch: List[CaseSpec] = builder.build_batch(count=500, seed=1337)
    assert len(batch) == 500

    checker = NumberConsistencyChecker()
    inconsistent_cases = []

    for case in batch:
        is_valid, inconsistencies = checker.check_case(case)
        if not is_valid:
            inconsistent_cases.append((case.case_id, inconsistencies, case.visible.presentation))

    assert len(inconsistent_cases) == 0, f"Inconsistent cases detected: {inconsistent_cases[:3]}"


def test_determinism_same_seed_gives_identical_cases():
    """Acceptance criterion 3: Same seed gives identical cases byte-for-byte."""
    config = CaseBuilderConfig(batch_size=10, seed=999)
    builder1 = CaseBuilder(config=config)
    builder2 = CaseBuilder(config=config)

    batch1 = builder1.build_batch(count=10, seed=999)
    batch2 = builder2.build_batch(count=10, seed=999)

    assert len(batch1) == len(batch2) == 10

    for c1, c2 in zip(batch1, batch2):
        assert c1.model_dump() == c2.model_dump(), f"Mismatch between seeds for {c1.case_id}!"

    # Lineage must be recorded in case metadata
    first_case = batch1[0]
    lineage = first_case.metadata.get("lineage")
    assert lineage is not None
    assert lineage.get("builder_seed") == 999
    assert lineage.get("synthea_dataset_id") is not None


def test_llm_narrative_mode_passes_same_tests():
    """Acceptance criterion 4: The LLM-narrative mode passes the same tests (integration marker)."""
    # Test LLM mode configuration with validated simulation wrapper
    config = CaseBuilderConfig(use_llm_narrative=True, seed=42)
    builder = CaseBuilder(config=config)

    case = builder.build_single_case(
        specialty_slug="acute_coronary_syndrome",
        seed=42,
    )

    guard = LeakageGuard.load_default()
    checker = NumberConsistencyChecker()

    # Check zero leakage
    visible_text = f"{case.visible.presentation} {case.visible.history} {case.visible.exam or ''}"
    assert not guard.has_leakage(visible_text, "acute_coronary_syndrome")

    # Check 100% number consistency
    is_valid, inconsistencies = checker.check_case(case)
    assert is_valid, f"LLM narrative has inconsistencies: {inconsistencies}"
    assert case.metadata.get("lineage", {}).get("generator_mode") == "llm"
