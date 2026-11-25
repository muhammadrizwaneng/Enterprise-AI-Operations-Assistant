"""Pydantic schemas for semantic search (Phase 3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

# Keep in sync with Settings.semantic_search_* defaults.
DEFAULT_TOP_K = 5
MAX_TOP_K = 20


class SemanticSearchRequest(BaseModel):
    """Natural-language search over document embeddings."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural-language question or search phrase.",
    )
    top_k: int = Field(
        default=DEFAULT_TOP_K,
        ge=1,
        le=MAX_TOP_K,
        description="Maximum number of chunks to return.",
    )
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum cosine similarity (1 - distance). "
            "Use 0 to return the top_k results regardless of score."
        ),
    )

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("query must not be empty or whitespace-only")
        return value


class SemanticSearchResult(BaseModel):
    """One ranked document chunk."""

    document_name: str
    chunk_index: int
    chunk_text: str
    similarity: float
    distance: float
    metadata: dict[str, Any] | None = None


class SemanticSearchResponse(BaseModel):
    """Semantic search API response."""

    query: str
    top_k: int
    min_similarity: float
    results: list[SemanticSearchResult] = Field(default_factory=list)
