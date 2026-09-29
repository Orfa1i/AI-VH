"""
FastAPI REST router for MedGemma clinical generation API.
Provides POST /api/generation/generate endpoint for schema-constrained generation.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from vh.generation.report import ClinicalReport
from vh.generation.medgemma import (
    MedGemmaAdapter,
    MedGemmaConfig,
    GenerationFailed,
    GenerationTimeoutError,
    MissingPromptVersionError,
)

router = APIRouter(prefix="/api/generation", tags=["Generation"])


class GenerationRequest(BaseModel):
    """Payload for clinical report generation."""
    prompt_name_version: str = Field(..., description="Prompt template version in name@version format")
    inputs: Dict[str, Any] = Field(..., description="Generation inputs including patient summary and evidence")
    model_id: Optional[str] = None
    temperature: Optional[float] = None
    max_retries: Optional[int] = None
    timeout_s: Optional[float] = None


@router.post("/generate", response_model=ClinicalReport)
async def generate_clinical_report(req: GenerationRequest, request: Request):
    """
    Generate evidence-grounded clinical report using MedGemma.
    Enforces constrained schema decoding, referential integrity, and retry error feedback.
    """
    adapter: Optional[MedGemmaAdapter] = getattr(request.app.state, "medgemma_adapter", None)
    if not adapter:
        config = MedGemmaConfig()
        if req.model_id:
            config.model_id = req.model_id
        if req.temperature is not None:
            config.temperature = req.temperature
        if req.max_retries is not None:
            config.max_retries = req.max_retries
        if req.timeout_s is not None:
            config.timeout_s = req.timeout_s
        adapter = MedGemmaAdapter(config=config)
        request.app.state.medgemma_adapter = adapter

    try:
        report = adapter.generate(
            prompt_name_version=req.prompt_name_version,
            inputs=req.inputs,
            response_schema=ClinicalReport,
        )
        return report
    except MissingPromptVersionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GenerationTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except GenerationFailed as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed unexpectedly: {str(e)}")
