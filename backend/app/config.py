"""
AI-Powered Banking Incident Resolution & Root Cause Analysis Agent
==================================================================
Configuration module using Pydantic Settings for environment-variable-driven config.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parent.parent / ".env").as_posix(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "AI Banking Incident Resolution Agent"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:4200"]  # Angular dev server

    # ── Database ─────────────────────────────────────────────────
    database_url: str = f"sqlite+aiosqlite:///{(Path(__file__).resolve().parent.parent / 'bank_app.db').as_posix()}"
    echo_sql: bool = False

    # ── JWT / Security ───────────────────────────────────────────
    jwt_secret_key: str = "dev-secret-change-in-production-32-chars-min"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── Ollama (LLM) ────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout: int = 120

    # ── Qdrant (Vector DB) ───────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_in_memory: bool = True  # Use in-memory for dev
    qdrant_collection_name: str = "banking_knowledge"
    qdrant_embedding_dim: int = 768  # nomic-embed-text dimension

    # ── External Banking Sandbox (Plaid) ─────────────────────────
    plaid_client_id: str | None = None
    plaid_secret: str | None = None
    plaid_env: str = "sandbox"

    # ── Redis (Cache) ────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    use_redis: bool = False  # In-memory cache by default

    # ── Kafka (Events) ──────────────────────────────────────────
    kafka_bootstrap_servers: str = "localhost:9092"
    use_kafka: bool = False  # In-memory event bus by default

    # ── Paths ────────────────────────────────────────────────────
    base_dir: Path = Path(__file__).resolve().parent.parent
    knowledge_base_dir: Path = Path(__file__).resolve().parent.parent / "knowledge_base"
    ml_models_dir: Path = Path(__file__).resolve().parent.parent / "ml_models"
    logs_dir: Path = Path(__file__).resolve().parent.parent / "logs"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
