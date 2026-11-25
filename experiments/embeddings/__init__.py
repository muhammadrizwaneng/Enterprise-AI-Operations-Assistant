"""Phase 2 educational embeddings experiment (no RAG / agents yet)."""

from experiments.embeddings.chunking import TextChunk, chunk_documents, chunk_text
from experiments.embeddings.similarity import cosine_similarity

__all__ = [
    "cosine_similarity",
    "chunk_text",
    "chunk_documents",
    "TextChunk",
]
