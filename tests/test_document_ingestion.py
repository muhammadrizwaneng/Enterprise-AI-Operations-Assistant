"""Unit tests for document embedding ingestion (mocked Ollama + DB session)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.document_embedding import EMBEDDING_DIMENSIONS, DocumentEmbedding
from app.services.document_ingestion import (
    DocumentIngestionError,
    DocumentIngestionService,
    EmbeddedChunk,
)
from app.services.embedding_client import EmbeddingClientError


def _vec(fill: float = 0.01) -> list[float]:
    return [fill] * EMBEDDING_DIMENSIONS


def _chunk(
    document_name: str,
    chunk_index: int,
    text: str = "chunk text",
) -> SimpleNamespace:
    return SimpleNamespace(
        document_name=document_name,
        chunk_index=chunk_index,
        chunk_text=text,
        character_count=len(text),
    )


def _embedded(
    document_name: str,
    chunk_index: int,
    text: str = "chunk text",
    fill: float = 0.01,
) -> EmbeddedChunk:
    return EmbeddedChunk(
        document_name=document_name,
        chunk_index=chunk_index,
        chunk_text=text,
        embedding=_vec(fill),
        metadata={"character_count": len(text)},
    )


def _db_with_stored_names(names: list[str]) -> MagicMock:
    db = MagicMock()
    db.scalars.return_value.all.return_value = list(names)
    db.execute.return_value = MagicMock(rowcount=0)
    return db


def test_embed_chunks_maps_vectors_and_metadata():
    embedding_client = MagicMock()
    embedding_client.model = "nomic-embed-text"
    embedding_client.embed_chunks.return_value = [_vec(0.1), _vec(0.2)]

    service = DocumentIngestionService(MagicMock(), embedding_client=embedding_client)
    chunks = [_chunk("a.md", 0, "one"), _chunk("a.md", 1, "two")]
    embedded = service.embed_chunks(chunks)

    assert len(embedded) == 2
    assert embedded[0].document_name == "a.md"
    assert embedded[0].embedding[0] == pytest.approx(0.1)
    assert embedded[0].metadata["embedding_model"] == "nomic-embed-text"
    assert embedded[0].metadata["embedding_dimensions"] == 768


def test_embed_chunks_wraps_embedding_client_errors():
    embedding_client = MagicMock()
    embedding_client.embed_chunks.side_effect = EmbeddingClientError("boom")
    service = DocumentIngestionService(MagicMock(), embedding_client=embedding_client)

    with pytest.raises(DocumentIngestionError, match="boom"):
        service.embed_chunks([_chunk("a.md", 0)])


def test_save_deletes_then_inserts_per_document():
    db = MagicMock()
    delete_result = MagicMock()
    delete_result.rowcount = 3
    db.execute.return_value = delete_result

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [
            _embedded("policy.md", 0, "a"),
            _embedded("policy.md", 1, "b"),
        ]
    )

    assert result.documents_processed == 1
    assert result.rows_deleted == 3
    assert result.rows_inserted == 2
    assert result.embeddings_generated == 2
    assert result.rows_purged == 0
    assert result.purged_document_names == []
    db.execute.assert_called_once()
    assert db.add.call_count == 2
    db.commit.assert_called_once()
    db.rollback.assert_not_called()
    db.scalars.assert_not_called()

    added = [c.args[0] for c in db.add.call_args_list]
    assert all(isinstance(row, DocumentEmbedding) for row in added)
    assert [row.chunk_index for row in added] == [0, 1]


def test_default_ignores_corpus_document_names():
    """Default mode must not purge; corpus list is ignored."""
    db = MagicMock()
    db.execute.return_value = MagicMock(rowcount=1)

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [_embedded("support.md", 0)],
        purge_missing_documents=False,
        corpus_document_names=["support.md"],  # ignored
    )

    assert result.rows_purged == 0
    assert result.purged_document_names == []
    db.scalars.assert_not_called()
    assert db.execute.call_count == 1


def test_duplicate_ingestion_replaces_document_rows():
    """Re-running ingestion deletes existing rows then inserts again."""
    db = MagicMock()
    first_delete = MagicMock(rowcount=0)
    second_delete = MagicMock(rowcount=2)
    db.execute.side_effect = [first_delete, second_delete]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    items = [_embedded("returns.md", 0), _embedded("returns.md", 1)]

    first = service.save_embedded_chunks(items)
    second = service.save_embedded_chunks(items)

    assert first.rows_deleted == 0
    assert first.rows_inserted == 2
    assert second.rows_deleted == 2
    assert second.rows_inserted == 2
    assert db.commit.call_count == 2


def test_updated_document_removes_stale_chunks():
    db = MagicMock()
    delete_result = MagicMock(rowcount=3)
    db.execute.return_value = delete_result

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks([_embedded("shipping.md", 0, "only")])

    assert result.rows_deleted == 3
    assert result.rows_inserted == 1
    assert db.add.call_count == 1
    added = db.add.call_args.args[0]
    assert added.chunk_index == 0
    assert added.chunk_text == "only"


def test_multi_document_batch_deletes_each_document():
    db = MagicMock()
    db.execute.side_effect = [
        MagicMock(rowcount=1),
        MagicMock(rowcount=2),
    ]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [
            _embedded("a.md", 0),
            _embedded("b.md", 0),
            _embedded("b.md", 1),
        ]
    )

    assert result.documents_processed == 2
    assert result.rows_deleted == 3
    assert result.rows_inserted == 3
    assert db.execute.call_count == 2


def test_transaction_rollback_on_commit_failure():
    db = MagicMock()
    db.execute.return_value = MagicMock(rowcount=0)
    db.commit.side_effect = RuntimeError("disk full")

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="rolled back"):
        service.save_embedded_chunks([_embedded("a.md", 0)])

    db.rollback.assert_called_once()


def test_rejects_wrong_embedding_dimension_before_db():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    bad = EmbeddedChunk(
        document_name="a.md",
        chunk_index=0,
        chunk_text="text",
        embedding=[0.1, 0.2],
    )
    with pytest.raises(DocumentIngestionError, match="768 dimensions"):
        service.save_embedded_chunks([bad])
    db.commit.assert_not_called()
    db.execute.assert_not_called()


def test_ingest_chunks_end_to_end_with_mocks():
    embedding_client = MagicMock()
    embedding_client.model = "nomic-embed-text"
    embedding_client.embed_chunks.return_value = [_vec(0.3)]

    db = MagicMock()
    db.execute.return_value = MagicMock(rowcount=0)

    service = DocumentIngestionService(db, embedding_client=embedding_client)
    result = service.ingest_chunks([_chunk("faq.md", 0, "answer")])

    assert result.rows_inserted == 1
    assert result.documents_processed == 1
    embedding_client.embed_chunks.assert_called_once()
    db.commit.assert_called_once()


def test_empty_batch_is_noop():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks([])
    assert result.rows_inserted == 0
    assert result.rows_purged == 0
    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_sync_purges_missing_documents():
    db = _db_with_stored_names(
        ["support.md", "delivery.md", "privacy_policy.md"]
    )
    # purge delete + replace support + replace delivery
    db.execute.side_effect = [
        MagicMock(rowcount=4),  # purged privacy rows
        MagicMock(rowcount=2),  # replace support
        MagicMock(rowcount=1),  # replace delivery
    ]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [
            _embedded("support.md", 0),
            _embedded("delivery.md", 0),
        ],
        purge_missing_documents=True,
        corpus_document_names=["support.md", "delivery.md"],
    )

    assert result.purged_document_names == ["privacy_policy.md"]
    assert result.rows_purged == 4
    assert result.rows_deleted == 3
    assert result.rows_inserted == 2
    assert result.document_names == ["support.md", "delivery.md"]
    db.commit.assert_called_once()


def test_sync_replaces_documents_included_in_corpus():
    db = _db_with_stored_names(["support.md"])
    db.execute.side_effect = [
        MagicMock(rowcount=5),  # replace support
    ]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [_embedded("support.md", 0, "new"), _embedded("support.md", 1, "new2")],
        purge_missing_documents=True,
        corpus_document_names=["support.md"],
    )

    assert result.rows_purged == 0
    assert result.purged_document_names == []
    assert result.rows_deleted == 5
    assert result.rows_inserted == 2
    assert db.add.call_count == 2


def test_sync_empty_document_in_corpus_clears_old_chunks():
    """Corpus member with zero chunks must still delete its old rows."""
    db = _db_with_stored_names(["support.md", "empty.md"])
    db.execute.side_effect = [
        MagicMock(rowcount=2),  # replace support
        MagicMock(rowcount=3),  # clear empty.md
    ]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [_embedded("support.md", 0)],
        purge_missing_documents=True,
        corpus_document_names=["support.md", "empty.md"],
    )

    assert result.rows_purged == 0
    assert result.documents_processed == 2
    assert result.rows_inserted == 1
    assert result.rows_deleted == 5
    # Two replace deletes: support.md then empty.md (corpus order)
    assert db.execute.call_count == 2
    assert db.add.call_count == 1


def test_sync_rejects_empty_corpus():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="non-empty"):
        service.save_embedded_chunks(
            [_embedded("a.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=[],
        )
    db.execute.assert_not_called()
    db.commit.assert_not_called()
    db.scalars.assert_not_called()


def test_sync_rejects_missing_corpus_list():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="required"):
        service.save_embedded_chunks(
            [_embedded("a.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=None,
        )
    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_sync_rejects_duplicate_corpus_names():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="duplicate"):
        service.save_embedded_chunks(
            [_embedded("a.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=["a.md", "a.md"],
        )
    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_sync_rejects_blank_corpus_names():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="non-blank"):
        service.save_embedded_chunks(
            [_embedded("a.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=["a.md", "  "],
        )
    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_sync_rejects_whitespace_padded_filenames_without_stripping():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="whitespace"):
        service.save_embedded_chunks(
            [_embedded("privacy_policy.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=[" privacy_policy.md"],
        )
    db.execute.assert_not_called()


def test_sync_preserves_exact_filename_convention():
    """Comparisons use bare filenames as stored (e.g. privacy_policy.md)."""
    db = _db_with_stored_names(["privacy_policy.md", "refund_policy.md"])
    db.execute.side_effect = [
        MagicMock(rowcount=8),  # purge refund_policy.md
        MagicMock(rowcount=8),  # replace privacy_policy.md
    ]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    result = service.save_embedded_chunks(
        [_embedded("privacy_policy.md", 0)],
        purge_missing_documents=True,
        corpus_document_names=["privacy_policy.md"],
    )

    assert result.purged_document_names == ["refund_policy.md"]
    assert "privacy_policy.md" in result.document_names
    # Ensure we never rewrote to a path-stripped or extension-stripped form
    assert result.document_names == ["privacy_policy.md"]


def test_sync_commit_failure_rolls_back_purge_and_replace():
    db = _db_with_stored_names(["keep.md", "orphan.md"])
    db.execute.side_effect = [
        MagicMock(rowcount=2),  # purge orphan
        MagicMock(rowcount=1),  # replace keep
    ]
    db.commit.side_effect = RuntimeError("disk full")

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="rolled back"):
        service.save_embedded_chunks(
            [_embedded("keep.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=["keep.md"],
        )

    db.rollback.assert_called_once()


def test_ingest_chunks_forwards_synchronization_arguments():
    embedding_client = MagicMock()
    embedding_client.model = "nomic-embed-text"
    embedding_client.embed_chunks.return_value = [_vec(0.1)]

    service = DocumentIngestionService(MagicMock(), embedding_client=embedding_client)
    with patch.object(
        service,
        "save_embedded_chunks",
        wraps=None,
        return_value=MagicMock(),
    ) as save:
        service.ingest_chunks(
            [_chunk("faq.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=["faq.md"],
        )

    save.assert_called_once()
    kwargs = save.call_args.kwargs
    assert kwargs["purge_missing_documents"] is True
    assert kwargs["corpus_document_names"] == ["faq.md"]
    assert len(save.call_args.args[0]) == 1


def test_sync_rejects_chunks_outside_corpus_with_no_writes():
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="outside the corpus"):
        service.save_embedded_chunks(
            [_embedded("extra.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=["support.md"],
        )
    db.execute.assert_not_called()
    db.commit.assert_not_called()
    db.scalars.assert_not_called()


def test_ingest_chunks_embedding_failure_prevents_database_writes():
    """If embedding fails, ingest_chunks must not touch the database."""
    db = MagicMock()
    service = DocumentIngestionService(db, embedding_client=MagicMock())

    with patch.object(
        service,
        "embed_chunks",
        side_effect=DocumentIngestionError("ollama unavailable"),
    ):
        with pytest.raises(DocumentIngestionError, match="ollama unavailable"):
            service.ingest_chunks([_chunk("faq.md", 0)])

    db.execute.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_insertion_failure_midway_triggers_rollback():
    """Replace deletes succeed; a later insert failure rolls back the unit of work."""
    db = MagicMock()
    db.execute.return_value = MagicMock(rowcount=1)
    db.add.side_effect = [None, RuntimeError("insert failed")]

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="rolled back"):
        service.save_embedded_chunks(
            [
                _embedded("policy.md", 0, "a"),
                _embedded("policy.md", 1, "b"),
            ]
        )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_sync_purge_failure_triggers_rollback():
    """Orphan-cleanup execute failure must roll back and never commit."""
    db = _db_with_stored_names(["keep.md", "orphan.md"])
    db.execute.side_effect = RuntimeError("purge failed")

    service = DocumentIngestionService(db, embedding_client=MagicMock())
    with pytest.raises(DocumentIngestionError, match="rolled back"):
        service.save_embedded_chunks(
            [_embedded("keep.md", 0)],
            purge_missing_documents=True,
            corpus_document_names=["keep.md"],
        )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
    db.add.assert_not_called()
