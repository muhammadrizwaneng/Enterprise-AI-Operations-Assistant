"""Ollama local LLM provider."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.llm.base import ChatMessage, LLMError, LLMProvider, LLMResponse

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """Talks to a local Ollama server over HTTP (`/api/chat`)."""

    name = "ollama"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")

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
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temp},
        }

        url = f"{self.base_url}/api/chat"
        logger.info(
            "Ollama chat request model=%s messages=%s timeout=%s",
            model_name,
            len(messages),
            request_timeout,
        )

        try:
            with httpx.Client(timeout=request_timeout) as client:
                response = client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out after %ss", request_timeout)
            raise LLMError(
                f"Ollama timed out after {request_timeout}s",
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Ollama connection error: %s", exc)
            raise LLMError(
                f"Failed to reach Ollama at {self.base_url}: {exc}",
                status_code=503,
            ) from exc

        if response.status_code >= 400:
            detail = response.text[:500]
            logger.error("Ollama error status=%s body=%s", response.status_code, detail)
            raise LLMError(
                f"Ollama returned HTTP {response.status_code}: {detail}",
                status_code=502,
            )

        data = response.json()
        message = data.get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            raise LLMError("Ollama returned an empty response", status_code=502)

        usage = {
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
        }
        return LLMResponse(
            content=content,
            model=data.get("model") or model_name,
            provider=self.name,
            finish_reason=data.get("done_reason"),
            usage={k: v for k, v in usage.items() if v is not None},
            raw=data,
        )

    def healthcheck(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
