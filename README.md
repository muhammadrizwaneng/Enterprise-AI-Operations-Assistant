# Enterprise AI Operations Assistant

Local-first foundation for an enterprise AI operations assistant.

**Completed so far**

- Project structure, PostgreSQL schema, synthetic dataset, CSV exports, RAG policy docs (for later), FastAPI foundation, DB browser UI
- **Phase 1:** LLM integration with provider abstraction, Ollama support, chat API, and persistent conversation history

> RAG, LangChain/LangGraph, MCP, AI agents, Docker, and CI/CD are intentionally **not** included yet.

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
│   │   ├── api/           # HTTP routes (health, stats, db browser, chat)
│   │   ├── core/          # settings + logging
│   │   ├── db/            # engine, session, init
│   │   ├── models/        # SQLAlchemy models (ops data + conversations)
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── llm/       # provider abstraction (Ollama, OpenAI-compatible)
│   │   │   └── chat.py    # conversation orchestration
│   │   ├── templates/     # DB browser HTML
│   │   └── main.py
│   └── requirements.txt
├── dataset/
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
| GET | `/docs` | OpenAPI UI |

## Run tests

```bash
PYTHONPATH=backend:. pytest -q
```

LLM/chat tests **mock** the model provider — a running Ollama instance is not required for CI/local pytest.

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
