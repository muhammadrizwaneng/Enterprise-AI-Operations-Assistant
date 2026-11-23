"""Unit tests for Ollama embedding client (HTTP mocked; no live server)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from experiments.embeddings.embedding_demo import (
    EmbeddingError,
    embed_texts,
    get_embedding_model,
    get_ollama_base_url,
)


def test_default_embedding_model_is_nomic(monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    assert get_embedding_model() == "nomic-embed-text"


def test_get_ollama_base_url_prefers_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://example.test:11434/")
    assert get_ollama_base_url() == "http://example.test:11434"


def test_embed_texts_success_with_mocked_http():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    vectors = embed_texts(
        ["hello world"],
        model="nomic-embed-text",
        base_url="http://127.0.0.1:11434",
        client=mock_client,
    )

    assert vectors == [[0.1, 0.2, 0.3]]
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0].endswith("/api/embeddings")
    assert kwargs["json"]["model"] == "nomic-embed-text"
    assert kwargs["json"]["prompt"] == "hello world"


def test_embed_texts_connection_error():
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")

    with pytest.raises(EmbeddingError, match="Failed to reach Ollama"):
        embed_texts(
            ["hello"],
            base_url="http://127.0.0.1:11434",
            client=mock_client,
        )


def test_embed_texts_timeout_error():
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.TimeoutException("timed out")

    with pytest.raises(EmbeddingError, match="timed out"):
        embed_texts(["hello"], client=mock_client, timeout=1.0)


def test_embed_texts_invalid_json_payload():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"not_embedding": []}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    with pytest.raises(EmbeddingError, match="missing 'embedding'"):
        embed_texts(["hello"], client=mock_client)


def test_embed_texts_http_error_status():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "internal error"

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    with pytest.raises(EmbeddingError, match="HTTP 500"):
        embed_texts(["hello"], client=mock_client)


def test_embed_texts_rejects_blank_input():
    with pytest.raises(EmbeddingError, match="non-empty"):
        embed_texts(["  "], client=MagicMock())


def test_embed_texts_owns_and_closes_client_when_not_injected():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [1.0, 0.0]}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch(
        "experiments.embeddings.embedding_demo.httpx.Client",
        return_value=mock_client,
    ):
        vectors = embed_texts(["hi"], base_url="http://127.0.0.1:11434")

    assert vectors == [[1.0, 0.0]]
    mock_client.close.assert_called_once()
