"""API tests for POST /api/v1/rag/ask (mocked RAGService; no live DB/Ollama)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.rag import RagAskResponse, RagRetrievalInfo, RagSource
from app.services.rag import RAGError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.init_db", lambda: None)

    def _override_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _ok_response() -> RagAskResponse:
    return RagAskResponse(
        question="What is your refund policy?",
        answer="Refunds may be requested within 30 days.",
        model="llama3.2",
        provider="ollama",
        sources=[
            RagSource(
                document_name="refund_policy.md",
                chunk_index=0,
                similarity=0.72,
                distance=0.28,
                chunk_text="Refunds within 30 days.",
            )
        ],
        retrieval=RagRetrievalInfo(top_k=5, min_similarity=0.5),
    )


def test_api_rag_ask_success(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.ask.return_value = _ok_response()
    monkeypatch.setattr("app.api.rag.RAGService", lambda db: mock_service)

    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "What is your refund policy?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answer"].startswith("Refunds")
    assert body["model"] == "llama3.2"
    assert body["provider"] == "ollama"
    assert body["retrieval"]["top_k"] == 5
    assert body["retrieval"]["min_similarity"] == pytest.approx(0.5)
    assert len(body["sources"]) == 1
    assert body["sources"][0]["document_name"] == "refund_policy.md"
    assert body["sources"][0]["chunk_index"] == 0
    assert "chunk_text" in body["sources"][0]
    assert "similarity" in body["sources"][0]
    assert "distance" in body["sources"][0]
    mock_service.ask.assert_called_once()


def test_api_rejects_empty_question(client):
    assert client.post("/api/v1/rag/ask", json={"question": ""}).status_code == 422


def test_api_rejects_whitespace_question(client):
    assert (
        client.post("/api/v1/rag/ask", json={"question": "   "}).status_code == 422
    )


def test_api_rejects_top_k_below_one(client):
    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "refund", "top_k": 0},
    )
    assert response.status_code == 422


def test_api_rejects_top_k_above_twenty(client):
    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "refund", "top_k": 21},
    )
    assert response.status_code == 422


def test_api_rejects_min_similarity_below_zero(client):
    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "refund", "min_similarity": -0.1},
    )
    assert response.status_code == 422


def test_api_rejects_min_similarity_above_one(client):
    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "refund", "min_similarity": 1.1},
    )
    assert response.status_code == 422


def test_api_maps_semantic_search_error(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.ask.side_effect = RAGError(
        "Failed to generate query embedding",
        status_code=502,
    )
    monkeypatch.setattr("app.api.rag.RAGService", lambda db: mock_service)

    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "refund policy"},
    )
    assert response.status_code == 502
    assert "embedding" in response.json()["detail"].lower()


def test_api_maps_llm_error(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.ask.side_effect = RAGError(
        "Ollama timed out after 60s",
        status_code=504,
    )
    monkeypatch.setattr("app.api.rag.RAGService", lambda db: mock_service)

    response = client.post(
        "/api/v1/rag/ask",
        json={"question": "refund policy"},
    )
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


def test_api_response_source_structure(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.ask.return_value = _ok_response()
    monkeypatch.setattr("app.api.rag.RAGService", lambda db: mock_service)

    body = client.post(
        "/api/v1/rag/ask",
        json={"question": "What is your refund policy?"},
    ).json()
    source = body["sources"][0]
    assert set(source.keys()) >= {
        "document_name",
        "chunk_index",
        "similarity",
        "distance",
        "chunk_text",
    }
