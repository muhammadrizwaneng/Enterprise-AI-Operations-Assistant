"""
Persist document chunk embeddings into ``document_embeddings``.

Replacement strategy (default)
------------------------------
For each ``document_name`` in a batch:
1. DELETE all existing rows for that document.
2. INSERT the new chunk rows.

Optional full-corpus synchronization
------------------------------------
When ``purge_missing_documents=True`` and an explicit non-empty
``corpus_document_names`` list is provided:
1. DELETE rows for documents absent from the corpus.
2. Replace rows for every corpus document (including those with zero chunks).
3. Commit once.

Default mode never deletes documents that are merely absent from the batch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.document_embedding import EMBEDDING_DIMENSIONS, DocumentEmbedding
from app.services.embedding_client import EmbeddingClient, EmbeddingClientError

logger = get_logger(__name__)


class DocumentIngestionError(RuntimeError):
    """Raised when ingestion fails."""


@dataclass(slots=True)
class EmbeddedChunk:
    """Chunk text + embedding ready for persistence."""

    document_name: str
    chunk_index: int
    chunk_text: str
    embedding: list[float]
    metadata: dict[str, Any] | None = None


@dataclass
class IngestionResult:
    documents_processed: int = 0
    chunks_received: int = 0
    embeddings_generated: int = 0
    # Rows removed while replacing documents that are being re-ingested.
    rows_deleted: int = 0
    rows_inserted: int = 0
    document_names: list[str] = field(default_factory=list)
    # Rows / names removed because they were absent from the declared corpus.
    rows_purged: int = 0
    purged_document_names: list[str] = field(default_factory=list)


class DocumentIngestionService:
    """Save embedded chunks using replace-by-document transactions."""

    def __init__(
        self,
        db: Session,
        *,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.db = db
        self.embedding_client = embedding_client or EmbeddingClient()

    def embed_chunks(self, chunks: Sequence[Any]) -> list[EmbeddedChunk]:
        """Generate embeddings for ``TextChunk``-like objects."""
        if not chunks:
            return []
        try:
            vectors = self.embedding_client.embed_chunks(chunks)
        except EmbeddingClientError as exc:
            raise DocumentIngestionError(str(exc)) from exc

        embedded: list[EmbeddedChunk] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            if len(vector) != EMBEDDING_DIMENSIONS:
                raise DocumentIngestionError(
                    f"Invalid embedding size {len(vector)} for "
                    f"{chunk.document_name}#{chunk.chunk_index}"
                )
            embedded.append(
                EmbeddedChunk(
                    document_name=chunk.document_name,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=vector,
                    metadata={
                        "character_count": getattr(
                            chunk, "character_count", len(chunk.chunk_text)
                        ),
                        "embedding_model": self.embedding_client.model,
                        "embedding_dimensions": EMBEDDING_DIMENSIONS,
                    },
                )
            )
        return embedded

    def save_embedded_chunks(
        self,
        embedded_chunks: Sequence[EmbeddedChunk],
        *,
        purge_missing_documents: bool = False,
        corpus_document_names: Sequence[str] | None = None,
    ) -> IngestionResult:
        """
        Replace DB rows for documents in ``embedded_chunks``.

        When ``purge_missing_documents`` is True, also remove embeddings for
        documents absent from the explicit ``corpus_document_names`` list and
        clear corpus members that currently have zero chunks.
        """
        result = IngestionResult(chunks_received=len(embedded_chunks))

        if not purge_missing_documents:
            # Default: ignore corpus_document_names; empty batch is a no-op.
            if not embedded_chunks:
                return result
            by_document = self._group_embedded_chunks(embedded_chunks)
            result.document_names = sorted(by_document.keys())
            result.documents_processed = len(by_document)
            result.embeddings_generated = len(embedded_chunks)
            return self._commit_replacements(result, by_document)

        corpus = self._validate_corpus_document_names(corpus_document_names)
        by_document = (
            self._group_embedded_chunks(embedded_chunks) if embedded_chunks else {}
        )
        unexpected = sorted(set(by_document) - set(corpus))
        if unexpected:
            raise DocumentIngestionError(
                "embedded chunks reference documents outside the corpus: "
                + ", ".join(unexpected)
            )

        result.document_names = list(corpus)
        result.documents_processed = len(corpus)
        result.embeddings_generated = len(embedded_chunks)

        try:
            stored_names = set(
                self.db.scalars(select(DocumentEmbedding.document_name).distinct()).all()
            )
            purged_names = sorted(stored_names - set(corpus))
            if purged_names:
                purged = self.db.execute(
                    delete(DocumentEmbedding).where(
                        DocumentEmbedding.document_name.in_(purged_names)
                    )
                )
                result.rows_purged = int(purged.rowcount or 0)
                result.purged_document_names = purged_names

            for document_name in corpus:
                items = by_document.get(document_name, [])
                deleted = self.db.execute(
                    delete(DocumentEmbedding).where(
                        DocumentEmbedding.document_name == document_name
                    )
                )
                result.rows_deleted += int(deleted.rowcount or 0)

                items_sorted = sorted(items, key=lambda c: c.chunk_index)
                for item in items_sorted:
                    self.db.add(
                        DocumentEmbedding(
                            document_name=item.document_name,
                            chunk_index=item.chunk_index,
                            chunk_text=item.chunk_text,
                            embedding=item.embedding,
                            chunk_metadata=item.metadata,
                        )
                    )
                    result.rows_inserted += 1

            self.db.commit()
        except DocumentIngestionError:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            logger.exception("Document ingestion failed; transaction rolled back")
            raise DocumentIngestionError(
                f"Ingestion failed and was rolled back: {exc}"
            ) from exc

        logger.info(
            "Synced corpus documents=%s inserted=%s replaced_deleted=%s purged=%s",
            result.documents_processed,
            result.rows_inserted,
            result.rows_deleted,
            result.rows_purged,
        )
        return result

    def ingest_chunks(
        self,
        chunks: Sequence[Any],
        *,
        purge_missing_documents: bool = False,
        corpus_document_names: Sequence[str] | None = None,
    ) -> IngestionResult:
        """Embed chunks then replace corresponding document rows."""
        embedded = self.embed_chunks(chunks)
        return self.save_embedded_chunks(
            embedded,
            purge_missing_documents=purge_missing_documents,
            corpus_document_names=corpus_document_names,
        )

    def count_stored_embeddings(self) -> int:
        return int(
            self.db.scalar(select(func.count()).select_from(DocumentEmbedding))
            or 0
        )

    def _commit_replacements(
        self,
        result: IngestionResult,
        by_document: dict[str, list[EmbeddedChunk]],
    ) -> IngestionResult:
        try:
            for document_name, items in by_document.items():
                deleted = self.db.execute(
                    delete(DocumentEmbedding).where(
                        DocumentEmbedding.document_name == document_name
                    )
                )
                result.rows_deleted += int(deleted.rowcount or 0)

                items_sorted = sorted(items, key=lambda c: c.chunk_index)
                for item in items_sorted:
                    self.db.add(
                        DocumentEmbedding(
                            document_name=item.document_name,
                            chunk_index=item.chunk_index,
                            chunk_text=item.chunk_text,
                            embedding=item.embedding,
                            chunk_metadata=item.metadata,
                        )
                    )
                    result.rows_inserted += 1

            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.exception("Document ingestion failed; transaction rolled back")
            raise DocumentIngestionError(
                f"Ingestion failed and was rolled back: {exc}"
            ) from exc

        logger.info(
            "Ingested documents=%s inserted=%s deleted=%s",
            result.documents_processed,
            result.rows_inserted,
            result.rows_deleted,
        )
        return result

    def _group_embedded_chunks(
        self,
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> dict[str, list[EmbeddedChunk]]:
        by_document: dict[str, list[EmbeddedChunk]] = {}
        for item in embedded_chunks:
            self._validate_embedded_chunk(item)
            by_document.setdefault(item.document_name, []).append(item)
        return by_document

    @staticmethod
    def _validate_corpus_document_names(
        names: Sequence[str] | None,
    ) -> list[str]:
        if names is None:
            raise DocumentIngestionError(
                "corpus_document_names is required when "
                "purge_missing_documents=True"
            )
        if len(names) == 0:
            raise DocumentIngestionError(
                "corpus_document_names must be non-empty when "
                "purge_missing_documents=True"
            )

        cleaned: list[str] = []
        seen: set[str] = set()
        for name in names:
            if not isinstance(name, str) or name.strip() == "":
                raise DocumentIngestionError(
                    "corpus_document_names entries must be non-blank filenames"
                )
            # Keep the exact string used in PostgreSQL (e.g. "privacy_policy.md").
            # Do not Path().name-strip or otherwise rewrite the value.
            if name != name.strip():
                raise DocumentIngestionError(
                    "corpus_document_names entries must not have leading/trailing "
                    f"whitespace: {name!r}"
                )
            if name in seen:
                raise DocumentIngestionError(
                    f"duplicate corpus document name: {name}"
                )
            seen.add(name)
            cleaned.append(name)
        return cleaned

    @staticmethod
    def _validate_embedded_chunk(item: EmbeddedChunk) -> None:
        if not item.document_name:
            raise DocumentIngestionError("document_name is required")
        if item.chunk_index < 0:
            raise DocumentIngestionError("chunk_index must be >= 0")
        if not item.chunk_text.strip():
            raise DocumentIngestionError("chunk_text must be non-empty")
        if len(item.embedding) != EMBEDDING_DIMENSIONS:
            raise DocumentIngestionError(
                f"embedding must have {EMBEDDING_DIMENSIONS} dimensions, "
                f"got {len(item.embedding)}"
            )
