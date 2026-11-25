"""Unit tests for EmbeddingClient (mocked Ollama; no live server / no DB)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.services.embedding_client import EmbeddingClient, EmbeddingClientError


def _settings(**overrides) -> Settings:
    base = dict(
        ollama_base_url="http://127.0.0.1:11434",
        embedding_model="nomic-embed-text",
        embedding_dimensions=768,
        embedding_timeout_seconds=30.0,
    )
    base.update(overrides)
    return Settings(**base)


def _vector(dim: int = 768, fill: float = 0.1) -> list[float]:
    return [fill] * dim


def test_embed_texts_success_validates_768_dimensions():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": _vector()}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    client = EmbeddingClient(settings=_settings(), client=mock_client)
    vectors = client.embed_texts(["hello world"])

    assert len(vectors) == 1
    assert len(vectors[0]) == 768
    args, kwargs = mock_client.post.call_args
    assert args[0].endswith("/api/embeddings")
    assert kwargs["json"]["model"] == "nomic-embed-text"
    assert kwargs["json"]["prompt"] == "hello world"


def test_embed_texts_rejects_wrong_dimension():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    client = EmbeddingClient(settings=_settings(), client=mock_client)
    with pytest.raises(EmbeddingClientError, match="Expected embedding dimension 768"):
        client.embed_texts(["hello"])


def test_embed_texts_caches_duplicate_texts_in_same_run():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": _vector(fill=0.5)}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    client = EmbeddingClient(settings=_settings(), client=mock_client)
    vectors = client.embed_texts(["same", "other", "same"])

    assert mock_client.post.call_count == 2
    assert vectors[0] == vectors[2]
    assert len(vectors[1]) == 768


def test_embed_chunks_uses_chunk_text_attr():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": _vector()}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    client = EmbeddingClient(settings=_settings(), client=mock_client)
    chunks = [
        SimpleNamespace(chunk_text="alpha"),
        SimpleNamespace(chunk_text="beta"),
    ]
    vectors = client.embed_chunks(chunks)
    assert len(vectors) == 2
    assert mock_client.post.call_count == 2


def test_connection_error():
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")
    client = EmbeddingClient(settings=_settings(), client=mock_client)

    with pytest.raises(EmbeddingClientError, match="Failed to reach Ollama"):
        client.embed_texts(["hello"])


def test_timeout_error():
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.TimeoutException("timed out")
    client = EmbeddingClient(settings=_settings(), client=mock_client)

    with pytest.raises(EmbeddingClientError, match="timed out"):
        client.embed_texts(["hello"])


def test_invalid_missing_embedding_list():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"not_embedding": []}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    client = EmbeddingClient(settings=_settings(), client=mock_client)

    with pytest.raises(EmbeddingClientError, match="missing 'embedding'"):
        client.embed_texts(["hello"])


def test_http_error_status():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "internal error"

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    client = EmbeddingClient(settings=_settings(), client=mock_client)

    with pytest.raises(EmbeddingClientError, match="HTTP 500"):
        client.embed_texts(["hello"])


def test_rejects_blank_input():
    client = EmbeddingClient(settings=_settings(), client=MagicMock())
    with pytest.raises(EmbeddingClientError, match="non-empty"):
        client.embed_texts(["  "])


def test_uses_configured_ollama_url_not_hardcoded():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": _vector()}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    client = EmbeddingClient(
        settings=_settings(ollama_base_url="http://custom-ollama:11434"),
        client=mock_client,
    )
    client.embed_texts(["hi"])
    assert mock_client.post.call_args.args[0].startswith(
        "http://custom-ollama:11434/"
    )


def test_owns_and_closes_client_when_not_injected():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": _vector()}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response

    with patch(
        "app.services.embedding_client.httpx.Client",
        return_value=mock_client,
    ):
        client = EmbeddingClient(settings=_settings())
        vectors = client.embed_texts(["hi"])

    assert len(vectors[0]) == 768
    mock_client.close.assert_called_once()
