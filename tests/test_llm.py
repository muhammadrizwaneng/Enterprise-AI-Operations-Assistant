"""Unit tests for LLM provider abstraction (no live model required)."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.llm.base import ChatMessage, LLMError, LLMResponse
from app.services.llm.factory import build_llm_provider
from app.services.llm.ollama import OllamaProvider


def test_build_ollama_provider():
    settings = Settings(
        llm_provider="ollama",
        llm_model="llama3.2",
        ollama_base_url="http://127.0.0.1:11434",
    )
    provider = build_llm_provider(settings)
    assert provider.name == "ollama"
    assert isinstance(provider, OllamaProvider)


def test_unsupported_provider_raises():
    settings = Settings(llm_provider="not-a-real-provider")
    with pytest.raises(LLMError) as exc:
        build_llm_provider(settings)
    assert exc.value.status_code == 500


def test_openai_provider_requires_api_key():
    settings = Settings(llm_provider="openai", openai_api_key=None)
    with pytest.raises(LLMError):
        build_llm_provider(settings)


def test_ollama_chat_success(httpx_mock=None):
    """Mock Ollama HTTP response via monkeypatch of httpx.Client."""
    from unittest.mock import MagicMock, patch

    settings = Settings(
        llm_provider="ollama",
        llm_model="llama3.2",
        ollama_base_url="http://127.0.0.1:11434",
        llm_timeout_seconds=5,
    )
    provider = OllamaProvider(settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "llama3.2",
        "message": {"role": "assistant", "content": "Hello from mock Ollama"},
        "done_reason": "stop",
        "prompt_eval_count": 10,
        "eval_count": 5,
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.post.return_value = mock_response

    with patch("app.services.llm.ollama.httpx.Client", return_value=mock_client):
        result = provider.chat(
            [ChatMessage(role="user", content="Hi")],
            temperature=0.2,
        )

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from mock Ollama"
    assert result.provider == "ollama"
    assert result.model == "llama3.2"
    mock_client.post.assert_called_once()


def test_ollama_timeout_maps_to_llm_error():
    from unittest.mock import MagicMock, patch

    import httpx

    settings = Settings(ollama_base_url="http://127.0.0.1:11434", llm_timeout_seconds=1)
    provider = OllamaProvider(settings)

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.post.side_effect = httpx.TimeoutException("timed out")

    with patch("app.services.llm.ollama.httpx.Client", return_value=mock_client):
        with pytest.raises(LLMError) as exc:
            provider.chat([ChatMessage(role="user", content="Hi")])
    assert exc.value.status_code == 504
