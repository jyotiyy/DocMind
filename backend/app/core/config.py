"""
Centralized application configuration.

All tunable parameters for DocMind are defined here and can be overridden
via environment variables or a `.env` file. Using a single Settings object
avoids scattering `os.environ` calls throughout the codebase.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    APP_NAME: str = "DocMind"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
        ]
    )

    # --- Storage paths ---
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    INDEX_DIR: Path = BASE_DIR / "indexes"
    FAISS_INDEX_PATH: Path = BASE_DIR / "indexes" / "faiss.index"
    METADATA_STORE_PATH: Path = BASE_DIR / "indexes" / "metadata.json"
    DOCUMENT_REGISTRY_PATH: Path = BASE_DIR / "indexes" / "documents.json"

    # --- OCR ---
    OCR_DPI: int = Field(default=300)
    OCR_LANGUAGE: str = Field(default="eng")
    MIN_TEXT_CHARS_PER_PAGE: int = Field(
        default=20,
        description="Below this char count a page is treated as scanned/image-only.",
    )

    # --- Chunking ---
    CHUNK_SIZE: int = Field(default=800)
    CHUNK_OVERLAP: int = Field(default=120)

    # --- Embeddings ---
    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_DIMENSION: int = Field(default=384)
    EMBEDDING_BATCH_SIZE: int = Field(default=32)

    # --- Reranking ---
    RERANKER_MODEL_NAME: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2"
    )
    RETRIEVAL_TOP_K: int = Field(default=10)
    RERANK_TOP_K: int = Field(default=5)

    # --- LLM / Ollama ---
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b")
    OLLAMA_TIMEOUT_SECONDS: int = Field(default=120)
    OLLAMA_TEMPERATURE: float = Field(default=0.1)

    # --- Confidence thresholds ---
    CONFIDENCE_HIGH_THRESHOLD: float = Field(default=0.75)
    CONFIDENCE_MEDIUM_THRESHOLD: float = Field(default=0.45)

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = Field(default=50)
    ALLOWED_EXTENSIONS: set[str] = Field(default_factory=lambda: {".pdf"})

    # --- Logging ---
    LOG_LEVEL: str = Field(default="INFO")
    LOG_DIR: Path = BASE_DIR / "logs"

    def ensure_directories(self) -> None:
        """Create all directories required by the application at startup."""
        for directory in (
            self.DATA_DIR,
            self.UPLOAD_DIR,
            self.INDEX_DIR,
            self.LOG_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
