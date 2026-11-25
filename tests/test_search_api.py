"""API tests for POST /api/v1/search/semantic (mocked service; no live DB/Ollama)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.search import SemanticSearchResponse, SemanticSearchResult
from app.services.semantic_search import SemanticSearchError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.init_db", lambda: None)

    def _override_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_semantic_search_success(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.search.return_value = SemanticSearchResponse(
        query="What is your refund policy?",
        top_k=5,
        min_similarity=0.0,
        results=[
            SemanticSearchResult(
                document_name="refund_policy.md",
                chunk_index=0,
                chunk_text="Refunds are available within 30 days.",
                similarity=0.91,
                distance=0.09,
                metadata={"embedding_model": "nomic-embed-text"},
            )
        ],
    )

    monkeypatch.setattr(
        "app.api.search.SemanticSearchService",
        lambda db: mock_service,
    )

    response = client.post(
        "/api/v1/search/semantic",
        json={"query": "What is your refund policy?", "top_k": 5},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["query"] == "What is your refund policy?"
    assert body["top_k"] == 5
    assert len(body["results"]) == 1
    assert body["results"][0]["document_name"] == "refund_policy.md"
    assert body["results"][0]["similarity"] == pytest.approx(0.91)
    mock_service.search.assert_called_once()


def test_api_rejects_empty_query(client):
    response = client.post("/api/v1/search/semantic", json={"query": ""})
    assert response.status_code == 422


def test_api_rejects_whitespace_query(client):
    response = client.post("/api/v1/search/semantic", json={"query": "   "})
    assert response.status_code == 422


def test_api_rejects_invalid_top_k(client):
    response = client.post(
        "/api/v1/search/semantic",
        json={"query": "refund", "top_k": 99},
    )
    assert response.status_code == 422


def test_api_maps_embedding_failure(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.search.side_effect = SemanticSearchError(
        "Failed to generate query embedding",
        status_code=502,
    )
    monkeypatch.setattr(
        "app.api.search.SemanticSearchService",
        lambda db: mock_service,
    )

    response = client.post(
        "/api/v1/search/semantic",
        json={"query": "refund policy"},
    )
    assert response.status_code == 502
    assert "embedding" in response.json()["detail"].lower()


def test_api_maps_database_failure(client, monkeypatch):
    mock_service = MagicMock()
    mock_service.search.side_effect = SemanticSearchError(
        "Semantic search database query failed",
        status_code=500,
    )
    monkeypatch.setattr(
        "app.api.search.SemanticSearchService",
        lambda db: mock_service,
    )

    response = client.post(
        "/api/v1/search/semantic",
        json={"query": "refund policy"},
    )
    assert response.status_code == 500
    assert "database" in response.json()["detail"].lower()
