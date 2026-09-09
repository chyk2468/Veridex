"""
Configuration module for Fact Knowledge Layer.
Loads settings from environment variables with strong typing and default fallbacks.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Ensure .env is loaded if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Groq Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ENABLE_OFFLINE_MOCK: bool = os.getenv("ENABLE_OFFLINE_MOCK", "false").lower() in ("true", "1", "yes")

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = 384

    # Storage
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'facts.db'}")
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", str(BASE_DIR / "data" / "facts.faiss"))

    # Matching & Comparison
    VALUE_TOLERANCE_PERCENT: float = 1.0  # Allow 1.0% tolerance for rounding in corroboration
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.65
    CONFIDENCE_THRESHOLD: float = 0.70

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

