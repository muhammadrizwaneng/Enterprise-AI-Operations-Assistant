"""
Runnable chunking experiment (no embeddings, no database writes).

Loads the six policy Markdown files from dataset/documents/, splits them into
overlapping character chunks, and prints a summary plus a tiny overlap demo.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from experiments.embeddings.chunking import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_DOCUMENTS_DIR,
    chunk_documents,
    chunk_text,
    load_markdown_documents,
)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _print_overlap_illustration() -> None:
    sample = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    size, overlap = 10, 4
    chunks = chunk_text(
        sample,
        chunk_size=size,
        chunk_overlap=overlap,
        document_name="illustration.txt",
    )
    print("--- Overlap illustration ---")
    print(f"Sample text ({len(sample)} chars): {sample}")
    print(f"chunk_size={size}, chunk_overlap={overlap}, step={size - overlap}")
    for chunk in chunks:
        print(
            f"  [{chunk.chunk_index}] {chunk.chunk_text!r} "
            f"({chunk.character_count} chars)"
        )
    if len(chunks) >= 2:
        shared = chunks[0].chunk_text[-overlap:]
        prefix = chunks[1].chunk_text[:overlap]
        print(f"Shared border between chunk 0 and 1: {shared!r} == {prefix!r}")
        print(f"Overlap matches: {shared == prefix}")
    print()


def run_demo(
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> None:
    print("=== Enterprise AI — Document Chunking Experiment (Phase 2) ===")
    print(f"Documents dir : {DEFAULT_DOCUMENTS_DIR}")
    print(f"chunk_size    : {chunk_size}")
    print(f"chunk_overlap : {chunk_overlap}")
    print()

    # Capture checksums before reading to prove we only read files.
    before_hashes = {
        path.name: _file_sha256(path)
        for path in sorted(DEFAULT_DOCUMENTS_DIR.glob("*.md"))
    }

    documents = load_markdown_documents()
    print(f"Loaded {len(documents)} Markdown documents (read-only).")
    print()

    all_chunks = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    for document_name, text in documents:
        doc_chunks = [c for c in all_chunks if c.document_name == document_name]
        print(f"Document : {document_name}")
        print(f"  characters : {len(text)}")
        print(f"  chunks     : {len(doc_chunks)}")
        if doc_chunks:
            first = doc_chunks[0]
            preview = first.chunk_text[:120].replace("\n", " ")
            print(f"  sample[0]  : {preview!r}…")
            if len(doc_chunks) > 1:
                second = doc_chunks[1]
                preview2 = second.chunk_text[:120].replace("\n", " ")
                print(f"  sample[1]  : {preview2!r}…")
        print()

    print(f"TOTAL chunks across all documents: {len(all_chunks)}")
    print()

    after_hashes = {
        path.name: _file_sha256(path)
        for path in sorted(DEFAULT_DOCUMENTS_DIR.glob("*.md"))
    }
    unchanged = before_hashes == after_hashes
    print(f"Original policy files unchanged: {unchanged}")
    print()

    _print_overlap_illustration()


if __name__ == "__main__":
    run_demo()
