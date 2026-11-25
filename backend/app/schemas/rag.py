"""Pydantic schemas for Retrieval-Augmented Generation (Phase 4)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Align with Settings.rag_top_k / semantic_search_max_top_k bounds.
DEFAULT_RAG_TOP_K = 5
MAX_RAG_TOP_K = 20
DEFAULT_RAG_MIN_SIMILARITY = 0.5


class RagAskRequest(BaseModel):
    """Stateless RAG question over ingested policy chunks."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural-language question to answer from retrieved documents.",
    )
    top_k: int = Field(
        default=DEFAULT_RAG_TOP_K,
        ge=1,
        le=MAX_RAG_TOP_K,
        description="Maximum chunks to retrieve for grounding.",
    )
    min_similarity: float = Field(
        default=DEFAULT_RAG_MIN_SIMILARITY,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity for retrieved chunks.",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("question must not be empty or whitespace-only")
        return value


class RagSource(BaseModel):
    """One retrieved chunk used as grounding context."""

    document_name: str
    chunk_index: int
    similarity: float
    distance: float
    chunk_text: str


class RagRetrievalInfo(BaseModel):
    """Retrieval settings applied for this answer."""

    top_k: int
    min_similarity: float


class RagAskResponse(BaseModel):
    """Grounded answer with source attribution."""

    question: str
    answer: str
    model: str
    provider: str
    sources: list[RagSource] = Field(default_factory=list)
    retrieval: RagRetrievalInfo
