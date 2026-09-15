"""
Live GPU Inference Regression Test
Verifies MedGemmaService actually loads the model + DPO LoRA adapter and executes
real generation through generate_comparative_inference(), instead of silently
falling through to the per-case canned fallback text. Skipped on machines without
CUDA (e.g. CI) since it requires the real quantized model + adapter on disk.
"""

import pytest
import torch

from backend.llm.medgemma_service import MedGemmaService

pytestmark = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="Live GPU inference test requires a CUDA device.",
)


@pytest.fixture(scope="module")
def loaded_service():
    service = MedGemmaService()
    service.load_model()
    return service


def test_medgemma_model_and_adapter_load(loaded_service):
    assert loaded_service.model is not None, "Base model failed to load onto GPU"
    assert loaded_service._is_adapter_loaded and loaded_service.adapter_model is not None, (
        "DPO LoRA adapter failed to load"
    )


def test_live_gpu_comparative_inference_produces_real_generated_text(loaded_service):
    result = loaded_service.generate_comparative_inference(case_id="CASE-101")

    assert result["telemetry"]["cuda_available"] is True
    assert result["telemetry"]["model_loaded"] is True
    assert result["telemetry"]["live_gpu_inference_used"] is True, (
        "Inference fell back to canned per-case text instead of running the real model"
    )

    base_dx = result["base_model_output"]["primary_diagnosis"]
    dpo_dx = result["dpo_model_output"]["primary_diagnosis"]
    base_reasoning = result["base_model_output"]["clinical_reasoning"]
    dpo_reasoning = result["dpo_model_output"]["clinical_reasoning"]

    # Real generation should not be empty/trivial or byte-identical between the
    # base and adapter-active passes (see medgemma_service.py: PeftModel mutates
    # the shared model in-place, so identical output here would mean the earlier
    # disable_adapter() fix regressed).
    assert len(base_dx) > 3 and len(dpo_dx) > 3
    assert len(base_reasoning) > 20 and len(dpo_reasoning) > 20
    assert base_reasoning != dpo_reasoning
