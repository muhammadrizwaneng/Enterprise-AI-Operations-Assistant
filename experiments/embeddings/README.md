# Embeddings Experiment (Phase 2)

Isolated experiments for **embeddings**, **cosine similarity**, **document chunking**, and **embedding ingestion** into PostgreSQL (`document_embeddings`).

**Phase 3 semantic search** (retrieve ranked chunks via the API) is implemented in the FastAPI app — see the root `README.md`. This experiment folder does **not** implement RAG or LLM answer generation.

## Concepts

| Term | Meaning |
|---|---|
| Embedding | Text converted into numbers (a vector) |
| Vector | Ordered list of floats |
| Dimensions | Length of a vector (**768** for `nomic-embed-text`) |
| Cosine similarity | How aligned two vectors are (higher ≈ closer meaning) |
| Chunking | Splitting a long document into smaller overlapping pieces |
| Chunk size | Max characters per chunk (default **500**) |
| Chunk overlap | Shared characters between adjacent chunks (default **100**) |
| Ingestion | Embed chunks and store them in `document_embeddings` |
| Semantic search | Embed a query and rank stored chunks with pgvector cosine distance (app API) |

### Why chunk before embeddings?

Embedding models work best on focused passages. Long policies are split so later retrieval can return the most relevant section instead of a whole file. Overlap keeps boundary sentences from being cut awkwardly.

### Embedding generation

`app.services.embedding_client.EmbeddingClient` calls Ollama `POST /api/embeddings` with the configured model (default `nomic-embed-text`). Every vector is validated to be exactly **768** dimensions. Within one client instance / ingestion run, identical chunk texts are cached so they are not re-embedded unnecessarily.

### Ingestion workflow

1. Load Markdown under `dataset/documents/` (read-only).
2. Chunk with `experiments.embeddings.chunking` (500 / 100 → **46** chunks expected).
3. Generate embeddings via `EmbeddingClient`.
4. `DocumentIngestionService` writes to PostgreSQL inside one transaction.

#### Default: incremental replace-by-document

With `purge_missing_documents=False` (the default used by `ingest_demo`):

- Only documents present in the incoming chunk batch are replaced (DELETE then INSERT).
- Documents stored in the DB but **absent from the batch** are left alone.
- An empty chunk batch is a no-op.
- `corpus_document_names` is ignored in this mode.

This makes re-runs safe for updated files and removes **stale chunk indexes** for those files when their content or chunk count changes.

#### Optional: full-corpus synchronization

When you need the DB to match the whole source corpus (including removals):

```python
service.ingest_chunks(
    chunks,
    purge_missing_documents=True,
    corpus_document_names=["support.md", "delivery.md"],  # every current file
)
```

In sync mode, within one transaction:

1. Delete embeddings for document names **not** in `corpus_document_names` (orphans).
2. Replace every corpus document (DELETE existing rows, then INSERT new chunks).
3. Commit once.

**Empty documents:** if a filename is listed in `corpus_document_names` but produced zero chunks, its old rows are still deleted (cleared). Do not omit empty files from the corpus list, or sync would treat them as removed.

**Safety restrictions (sync mode):**

- `corpus_document_names` is **required** and must be **non-empty**.
- Blank names, whitespace-padded names, and duplicates are rejected.
- Filenames must match the exact strings already stored (e.g. `privacy_policy.md`) — no path stripping.
- Invalid sync requests raise `DocumentIngestionError` and perform **zero** DB writes.
- Sync is **not** enabled by default in `ingest_demo`.

## Prerequisites

- Project virtualenv (`pip install -r backend/requirements.txt`)
- PostgreSQL with `pgvector` and the `document_embeddings` table
- Ollama running locally
- Embedding model pulled:

```bash
ollama pull nomic-embed-text
```

Configuration (see `.env` / `.env.example`):

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=768
EMBEDDING_TIMEOUT_SECONDS=60
```

## Files

| File | Purpose |
|---|---|
| `similarity.py` | Cosine similarity |
| `embedding_demo.py` | Educational Ollama embedding + similarity demo |
| `chunking.py` | Chunking + Markdown loader |
| `chunking_demo.py` | Runnable chunking experiment |
| `ingest_demo.py` | Chunk → embed → PostgreSQL ingestion |
| `backend/app/services/embedding_client.py` | Reusable Ollama embedding service |
| `backend/app/services/document_ingestion.py` | DB replace-by-document ingestion |

## Run chunking experiment (no Ollama / no DB)

```bash
source .venv/bin/activate
PYTHONPATH=backend:. python -m experiments.embeddings.chunking_demo
```

## Run embedding demo

```bash
brew services start ollama   # if needed
ollama pull nomic-embed-text

PYTHONPATH=backend:. python -m experiments.embeddings.embedding_demo
```

## Run document ingestion

```bash
source .venv/bin/activate
brew services start ollama   # if needed
ollama pull nomic-embed-text

PYTHONPATH=backend:. python -m experiments.embeddings.ingest_demo
```

Expected summary fields:

- Documents processed (6 Markdown policies)
- Total chunks generated (46 with defaults)
- Embeddings generated
- DB rows deleted / inserted (replacement strategy)
- DB rows purged (orphans; stays 0 unless sync is explicitly enabled)

### Verify database records

```sql
SELECT COUNT(*) FROM document_embeddings;                 -- expect 46 after a clean ingest
SELECT document_name, COUNT(*) AS chunks
FROM document_embeddings
GROUP BY document_name
ORDER BY document_name;

SELECT document_name, chunk_index, LEFT(chunk_text, 80) AS preview
FROM document_embeddings
ORDER BY document_name, chunk_index
LIMIT 20;
```

Business tables (`customers`, `orders`, …) are not touched by ingestion.

### Rerun ingestion safely

Re-run the same `ingest_demo` command at any time. Default mode replaces each document present in the batch only; it does **not** delete embeddings for files removed from the folder. To drop orphans, call the service with `purge_missing_documents=True` and an explicit full `corpus_document_names` list (see above). Policy Markdown files under `dataset/documents/` are never modified.

## Semantic search (after ingestion)

Ingestion must complete before searching. The app endpoint:

`POST /api/v1/search/semantic`

embeds the query with `EmbeddingClient` (`nomic-embed-text`, 768-d), then ranks rows with pgvector **cosine distance** (`<=>`). Similarity reported to clients is `1 - distance`. See the root `README.md` for request/response examples.

This is **retrieval only** — not RAG (no LLM answer synthesis).

## Tests

```bash
source .venv/bin/activate
PYTHONPATH=backend:. pytest -q \
  tests/test_embeddings_similarity.py \
  tests/test_embeddings_ollama.py \
  tests/test_embeddings_chunking.py \
  tests/test_embedding_client.py \
  tests/test_document_ingestion.py \
  tests/test_semantic_search.py \
  tests/test_search_api.py
```

Embedding / ingestion / semantic-search unit tests **mock** Ollama and the DB session. They do **not** require a running Ollama instance and do **not** write to the real `enterprise_ai` database.
