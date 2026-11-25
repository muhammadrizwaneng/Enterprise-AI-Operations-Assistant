"""
Semantic search over ``document_embeddings`` using pgvector cosine distance.

Phase 3 only: retrieve ranked chunks. Does not generate LLM answers or RAG.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.document_embedding import EMBEDDING_DIMENSIONS, DocumentEmbedding
from app.schemas.search import (
    SemanticSearchResponse,
    SemanticSearchResult,
)
from app.services.embedding_client import EmbeddingClient, EmbeddingClientError

logger = get_logger(__name__)


class SemanticSearchError(RuntimeError):
    """Raised when semantic search fails."""

    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


class SemanticSearchService:
    """Embed a query and rank stored document chunks by cosine distance."""

    def __init__(
        self,
        db: Session,
        *,
        embedding_client: EmbeddingClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.embedding_client = embedding_client or EmbeddingClient(
            settings=self.settings
        )

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_similarity: float = 0.0,
    ) -> SemanticSearchResponse:
        """
        Return the top matching chunks for ``query``.

        Embeddings are generated before any database query. The database
        session is used for a read-only ranked SELECT only.
        """
        cleaned = self._validate_query(query)
        limit = self._resolve_top_k(top_k)
        threshold = self._validate_min_similarity(min_similarity)

        query_vector = self._embed_query(cleaned)
        rows = self._query_similar_chunks(
            query_vector,
            top_k=limit,
            min_similarity=threshold,
        )

        results = [
            SemanticSearchResult(
                document_name=row.document_name,
                chunk_index=row.chunk_index,
                chunk_text=row.chunk_text,
                similarity=row.similarity,
                distance=row.distance,
                metadata=row.chunk_metadata,
            )
            for row in rows
        ]

        return SemanticSearchResponse(
            query=cleaned,
            top_k=limit,
            min_similarity=threshold,
            results=results,
        )

    def _embed_query(self, query: str) -> list[float]:
        try:
            vectors = self.embedding_client.embed_texts([query])
        except EmbeddingClientError as exc:
            logger.warning("Query embedding failed: %s", exc)
            raise SemanticSearchError(
                "Failed to generate query embedding",
                status_code=502,
            ) from exc

        if not vectors:
            raise SemanticSearchError(
                "Failed to generate query embedding",
                status_code=502,
            )
        vector = vectors[0]
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise SemanticSearchError(
                "Failed to generate query embedding",
                status_code=502,
            )
        return vector

    def _query_similar_chunks(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        min_similarity: float,
    ) -> list[_RankedChunk]:
        distance_expr = DocumentEmbedding.embedding.cosine_distance(query_vector)
        stmt = select(DocumentEmbedding, distance_expr.label("distance"))

        if min_similarity > 0.0:
            max_distance = 1.0 - min_similarity
            stmt = stmt.where(distance_expr <= max_distance)

        stmt = stmt.order_by(distance_expr).limit(top_k)

        try:
            result = self.db.execute(stmt)
            pairs = result.all()
        except Exception as exc:
            logger.exception("Semantic search database query failed")
            raise SemanticSearchError(
                "Semantic search database query failed",
                status_code=500,
            ) from exc

        ranked: list[_RankedChunk] = []
        for entity, distance in pairs:
            dist = float(distance)
            ranked.append(
                _RankedChunk(
                    document_name=entity.document_name,
                    chunk_index=entity.chunk_index,
                    chunk_text=entity.chunk_text,
                    chunk_metadata=entity.chunk_metadata,
                    distance=dist,
                    similarity=1.0 - dist,
                )
            )
        return ranked

    def _resolve_top_k(self, top_k: int | None) -> int:
        limit = (
            self.settings.semantic_search_default_top_k
            if top_k is None
            else top_k
        )
        max_k = self.settings.semantic_search_max_top_k
        if limit < 1 or limit > max_k:
            raise SemanticSearchError(
                f"top_k must be between 1 and {max_k}",
                status_code=422,
            )
        return limit

    @staticmethod
    def _validate_query(query: str) -> str:
        if not isinstance(query, str) or query.strip() == "":
            raise SemanticSearchError(
                "query must not be empty or whitespace-only",
                status_code=422,
            )
        return query.strip()

    @staticmethod
    def _validate_min_similarity(value: float) -> float:
        if value < 0.0 or value > 1.0:
            raise SemanticSearchError(
                "min_similarity must be between 0 and 1",
                status_code=422,
            )
        return float(value)


class _RankedChunk:
    __slots__ = (
        "document_name",
        "chunk_index",
        "chunk_text",
        "chunk_metadata",
        "distance",
        "similarity",
    )

    def __init__(
        self,
        *,
        document_name: str,
        chunk_index: int,
        chunk_text: str,
        chunk_metadata: dict[str, Any] | None,
        distance: float,
        similarity: float,
    ) -> None:
        self.document_name = document_name
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.chunk_metadata = chunk_metadata
        self.distance = distance
        self.similarity = similarity
