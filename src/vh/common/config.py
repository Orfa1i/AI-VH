"""
Core configuration settings for AI Virtual Hospital (AI-VH).
Uses pydantic-settings to manage environment variables with strong typing and default fallbacks.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings backed by environment variables and .env file."""

    # Server & Environment
    APP_ENV: str = Field(default="development", description="Application environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Enable debug mode and verbose traceback logging")
    HOST: str = Field(default="127.0.0.1", description="FastAPI host address")
    PORT: int = Field(default=8000, description="FastAPI port")
    SECRET_KEY: str = Field(
        default="insecure-dev-secret-key-change-in-production",
        description="Application secret key for signing session tokens and internal APIs"
    )

    # Database Configuration (SQLite default for development, PostgreSQL for production)
    DATABASE_URL: str = Field(
        default="sqlite:///./hospital.db",
        description="Primary database connection string"
    )
    POSTGRES_USER: str = Field(default="ai_vh", description="PostgreSQL database user")
    POSTGRES_PASSWORD: str = Field(default="ai_vh_secret", description="PostgreSQL database password")
    POSTGRES_DB: str = Field(default="ai_vh", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")

    # Local AI & Medical Knowledge Model Paths
    MEDGEMMA_MODEL_PATH: str = Field(
        default="./MedGemma Model/model",
        description="Filesystem path to local MedGemma quantized weights"
    )
    DPO_ADAPTER_PATH: str = Field(
        default="./models/medgemma-dpo-lora",
        description="Filesystem path to trained DPO LoRA adapter"
    )
    HARRISON_VECTOR_DB_PATH: str = Field(
        default="./data/knowledge/harrison_chroma",
        description="Filesystem path to ChromaDB vector store containing Harrison's Internal Medicine"
    )

    # Governance & Evaluation Thresholds
    THRESHOLDS_PATH: str = Field(
        default="./configs/thresholds.yaml",
        description="Path to thresholds.yaml defining quality and safety gate thresholds"
    )

    # CORS and Frontend Networking
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        description="Allowed CORS origin URLs for clinical web portal"
    )

    # Logging & Observability
    LOG_LEVEL: str = Field(default="INFO", description="Standard logging level (DEBUG, INFO, WARNING, ERROR)")

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton instance of application settings."""
    return Settings()
