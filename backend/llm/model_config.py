"""
Model Configuration & Provenance Source of Truth.
Provides the unified model ID and parameters for MedGemma 4B on local GPU.
"""

import os

DEFAULT_MODEL_ID = "google/medgemma-4b"


def get_model_id() -> str:
    """Returns the resolved model ID (defaults to local MedGemma 4B)."""
    return os.environ.get("VH_MODEL_ID", DEFAULT_MODEL_ID)
