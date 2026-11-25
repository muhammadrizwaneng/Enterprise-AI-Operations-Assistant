"""Tests for document_embeddings model / pgvector schema."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db.base import Base
from app.models.document_embedding import EMBEDDING_DIMENSIONS, DocumentEmbedding


def test_document_embeddings_registered_on_metadata():
    assert "document_embeddings" in Base.metadata.tables


def test_embedding_dimension_constant_matches_nomic():
    assert EMBEDDING_DIMENSIONS == 768
    table = Base.metadata.tables["document_embeddings"]
    embedding_col = table.c.embedding
    # pgvector SQLAlchemy Vector exposes dim
    assert getattr(embedding_col.type, "dim", None) == 768


def test_unique_constraint_document_name_chunk_index():
    table = Base.metadata.tables["document_embeddings"]
    constraint_names = {c.name for c in table.constraints if c.name}
    assert "uq_document_embeddings_document_chunk" in constraint_names


def test_required_columns_present():
    table = Base.metadata.tables["document_embeddings"]
    expected = {
        "id",
        "document_name",
        "chunk_index",
        "chunk_text",
        "embedding",
        "metadata",
        "created_at",
    }
    assert expected.issubset(set(table.c.keys()))


def test_create_and_read_document_embedding_roundtrip():
    from app.db.init_db import init_db
    from app.db.session import SessionLocal, engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
    except OperationalError:
        pytest.skip("PostgreSQL is not available")

    init_db()

    vector = [0.01 * i for i in range(EMBEDDING_DIMENSIONS)]
    assert len(vector) == 768

    row_id = uuid.uuid4()
    doc_name = f"test-policy-{row_id}.md"

    with SessionLocal() as db:
        row = DocumentEmbedding(
            id=row_id,
            document_name=doc_name,
            chunk_index=0,
            chunk_text="Refund requests must be submitted within 30 days.",
            embedding=vector,
            chunk_metadata={"source": "unit-test", "section": "refunds"},
        )
        db.add(row)
        db.commit()

        loaded = db.scalar(
            select(DocumentEmbedding).where(DocumentEmbedding.id == row_id)
        )
        assert loaded is not None
        assert loaded.document_name == doc_name
        assert loaded.chunk_index == 0
        assert len(loaded.embedding) == 768
        assert loaded.chunk_metadata["source"] == "unit-test"

        # Unique constraint: same document_name + chunk_index should fail
        dup = DocumentEmbedding(
            document_name=doc_name,
            chunk_index=0,
            chunk_text="duplicate chunk",
            embedding=vector,
        )
        db.add(dup)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # cleanup test row(s)
        db.delete(loaded)
        db.commit()

    # Confirm table exists in live DB and business counts untouched
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'document_embeddings'"
            )
        ).scalar()
        assert exists == 1
        customers = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        orders = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        assert customers == 500
        assert orders == 2000


def test_wrong_embedding_dimension_rejected_by_database():
    from app.db.init_db import init_db
    from app.db.session import SessionLocal, engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
    except OperationalError:
        pytest.skip("PostgreSQL is not available")

    init_db()

    with SessionLocal() as db:
        bad = DocumentEmbedding(
            document_name=f"bad-dim-{uuid.uuid4()}.md",
            chunk_index=0,
            chunk_text="too short vector",
            embedding=[0.1, 0.2, 0.3],  # not 768
        )
        db.add(bad)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()
