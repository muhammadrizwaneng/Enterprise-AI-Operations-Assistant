"""Document chunk embeddings stored with pgvector (Phase 2 storage only)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Must match nomic-embed-text output size used in experiments/embeddings.
EMBEDDING_DIMENSIONS = 768


class DocumentEmbedding(Base):
    """
    One embedded text chunk from a source document.

    Rows are written by ``DocumentIngestionService`` (Phase 2).
    Ranked retrieval is provided by ``SemanticSearchService`` (Phase 3).
    RAG / LLM answer generation is not implemented here.
    """

    __tablename__ = "document_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "document_name",
            "chunk_index",
            name="uq_document_embeddings_document_chunk",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=False,
    )
    # Python attr cannot be named `metadata` (conflicts with DeclarativeBase.metadata).
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
