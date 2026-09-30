"""
Acceptance tests for STEP 51 (P9.1): imaging models as Radiology agent tools.

Scope honesty (see STEP-51.md): no trained fracture/KOA weights or licensed
image datasets exist in this repository, and repo rules forbid fetching
patient-derived data. This step therefore ships deterministic REFERENCE tools
validated against procedural synthetic phantoms with known ground truth,
explicitly labeled as model output -- never as ground truth or clinical-grade
models. Real weight integration is recorded as future work.

Criteria (from plan/prompts/phase-9-advanced/STEP-51_P9.1_imaging-tools.md):
1. Existing baselines reproduced within tolerance (phantom baselines below).
2. Imaging claims without a tool-output citation are flagged.
3. Full regression suite of all phases passes.
"""

import numpy as np
import pytest

from vh.agents.tools.imaging import (
    FractureLocalizationTool,
    KneeOAGradingTool,
    generate_fracture_phantom,
    generate_knee_phantom,
)

FRACTURE_VERSION = "fracture-loc-ref/v1.0.0"
KOA_VERSION = "knee-oa-grade-ref/v1.0.0"


def test_fracture_baseline_within_tolerance():
    """Criterion 1: localization center error <= 4px on 64px phantoms."""
    tool = FractureLocalizationTool()
    assert tool.model_version == FRACTURE_VERSION
    errors = []
    for seed in range(10):
        phantom = generate_fracture_phantom(seed=seed, fracture=True)
        out = tool.analyze(phantom["pixels"])
        assert out.finding == "fracture_detected"
        assert out.model_version == FRACTURE_VERSION
        assert out.interpretation == "model-output"
        assert out.output_id.startswith("IMG-FX-")
        gx = (phantom["ground_truth"]["bbox"][0] + phantom["ground_truth"]["bbox"][2]) / 2
        gy = (phantom["ground_truth"]["bbox"][1] + phantom["ground_truth"]["bbox"][3]) / 2
        ox = (out.location["xmin"] + out.location["xmax"]) / 2
        oy = (out.location["ymin"] + out.location["ymax"]) / 2
        errors.append(abs(gx - ox) + abs(gy - oy))
    assert max(errors) <= 4.0
    assert sum(errors) / len(errors) <= 2.5


def test_fracture_negative_phantoms():
    """Fracture-free phantoms report no_fracture (no false positives)."""
    tool = FractureLocalizationTool()
    for seed in range(10):
        phantom = generate_fracture_phantom(seed=seed, fracture=False)
        out = tool.analyze(phantom["pixels"])
        assert out.finding == "no_fracture"
        assert out.location is None


def test_koa_grades_exact_across_severities():
    """Criterion 1: KOA grades match the phantom severity sweep exactly."""
    tool = KneeOAGradingTool()
    assert tool.model_version == KOA_VERSION
    for severity in range(5):
        for seed in (0, 1, 2):
            phantom = generate_knee_phantom(severity=severity, seed=seed)
            out = tool.analyze(phantom["pixels"])
            assert out.grade == severity, f"severity {severity} seed {seed}"
            assert out.interpretation == "model-output"
            assert out.output_id.startswith("IMG-KOA-")
            assert 0.0 <= out.confidence <= 1.0


def test_typed_output_schema():
    """Typed outputs carry finding/location/grade/confidence/version."""
    fx = FractureLocalizationTool().analyze(generate_fracture_phantom(seed=3)["pixels"])
    assert set(fx.model_dump()) >= {
        "output_id",
        "tool",
        "model_version",
        "finding",
        "location",
        "grade",
        "confidence",
        "interpretation",
    }
    koa = KneeOAGradingTool().analyze(generate_knee_phantom(severity=2, seed=3)["pixels"])
    assert koa.grade == 2
    assert koa.finding == "oa_graded"


def test_imaging_claims_without_tool_citation_flagged():
    """Criterion 2: imaging-mentioning claims lacking IMG evidence are flagged."""
    from vh.generation.report import find_uncited_imaging_claims

    report = {
        "claims": [
            {
                "claim_id": "CLM-IMG-01",
                "text": "Radiograph shows a distal radius fracture.",
                "evidence_ids": ["CHUNK-001"],
            },
            {
                "claim_id": "CLM-IMG-02",
                "text": "Knee radiograph Kellgren grade 3 osteoarthritis.",
                "evidence_ids": ["IMG-KOA-abc123"],
            },
            {
                "claim_id": "CLM-OK-01",
                "text": "Troponin rise confirms infarction.",
                "evidence_ids": ["CHUNK-001"],
            },
        ]
    }
    flagged = find_uncited_imaging_claims(report, valid_tool_ids={"IMG-KOA-abc123"})
    assert flagged == ["CLM-IMG-01"]


def test_imaging_claims_with_valid_citation_pass():
    """Cited imaging claims are not flagged."""
    from vh.generation.report import find_uncited_imaging_claims

    report = {
        "claims": [
            {
                "claim_id": "CLM-IMG-01",
                "text": "Fracture visible on x-ray.",
                "evidence_ids": ["IMG-FX-abc123"],
            }
        ]
    }
    assert find_uncited_imaging_claims(report, valid_tool_ids={"IMG-FX-abc123"}) == []


def test_radiology_agent_stub_replaced():
    """P5.2 stub is gone: the agent executes imaging tools via permissions."""
    from vh.agents.roles.radiology import RadiologyAgent
    from vh.cases.spec import AgentView, VisiblePresentation

    view = AgentView(
        case_id="CASE-IMG-001",
        specialty="Radiology",
        patient_ref="PAT-IMG-001",
        visible=VisiblePresentation(presentation="Wrist pain after fall."),
        released_results=[],
        version="1.0.0",
    )
    agent = RadiologyAgent(agent_view=view, environment=None)
    phantom = generate_fracture_phantom(seed=11, fracture=True)
    out = agent.inspect_image_pixels("FX-WRIST-01", image=phantom["pixels"], tool="fracture")
    assert out["finding"] == "fracture_detected"
    assert out["interpretation"] == "model-output"
    assert out["output_id"].startswith("IMG-")
    with pytest.raises(ValueError):
        agent.inspect_image_pixels("FX-WRIST-01", image=phantom["pixels"], tool="unknown-tool")


def test_imaging_rule_fires_in_engine():
    """P4.1 extension: the rules engine flags uncited imaging claims."""
    from vh.generation.report import ClinicalReport
    from vh.verification.rules.engine import DeterministicSafetyEngine
    from vh.verification.rules.imaging import ImagingCitationRule

    assert ImagingCitationRule().rule_id == "RULE-IMAGING-CITE-001"
    report = ClinicalReport.model_validate(
        {
            "patient_summary": "Wrist pain.",
            "findings": [],
            "differential": [
                {"dx": "Distal radius fracture", "likelihood": "high", "claim_ids": ["CLM-1"]}
            ],
            "recommendations": [],
            "claims": [
                {
                    "claim_id": "CLM-1",
                    "text": "Fracture visible on x-ray.",
                    "type": "diagnostic",
                    "evidence_ids": [],
                }
            ],
            "provenance": {
                "run_id": "r",
                "model_id": "m",
                "prompt_name_version": "p@1",
                "index_version": "i",
                "case_id": "c",
            },
        }
    )
    engine = DeterministicSafetyEngine(mode="dev")
    result = engine.evaluate(report=report, patient_record={})
    flagged = [f for f in result.findings if f.rule_id == "RULE-IMAGING-CITE-001"]
    assert len(flagged) == 1
