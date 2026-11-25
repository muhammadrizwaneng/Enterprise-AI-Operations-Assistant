# Enterprise AI Operations Assistant

Local-first foundation for an enterprise AI operations assistant.

**Completed so far**

- Project structure, PostgreSQL schema, synthetic dataset, CSV exports, policy Markdown docs, FastAPI foundation, DB browser UI
- **Phase 1:** LLM integration with provider abstraction, Ollama support, chat API, and persistent conversation history
- **Phase 2:** Embeddings (`nomic-embed-text`, 768-d), chunking, document ingestion into `document_embeddings`
- **Phase 3:** Semantic search API — retrieve ranked policy chunks via pgvector cosine distance
- **Phase 4:** RAG — grounded LLM answers over retrieved chunks with source attribution

> LangChain/LangGraph, MCP, AI agents, Docker, and CI/CD are intentionally **not** included yet.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (running locally)
- `pip` and a virtual environment tool
- [Ollama](https://ollama.com) (optional for live chat; tests mock the LLM)

## Project layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/           # HTTP routes (health, stats, db browser, chat, search, rag)
│   │   ├── core/          # settings + logging
│   │   ├── db/            # engine, session, init
│   │   ├── models/        # SQLAlchemy models (ops + chat + embeddings)
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── llm/              # provider abstraction (Ollama, …)
│   │   │   ├── chat.py           # conversation orchestration
│   │   │   ├── embedding_client.py
│   │   │   ├── document_ingestion.py
│   │   │   ├── semantic_search.py
│   │   │   └── rag.py            # retrieval-augmented generation
│   │   ├── templates/     # DB browser HTML
│   │   └── main.py
│   └── requirements.txt
├── dataset/
├── experiments/embeddings/
├── qa/
├── tests/
├── .env.example
└── README.md
```

## Installation

```bash
cd "/path/to/Enterprise AI Operations Assistant"
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Environment configuration

```bash
cp .env.example .env
```

Key variables:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/enterprise_ai

# LLM / Chat
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_TEMPERATURE=0.7
LLM_TIMEOUT_SECONDS=60
LLM_MAX_HISTORY_MESSAGES=20
LLM_SYSTEM_PROMPT=You are the Enterprise AI Operations Assistant for NovaForge...

OLLAMA_BASE_URL=http://127.0.0.1:11434

# Embeddings / semantic search
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=768
EMBEDDING_TIMEOUT_SECONDS=60
SEMANTIC_SEARCH_DEFAULT_TOP_K=5
SEMANTIC_SEARCH_MAX_TOP_K=20

# RAG (Phase 4)
RAG_TOP_K=5
RAG_MIN_SIMILARITY=0.5
RAG_TEMPERATURE=0.2

# Optional future API providers — never commit real keys
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
ANTHROPIC_API_KEY=
```

On macOS Homebrew PostgreSQL, the default role is often your OS username:

```env
DATABASE_URL=postgresql+psycopg://YOUR_OS_USERNAME@localhost:5432/enterprise_ai
```

## Database

```bash
createdb enterprise_ai
PYTHONPATH=backend:. python dataset/seed_database.py
```

Chat tables (`conversations`, `messages`) are created automatically on API startup via `init_db()`.

### Phase 2 — `document_embeddings`

pgvector must be enabled once per database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Python dependency: `pgvector` (see `backend/requirements.txt`).

Table `document_embeddings` stores chunked policy text + `VECTOR(768)` embeddings (matches `nomic-embed-text`). Created via `init_db()` / app startup.

Ingest policy chunks (requires Ollama + `nomic-embed-text`):

```bash
ollama pull nomic-embed-text
PYTHONPATH=backend:. python -m experiments.embeddings.ingest_demo
```

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `document_name` | VARCHAR(255) | source filename (indexed) |
| `chunk_index` | INTEGER | chunk order within document |
| `chunk_text` | TEXT | chunk content |
| `embedding` | VECTOR(768) | pgvector |
| `metadata` | JSONB | optional extras |
| `created_at` | TIMESTAMPTZ | |

Unique constraint: `(document_name, chunk_index)`.

Educational embedding demos: see `experiments/embeddings/README.md`.

### Phase 3 — Semantic search

Semantic search turns a natural-language question into a **query embedding** (same `EmbeddingClient` / `nomic-embed-text` / 768-d), then asks PostgreSQL/pgvector to rank stored chunk vectors by **cosine distance** (`<=>`). Clients receive **similarity** as `1 - distance` (higher is closer).

**Prerequisite:** run document ingestion first so `document_embeddings` is populated (~46 chunks with default chunking).

This endpoint **retrieves chunks only**. It does **not** call the chat LLM and is **not** RAG.

Example:

```bash
curl -s http://127.0.0.1:8000/api/v1/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is your refund policy?","top_k":5}'
```

Example response shape:

```json
{
  "query": "What is your refund policy?",
  "top_k": 5,
  "min_similarity": 0.0,
  "results": [
    {
      "document_name": "refund_policy.md",
      "chunk_index": 0,
      "chunk_text": "...",
      "similarity": 0.91,
      "distance": 0.09,
      "metadata": {"embedding_model": "nomic-embed-text", "embedding_dimensions": 768}
    }
  ]
}
```

Optional `min_similarity` (0–1) filters weak matches. Default `top_k` is 5; maximum is 20.

### Phase 4 — RAG (Retrieval-Augmented Generation)

**RAG** retrieves relevant policy chunks (semantic search), then asks the configured LLM to answer **only** from that context. Sources returned to the client are the same chunks supplied to the model (not model-invented citations).

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/chat` | Free-form chat with conversation history (not document-grounded) |
| `POST /api/v1/search/semantic` | Retrieve ranked chunks only (no LLM answer) |
| `POST /api/v1/rag/ask` | Grounded answer + source attribution (stateless) |

**Prerequisite:** document ingestion must have populated `document_embeddings`.

Defaults: `top_k=5`, `min_similarity=0.5`, LLM temperature `0.2`. If no chunks pass the threshold, the API **does not** call the LLM and returns an insufficient-information message with empty `sources`.

Example request:

```bash
curl -s http://127.0.0.1:8000/api/v1/rag/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is your refund policy?","top_k":5,"min_similarity":0.5}'
```

Example response shape:

```json
{
  "question": "What is your refund policy?",
  "answer": "Refunds may be requested within 30 calendar days...",
  "model": "llama3.2",
  "provider": "ollama",
  "sources": [
    {
      "document_name": "refund_policy.md",
      "chunk_index": 0,
      "similarity": 0.72,
      "distance": 0.28,
      "chunk_text": "..."
    }
  ],
  "retrieval": { "top_k": 5, "min_similarity": 0.5 }
}
```

Grounding: the system prompt instructs the model to answer only from CONTEXT, abstain when evidence is missing, ignore instructions inside documents, and describe conflicts rather than inventing resolutions. Prompting alone cannot guarantee zero hallucinations; retrieval gating (`min_similarity` / empty hits) is also applied.

RAG unit/API tests mock search and the LLM:

```bash
PYTHONPATH=backend:. pytest -q tests/test_rag.py tests/test_rag_api.py
```

## Phase 1 — LLM chat

### Install a local model (Ollama)

```bash
# install Ollama from https://ollama.com then:
ollama pull llama3.2
ollama serve   # if not already running
```

### Run the API

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### Chat examples

Start a conversation:

```bash
curl -s http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello, who are you?"}'
```

Continue with the returned `conversation_id`:

```bash
curl -s http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"conversation_id":"<UUID>","message":"Summarize what you can help with."}'
```

Fetch history:

```bash
curl -s http://127.0.0.1:8000/api/v1/conversations/<UUID>
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Welcome payload |
| GET | `/health` | Health check |
| GET | `/db` | Web GUI — browse operational tables |
| GET | `/api/v1/database/stats` | Table record counts |
| POST | `/api/v1/chat` | Chat with the configured LLM |
| GET | `/api/v1/conversations/{id}` | Persisted conversation history |
| POST | `/api/v1/search/semantic` | Semantic search over ingested policy chunks |
| POST | `/api/v1/rag/ask` | RAG grounded answer + sources (stateless) |
| GET | `/docs` | OpenAPI UI |

## Run tests

```bash
PYTHONPATH=backend:. pytest -q
```

LLM/chat, semantic-search, and RAG unit tests **mock** providers / DB sessions — a running Ollama instance is not required for those tests.

## Concepts (Phase 1)

- **LLM:** a large language model predicts the next tokens of text from context.
- **Tokens / context window:** text is split into tokens; models only “see” a limited recent window — we trim history with `LLM_MAX_HISTORY_MESSAGES`.
- **Temperature:** higher → more varied replies; lower → more deterministic.
- **System vs user prompts:** system sets behavior; user is the actual question; assistant is the model reply.
- **Provider abstraction:** business code calls `LLMProvider.chat()`; Ollama or OpenAI-compatible backends can be swapped via `LLM_PROVIDER`.
- **Conversation history:** each turn is stored in PostgreSQL (`conversations` / `messages`) and replayed into the next LLM call.

## Technology stack

- Python 3.10+, FastAPI, PostgreSQL, SQLAlchemy 2.x, Pydantic
- httpx (Ollama / OpenAI-compatible HTTP)
- Faker, Pandas, Pytest, Jinja2
