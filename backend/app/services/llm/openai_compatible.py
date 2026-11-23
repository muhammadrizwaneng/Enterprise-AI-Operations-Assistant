"""
OpenAI-compatible provider stub (extensible for future API integrations).

Not wired as the default. When OPENAI_API_KEY is set and llm_provider=openai,
the factory can construct this class. Kept separate so business logic never
depends on a specific vendor SDK.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.llm.base import ChatMessage, LLMError, LLMProvider, LLMResponse

logger = get_logger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """
    Minimal chat completions client for OpenAI-compatible HTTP APIs.

    Credentials must come from Settings / environment variables.
    """

    name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.openai_api_key:
            raise LLMError(
                "OPENAI_API_KEY is not configured",
                status_code=500,
            )
        self.base_url = self.settings.openai_base_url.rstrip("/")

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        model_name = model or self.settings.llm_model
        temp = (
            self.settings.llm_temperature if temperature is None else temperature
        )
        request_timeout = (
            self.settings.llm_timeout_seconds if timeout is None else timeout
        )

        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temp,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        logger.info("OpenAI-compatible chat model=%s messages=%s", model_name, len(messages))

        try:
            with httpx.Client(timeout=request_timeout) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMError(
                f"OpenAI-compatible API timed out after {request_timeout}s",
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMError(
                f"Failed to reach OpenAI-compatible API: {exc}",
                status_code=503,
            ) from exc

        if response.status_code >= 400:
            raise LLMError(
                f"OpenAI-compatible API HTTP {response.status_code}: {response.text[:500]}",
                status_code=502,
            )

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise LLMError("OpenAI-compatible API returned no choices", status_code=502)

        content = ((choices[0].get("message") or {}).get("content") or "").strip()
        if not content:
            raise LLMError("OpenAI-compatible API returned empty content", status_code=502)

        return LLMResponse(
            content=content,
            model=data.get("model") or model_name,
            provider=self.name,
            finish_reason=choices[0].get("finish_reason"),
            usage=data.get("usage") or {},
            raw=data,
        )

    def healthcheck(self) -> bool:
        return bool(self.settings.openai_api_key)
