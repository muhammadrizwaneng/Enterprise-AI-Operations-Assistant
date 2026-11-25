"""
Document text chunking helpers (Phase 2 educational step).

What is chunking?
    Splitting a long document into smaller pieces so each piece can later fit
    inside an embedding model's practical input size / context budget.

Why chunk before embeddings?
    Embedding models work best on focused passages. Huge documents are usually
    split so retrieval can return the most relevant section, not the whole file.

Overlap:
    Adjacent chunks intentionally share some characters so meaning near a
    boundary is not cut in half. Overlap is expected duplication — not a bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100

# Project root: .../Enterprise AI Operations Assistant
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCUMENTS_DIR = _PROJECT_ROOT / "dataset" / "documents"


class ChunkingError(ValueError):
    """Raised when chunking configuration or input is invalid."""


@dataclass(frozen=True, slots=True)
class TextChunk:
    """One chunk of a source document (DB-independent)."""

    document_name: str
    chunk_index: int
    chunk_text: str
    character_count: int


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    document_name: str = "document",
) -> list[TextChunk]:
    """
    Split ``text`` into overlapping character windows.

    Rules
    -----
    - Empty / whitespace-only text → empty list.
    - ``chunk_size`` must be > 0.
    - ``chunk_overlap`` must be >= 0 and < ``chunk_size``.
    - Step between windows is ``chunk_size - chunk_overlap``.
    - Characters are preserved; only intentional overlap is repeated.
    """
    if chunk_size <= 0:
        raise ChunkingError("chunk_size must be a positive integer")
    if chunk_overlap < 0:
        raise ChunkingError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ChunkingError(
            "chunk_overlap must be smaller than chunk_size "
            f"(got overlap={chunk_overlap}, size={chunk_size})"
        )

    if text is None:
        raise ChunkingError("text must be a string")
    if not isinstance(text, str):
        raise ChunkingError("text must be a string")
    if text == "" or text.strip() == "":
        return []

    step = chunk_size - chunk_overlap
    chunks: list[TextChunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end]
        chunks.append(
            TextChunk(
                document_name=document_name,
                chunk_index=index,
                chunk_text=piece,
                character_count=len(piece),
            )
        )
        index += 1
        if end >= len(text):
            break
        start += step

    return chunks


def load_markdown_documents(
    documents_dir: Path | str | None = None,
) -> list[tuple[str, str]]:
    """
    Read ``*.md`` files from ``dataset/documents/`` (read-only).

    Returns
    -------
    list of (filename, text) sorted by filename.
    """
    directory = Path(documents_dir) if documents_dir else DEFAULT_DOCUMENTS_DIR
    if not directory.is_dir():
        raise ChunkingError(f"Documents directory not found: {directory}")

    results: list[tuple[str, str]] = []
    for path in sorted(directory.glob("*.md")):
        # Read only — never write/modify source files.
        text = path.read_text(encoding="utf-8")
        results.append((path.name, text))
    return results


def chunk_documents(
    documents: list[tuple[str, str]] | None = None,
    *,
    documents_dir: Path | str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """
    Load policy Markdown files (unless ``documents`` is provided) and chunk them.
    """
    docs = (
        documents
        if documents is not None
        else load_markdown_documents(documents_dir)
    )
    all_chunks: list[TextChunk] = []
    for document_name, text in docs:
        all_chunks.extend(
            chunk_text(
                text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                document_name=document_name,
            )
        )
    return all_chunks
