"""
Fish Audio / Flash Audio TTS Service for AI-VH Specialists.
Provides speech synthesis proxy for specialist reasoning updates with automatic fallback
to client-side speech synthesis when API credits are exhausted or offline.
"""

import os
import io
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Response, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger("TTS_Service")
router = APIRouter(prefix="/tts", tags=["TTS"])

DEFAULT_FISH_KEY = "sk-fish-lOjCwIaCf9ML-StgZx64iGYz-QAWbncWGa8_HUyTYis"

class TTSRequest(BaseModel):
    text: str = Field(..., description="Brief clinical text to speak")
    specialist: Optional[str] = Field("router", description="Specialist ID or name")
    voice_id: Optional[str] = Field(None, description="Optional Fish Audio voice model ID")
    format: Optional[str] = Field("mp3", description="Audio format")


# Voice mappings for specialists (can use specific voice IDs if configured)
SPECIALIST_VOICES: Dict[str, Dict[str, Any]] = {
    "router": {"pitch": 1.0, "rate": 1.05, "desc": "MedGemma System"},
    "id": {"pitch": 0.95, "rate": 1.0, "desc": "Dr. Anthony Mercer (Infectious Diseases)"},
    "infectious_diseases": {"pitch": 0.95, "rate": 1.0, "desc": "Dr. Anthony Mercer (Infectious Diseases)"},
    "gy": {"pitch": 1.15, "rate": 1.02, "desc": "Dr. Evelyn Reed (Gynecology)"},
    "gynecology": {"pitch": 1.15, "rate": 1.02, "desc": "Dr. Evelyn Reed (Gynecology)"},
    "ne": {"pitch": 0.9, "rate": 0.98, "desc": "Dr. Alexander Hayes (Neurology)"},
    "neurology": {"pitch": 0.9, "rate": 0.98, "desc": "Dr. Alexander Hayes (Neurology)"},
    "ca": {"pitch": 1.0, "rate": 1.05, "desc": "Dr. Rachel Vance (Cardiology)"},
    "cardiology": {"pitch": 1.0, "rate": 1.05, "desc": "Dr. Rachel Vance (Cardiology)"},
    "im": {"pitch": 0.98, "rate": 1.0, "desc": "Dr. Marcus Vance (Internal Medicine)"},
    "internal_medicine": {"pitch": 0.98, "rate": 1.0, "desc": "Dr. Marcus Vance (Internal Medicine)"},
    "em": {"pitch": 1.05, "rate": 1.1, "desc": "Dr. David Kim (Emergency Medicine)"},
    "emergency": {"pitch": 1.05, "rate": 1.1, "desc": "Dr. David Kim (Emergency Medicine)"},
    "su": {"pitch": 0.92, "rate": 1.0, "desc": "Dr. Sarah Lin (Surgery)"},
    "surgery": {"pitch": 0.92, "rate": 1.0, "desc": "Dr. Sarah Lin (Surgery)"},
}


@router.get("/status")
async def tts_status():
    """Returns TTS configuration status and availability."""
    api_key = os.getenv("FISH_AUDIO_API_KEY", DEFAULT_FISH_KEY)
    masked_key = api_key[:8] + "..." + api_key[-4:] if api_key and len(api_key) > 12 else "not_configured"
    return {
        "service": "Fish Audio (Flash Audio)",
        "endpoint": "https://api.fish.audio/v1/tts",
        "api_key_configured": bool(api_key),
        "api_key_masked": masked_key,
        "fallback_available": True,
        "fallback_engine": "Web Speech API (SpeechSynthesis)",
        "specialists_configured": list(SPECIALIST_VOICES.keys())
    }


@router.post("/speak")
async def generate_speech(req: TTSRequest):
    """
    Synthesize speech for a specialist update.
    Streams MP3 if Fish Audio succeeds; otherwise returns fallback instructions.
    """
    api_key = os.getenv("FISH_AUDIO_API_KEY", DEFAULT_FISH_KEY)
    
    # Strip text to ensure concise updates
    clean_text = req.text.strip()
    if not clean_text:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Text cannot be empty"}
        )

    # Truncate to maximum 250 characters to strictly maintain efficiency & cost
    if len(clean_text) > 250:
        clean_text = clean_text[:247] + "..."

    # Attempt Fish Audio API call
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload: Dict[str, Any] = {
                    "text": clean_text,
                    "format": req.format or "mp3"
                }
                if req.voice_id:
                    payload["reference_id"] = req.voice_id

                resp = await client.post("https://api.fish.audio/v1/tts", json=payload, headers=headers)
                
                if resp.status_code == 200 and resp.content:
                    return StreamingResponse(
                        io.BytesIO(resp.content),
                        media_type="audio/mpeg",
                        headers={"Content-Disposition": "inline; filename=speech.mp3"}
                    )
                else:
                    logger.warning(
                        f"Fish Audio API returned status {resp.status_code}: {resp.text[:200]}. "
                        "Falling back to client synthesis."
                    )
        except Exception as err:
            logger.warning(f"Fish Audio request failed: {err}. Falling back to client synthesis.")

    # Fallback response for browser synthesis
    voice_pref = SPECIALIST_VOICES.get(req.specialist.lower(), {"pitch": 1.0, "rate": 1.0})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "fallback": True,
            "text": clean_text,
            "specialist": req.specialist,
            "pitch": voice_pref.get("pitch", 1.0),
            "rate": voice_pref.get("rate", 1.0),
            "engine": "browser_speech_synthesis"
        }
    )
