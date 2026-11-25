"""Unit tests for SemanticSearchService (mocked embed + DB; no live services)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.models.document_embedding import EMBEDDING_DIMENSIONS
from app.services.embedding_client import EmbeddingClientError
from app.services.semantic_search import SemanticSearchError, SemanticSearchService


def _vec(fill: float = 0.01) -> list[float]:
    return [fill] * EMBEDDING_DIMENSIONS


def _settings() -> Settings:
    return Settings(
        semantic_search_default_top_k=5,
        semantic_search_max_top_k=20,
        embedding_dimensions=768,
        embedding_model="nomic-embed-text",
        ollama_base_url="http://127.0.0.1:11434",
    )


def _entity(
    name: str,
    index: int,
    text: str,
    metadata: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        document_name=name,
        chunk_index=index,
        chunk_text=text,
        chunk_metadata=metadata or {"source": "test"},
    )


def test_successful_semantic_search_ranks_by_cosine_distance():
    embedding_client = MagicMock()
    embedding_client.embed_texts.return_value = [_vec(0.5)]

    db = MagicMock()
    db.execute.return_value.all.return_value = [
        (_entity("refund_policy.md", 0, "refunds within 30 days"), 0.10),
        (_entity("privacy_policy.md", 1, "data retention"), 0.40),
        (_entity("delivery_policy.md", 0, "shipping times"), 0.55),
    ]

    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    response = service.search("What is your refund policy?", top_k=3)

    assert response.query == "What is your refund policy?"
    assert response.top_k == 3
    assert len(response.results) == 3
    assert response.results[0].document_name == "refund_policy.md"
    assert response.results[0].distance == pytest.approx(0.10)
    assert response.results[0].similarity == pytest.approx(0.90)
    assert response.results[1].similarity == pytest.approx(0.60)
    assert response.results[2].similarity == pytest.approx(0.45)
    embedding_client.embed_texts.assert_called_once_with(
        ["What is your refund policy?"]
    )
    db.execute.assert_called_once()


def test_top_k_default_and_limit_passed_to_query():
    embedding_client = MagicMock()
    embedding_client.embed_texts.return_value = [_vec()]
    db = MagicMock()
    db.execute.return_value.all.return_value = []

    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    response = service.search("refunds")
    assert response.top_k == 5
    assert response.results == []


def test_empty_query_rejected():
    service = SemanticSearchService(
        MagicMock(), embedding_client=MagicMock(), settings=_settings()
    )
    with pytest.raises(SemanticSearchError, match="whitespace-only|empty") as exc:
        service.search("")
    assert exc.value.status_code == 422


def test_whitespace_query_rejected():
    db = MagicMock()
    embedding_client = MagicMock()
    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    with pytest.raises(SemanticSearchError, match="whitespace-only|empty"):
        service.search("   \n\t  ")
    embedding_client.embed_texts.assert_not_called()
    db.execute.assert_not_called()


def test_invalid_top_k_rejected():
    service = SemanticSearchService(
        MagicMock(), embedding_client=MagicMock(), settings=_settings()
    )
    with pytest.raises(SemanticSearchError, match="top_k") as exc:
        service.search("refund", top_k=21)
    assert exc.value.status_code == 422


def test_embedding_failure_does_not_query_database():
    embedding_client = MagicMock()
    embedding_client.embed_texts.side_effect = EmbeddingClientError("down")
    db = MagicMock()
    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    with pytest.raises(SemanticSearchError, match="query embedding") as exc:
        service.search("refund policy")
    assert exc.value.status_code == 502
    db.execute.assert_not_called()


def test_database_query_failure():
    embedding_client = MagicMock()
    embedding_client.embed_texts.return_value = [_vec()]
    db = MagicMock()
    db.execute.side_effect = RuntimeError("db down")

    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    with pytest.raises(SemanticSearchError, match="database query") as exc:
        service.search("refund policy")
    assert exc.value.status_code == 500


def test_empty_database_results():
    embedding_client = MagicMock()
    embedding_client.embed_texts.return_value = [_vec()]
    db = MagicMock()
    db.execute.return_value.all.return_value = []

    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    response = service.search("unknown topic", top_k=5)
    assert response.results == []


def test_similarity_threshold_applied_in_sql_filter():
    embedding_client = MagicMock()
    embedding_client.embed_texts.return_value = [_vec()]
    db = MagicMock()
    # Service returns only rows already filtered by SQL; simulate one strong hit
    db.execute.return_value.all.return_value = [
        (_entity("refund_policy.md", 0, "refund window"), 0.05),
    ]

    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    response = service.search("refund", top_k=5, min_similarity=0.8)

    assert len(response.results) == 1
    assert response.results[0].similarity >= 0.8
    assert response.min_similarity == pytest.approx(0.8)
    db.execute.assert_called_once()


def test_query_is_stripped_before_embed():
    embedding_client = MagicMock()
    embedding_client.embed_texts.return_value = [_vec()]
    db = MagicMock()
    db.execute.return_value.all.return_value = []

    service = SemanticSearchService(
        db, embedding_client=embedding_client, settings=_settings()
    )
    response = service.search("  refund policy  ")
    assert response.query == "refund policy"
    embedding_client.embed_texts.assert_called_once_with(["refund policy"])
