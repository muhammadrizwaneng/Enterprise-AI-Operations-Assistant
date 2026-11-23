"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: .../Enterprise AI Operations Assistant
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime settings for the Enterprise AI Operations Assistant."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Enterprise AI Operations Assistant"
    app_env: str = "development"
    debug: bool = True
    database_url: str = (
        "postgresql+psycopg://postgres:password@localhost:5432/enterprise_ai"
    )
    dataset_seed: int = 42

    # --- LLM / chat ---
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    llm_temperature: float = 0.7
    llm_timeout_seconds: float = 60.0
    llm_max_history_messages: int = 20
    llm_system_prompt: str = (
        "You are the Enterprise AI Operations Assistant for NovaForge. "
        "Be concise, accurate, and helpful about orders, customers, payments, "
        "and support operations. If you lack data, say so clearly."
    )

    # Ollama (local)
    ollama_base_url: str = "http://127.0.0.1:11434"

    # Future API providers (optional; never hardcode secrets)
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings (useful in tests)."""
    get_settings.cache_clear()
