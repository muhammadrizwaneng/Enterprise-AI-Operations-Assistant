"""Chat API and conversation history tests (mocked LLM)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.services.llm.base import LLMError, LLMResponse


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.name = "mock"
    provider.chat.return_value = LLMResponse(
        content="Mocked assistant reply",
        model="mock-model",
        provider="mock",
        finish_reason="stop",
        usage={"prompt_tokens": 3, "completion_tokens": 5},
    )
    return provider


@pytest.fixture
def chat_client(mock_provider, monkeypatch):
    """Test client with LLM provider mocked; uses real Postgres when available."""
    monkeypatch.setattr(
        "app.services.chat.get_llm_provider",
        lambda: mock_provider,
    )
    monkeypatch.setattr(
        "app.services.llm.factory.get_llm_provider",
        lambda: mock_provider,
    )

    from app.main import app

    with TestClient(app) as client:
        yield client, mock_provider


def _db_available(client: TestClient) -> bool:
    try:
        response = client.get("/api/v1/database/stats")
    except OperationalError:
        return False
    return response.status_code == 200


def test_chat_creates_conversation_and_returns_reply(chat_client):
    client, mock_provider = chat_client
    if not _db_available(client):
        pytest.skip("PostgreSQL not available")

    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello, what can you do?"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["reply"] == "Mocked assistant reply"
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"
    assert payload["conversation_id"]
    assert payload["message"]["role"] == "assistant"
    mock_provider.chat.assert_called_once()

    # History endpoint should include user + assistant
    conversation_id = payload["conversation_id"]
    history = client.get(f"/api/v1/conversations/{conversation_id}")
    assert history.status_code == 200
    body = history.json()
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["user", "assistant"]
    assert body["messages"][0]["content"] == "Hello, what can you do?"


def test_chat_reuses_conversation_history(chat_client):
    client, mock_provider = chat_client
    if not _db_available(client):
        pytest.skip("PostgreSQL not available")

    first = client.post("/api/v1/chat", json={"message": "First message"})
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/v1/chat",
        json={"message": "Follow-up question", "conversation_id": conversation_id},
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id
    assert mock_provider.chat.call_count == 2

    # Second call should include prior turns in the messages sent to the LLM
    sent_messages = mock_provider.chat.call_args.args[0]
    roles = [m.role for m in sent_messages]
    assert roles[0] == "system"
    assert roles.count("user") >= 2
    assert "assistant" in roles


def test_chat_unknown_conversation_returns_404(chat_client):
    client, _ = chat_client
    if not _db_available(client):
        pytest.skip("PostgreSQL not available")

    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "conversation_id": str(uuid4())},
    )
    assert response.status_code == 404


def test_chat_provider_error_maps_to_http(chat_client):
    client, mock_provider = chat_client
    if not _db_available(client):
        pytest.skip("PostgreSQL not available")

    mock_provider.chat.side_effect = LLMError("Ollama is down", status_code=503)
    response = client.post("/api/v1/chat", json={"message": "Ping"})
    assert response.status_code == 503
    assert "Ollama is down" in response.json()["detail"]


def test_chat_validation_rejects_empty_message(chat_client):
    client, _ = chat_client
    response = client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422
