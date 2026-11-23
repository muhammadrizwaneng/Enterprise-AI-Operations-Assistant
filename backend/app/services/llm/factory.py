"""Factory / registry for LLM providers."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.llm.base import LLMError, LLMProvider
from app.services.llm.ollama import OllamaProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider

logger = get_logger(__name__)


def build_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Construct the configured provider instance."""
    cfg = settings or get_settings()
    provider_name = (cfg.llm_provider or "ollama").strip().lower()
    logger.info("Building LLM provider=%s model=%s", provider_name, cfg.llm_model)

    if provider_name == "ollama":
        return OllamaProvider(cfg)
    if provider_name in {"openai", "openai_compatible"}:
        return OpenAICompatibleProvider(cfg)

    raise LLMError(
        f"Unsupported LLM provider '{provider_name}'. "
        "Supported: ollama, openai",
        status_code=500,
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Cached default provider from environment settings."""
    return build_llm_provider()


def clear_llm_provider_cache() -> None:
    """Clear cached provider (tests / settings reload)."""
    get_llm_provider.cache_clear()
