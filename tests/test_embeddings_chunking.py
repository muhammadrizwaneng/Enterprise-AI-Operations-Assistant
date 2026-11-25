"""Unit tests for document chunking (no embeddings / DB)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from experiments.embeddings.chunking import (
    DEFAULT_DOCUMENTS_DIR,
    ChunkingError,
    TextChunk,
    chunk_documents,
    chunk_text,
    load_markdown_documents,
)


def test_empty_input_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []


def test_short_text_single_chunk():
    text = "Hello world"
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=100, document_name="x.md")
    assert len(chunks) == 1
    assert chunks[0].chunk_text == text
    assert chunks[0].chunk_index == 0
    assert chunks[0].character_count == len(text)
    assert chunks[0].document_name == "x.md"


def test_long_text_multiple_chunks_and_indexes():
    text = "A" * 1200
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
    assert len(chunks) == 3
    assert [c.chunk_index for c in chunks] == [0, 1, 2]
    assert chunks[0].character_count == 500
    assert chunks[1].character_count == 500
    assert chunks[2].character_count == 400  # final window: chars 800..1199


def test_adjacent_chunks_share_overlap():
    text = "".join(chr(65 + (i % 26)) for i in range(50))
    size, overlap = 20, 5
    chunks = chunk_text(text, chunk_size=size, chunk_overlap=overlap)
    assert len(chunks) >= 2
    assert chunks[0].chunk_text[-overlap:] == chunks[1].chunk_text[:overlap]


def test_invalid_chunk_size():
    with pytest.raises(ChunkingError, match="chunk_size"):
        chunk_text("abc", chunk_size=0)
    with pytest.raises(ChunkingError, match="chunk_size"):
        chunk_text("abc", chunk_size=-10)


def test_invalid_overlap():
    with pytest.raises(ChunkingError, match="chunk_overlap"):
        chunk_text("abc", chunk_size=10, chunk_overlap=-1)
    with pytest.raises(ChunkingError, match="smaller than chunk_size"):
        chunk_text("abc", chunk_size=10, chunk_overlap=10)
    with pytest.raises(ChunkingError, match="smaller than chunk_size"):
        chunk_text("abc", chunk_size=10, chunk_overlap=15)


def test_chunk_indexes_are_sequential_per_document():
    docs = [
        ("a.md", "X" * 600),
        ("b.md", "Y" * 100),
    ]
    chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=100)
    a_chunks = [c for c in chunks if c.document_name == "a.md"]
    b_chunks = [c for c in chunks if c.document_name == "b.md"]
    assert [c.chunk_index for c in a_chunks] == list(range(len(a_chunks)))
    assert [c.chunk_index for c in b_chunks] == [0]


def test_load_markdown_files_without_modifying_them():
    assert DEFAULT_DOCUMENTS_DIR.is_dir()
    paths = sorted(DEFAULT_DOCUMENTS_DIR.glob("*.md"))
    assert len(paths) == 6

    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    docs = load_markdown_documents()
    assert len(docs) == 6
    names = [name for name, _ in docs]
    assert names == sorted(names)
    assert set(names) == {p.name for p in paths}

    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    assert before == after


def test_chunk_documents_processes_all_policy_files():
    chunks = chunk_documents(chunk_size=500, chunk_overlap=100)
    names = {c.document_name for c in chunks}
    expected = {
        "refund_policy.md",
        "delivery_policy.md",
        "employee_handbook.md",
        "product_documentation.md",
        "customer_support_guidelines.md",
        "privacy_policy.md",
    }
    assert names == expected
    assert all(isinstance(c, TextChunk) for c in chunks)
    assert all(c.character_count == len(c.chunk_text) for c in chunks)
    assert len(chunks) > 6  # at least one chunk per doc, usually more
