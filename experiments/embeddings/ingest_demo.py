"""
Document embedding ingestion experiment.

Flow:
1. Load six policy Markdown files (read-only).
2. Chunk with experiments.embeddings.chunking.
3. Embed with Ollama nomic-embed-text (768-d).
4. Replace rows in document_embeddings per document.

Does not implement semantic search or RAG.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
for _path in (str(_PROJECT_ROOT), str(_BACKEND_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.document_ingestion import (
    DocumentIngestionError,
    DocumentIngestionService,
)
from app.services.embedding_client import EmbeddingClient
from experiments.embeddings.chunking import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_DOCUMENTS_DIR,
    chunk_documents,
    load_markdown_documents,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_ingestion() -> int:
    print("=== Enterprise AI — Document Embedding Ingestion (Phase 2) ===")
    print(f"Documents : {DEFAULT_DOCUMENTS_DIR}")
    print(f"Chunking  : size={DEFAULT_CHUNK_SIZE}, overlap={DEFAULT_CHUNK_OVERLAP}")
    print()

    before_hashes = {
        p.name: _sha256(p) for p in sorted(DEFAULT_DOCUMENTS_DIR.glob("*.md"))
    }

    documents = load_markdown_documents()
    print(f"Documents processed (loaded): {len(documents)}")
    for name, text in documents:
        print(f"  - {name} ({len(text)} chars)")
    print()

    chunks = chunk_documents(
        documents,
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )
    print(f"Total chunks generated: {len(chunks)}")

    init_db()
    client = EmbeddingClient()
    print(f"Embedding model : {client.model}")
    print(f"Ollama URL      : {client.base_url}")
    print(f"Dimensions      : {client.dimensions}")
    print()

    with SessionLocal() as db:
        service = DocumentIngestionService(db, embedding_client=client)
        try:
            result = service.ingest_chunks(chunks)
        except DocumentIngestionError as exc:
            print(f"ERROR: {exc}")
            return 1

        stored = service.count_stored_embeddings()

    print("--- Ingestion summary ---")
    print(f"Documents processed     : {result.documents_processed}")
    print(f"Document names          : {', '.join(result.document_names)}")
    print(f"Total chunks generated  : {result.chunks_received}")
    print(f"Embeddings generated    : {result.embeddings_generated}")
    print(f"DB rows deleted         : {result.rows_deleted}")
    print(f"DB rows purged (orphans): {result.rows_purged}")
    if result.purged_document_names:
        print(f"Purged documents        : {', '.join(result.purged_document_names)}")
    print(f"DB rows inserted/updated: {result.rows_inserted}")
    print(f"Rows now in table       : {stored}")
    print()
    # Full-corpus sync (purge_missing_documents=True) is opt-in via the service
    # API and is intentionally not enabled by this demo.


    after_hashes = {
        p.name: _sha256(p) for p in sorted(DEFAULT_DOCUMENTS_DIR.glob("*.md"))
    }
    print(f"Original policy files unchanged: {before_hashes == after_hashes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_ingestion())
