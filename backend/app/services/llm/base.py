"""Provider-agnostic LLM interfaces and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant"]


@dataclass(slots=True)
class ChatMessage:
    """One turn in a chat conversation."""

    role: Role
    content: str


@dataclass(slots=True)
class LLMResponse:
    """Normalized completion returned by any provider."""

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class LLMError(Exception):
    """Base error for LLM provider failures."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMProvider(ABC):
    """
    Abstract LLM provider.

    Business logic talks only to this interface so providers can be swapped
    (Ollama today, OpenAI/Anthropic later) without changing chat services.
    """

    name: str

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        """Generate an assistant reply for the given message list."""

    @abstractmethod
    def healthcheck(self) -> bool:
        """Return True if the provider is reachable."""
