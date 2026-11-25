"""
Ollama embedding client for Phase 2 document ingestion.

Uses local ``nomic-embed-text`` (768 dimensions) by default.
Does not implement semantic search or RAG.
"""

from __future__ import annotations

from typing import Any, Sequence

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.document_embedding import EMBEDDING_DIMENSIONS

logger = get_logger(__name__)


class EmbeddingClientError(RuntimeError):
    """Raised when embedding generation fails."""


class EmbeddingClient:
    """
    Generate text embeddings via Ollama ``POST /api/embeddings``.

    Within a single client instance / ingestion run, identical texts are
    embedded only once (simple in-memory cache).
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        base_url: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.base_url = (
            base_url or self.settings.ollama_base_url
        ).rstrip("/")
        self.model = model or self.settings.embedding_model
        self.dimensions = dimensions or self.settings.embedding_dimensions
        if self.dimensions != EMBEDDING_DIMENSIONS:
            # Keep storage model and client aligned unless explicitly overridden.
            logger.warning(
                "EmbeddingClient dimensions=%s (document_embeddings expects %s)",
                self.dimensions,
                EMBEDDING_DIMENSIONS,
            )
        self.timeout = (
            self.settings.embedding_timeout_seconds
            if timeout is None
            else timeout
        )
        self._client = client
        self._cache: dict[str, list[float]] = {}

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed each text; reuse cached vectors for duplicates in this run."""
        if not texts:
            return []

        owns_client = self._client is None
        http_client = self._client or httpx.Client(timeout=self.timeout)
        results: list[list[float]] = []

        try:
            for text in texts:
                if not isinstance(text, str) or not text.strip():
                    raise EmbeddingClientError(
                        "Each input text must be a non-empty string"
                    )
                cached = self._cache.get(text)
                if cached is not None:
                    results.append(list(cached))
                    continue
                vector = self._embed_one(http_client, text)
                self._cache[text] = vector
                results.append(list(vector))
        finally:
            if owns_client:
                http_client.close()

        return results

    def embed_chunks(
        self,
        chunks: Sequence[Any],
        *,
        text_attr: str = "chunk_text",
    ) -> list[list[float]]:
        """
        Embed a sequence of chunk objects (e.g. ``TextChunk``).

        Returns embeddings aligned with the input order.
        """
        texts = [getattr(chunk, text_attr) for chunk in chunks]
        return self.embed_texts(texts)

    def _embed_one(self, http_client: httpx.Client, text: str) -> list[float]:
        endpoint = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model, "prompt": text}
        logger.info(
            "Embedding request model=%s chars=%s",
            self.model,
            len(text),
        )

        try:
            response = http_client.post(endpoint, json=payload)
        except httpx.TimeoutException as exc:
            raise EmbeddingClientError(
                f"Ollama embedding timed out after {self.timeout}s"
            ) from exc
        except httpx.HTTPError as exc:
            raise EmbeddingClientError(
                f"Failed to reach Ollama at {self.base_url}: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise EmbeddingClientError(
                f"Ollama embeddings HTTP {response.status_code}: "
                f"{response.text[:400]}"
            )

        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:
            raise EmbeddingClientError(
                "Ollama returned non-JSON embedding response"
            ) from exc

        vector = data.get("embedding")
        if not isinstance(vector, list) or not vector:
            raise EmbeddingClientError(
                "Invalid Ollama embedding response: missing 'embedding' list"
            )
        if not all(isinstance(x, (int, float)) for x in vector):
            raise EmbeddingClientError(
                "Invalid Ollama embedding response: non-numeric values"
            )

        floats = [float(x) for x in vector]
        if len(floats) != self.dimensions:
            raise EmbeddingClientError(
                f"Expected embedding dimension {self.dimensions}, "
                f"got {len(floats)}"
            )
        return floats

    def clear_cache(self) -> None:
        """Drop the in-run cache (tests / new ingestion run)."""
        self._cache.clear()
