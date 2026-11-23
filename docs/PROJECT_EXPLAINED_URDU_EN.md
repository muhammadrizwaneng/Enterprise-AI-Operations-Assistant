# Project Explained — File by File, Line by Line

**Audience:** beginner-friendly (English + simple Roman Urdu)  
**Project:** Enterprise AI Operations Assistant  

Ye file batati hai: **kon si folder / file kya kaam karti hai**, aur important files me **har line / har block kya karta hai**.

> Tip: pehle project map padho, phir Phase 2 embeddings (line-by-line), phir Phase 1 chat.

---

## 0) Simple picture (poora project kya hai?)

```text
Browser / curl
    │
    ▼
FastAPI (backend/app/main.py)     ← API server
    │
    ├── /health, /db, /api/v1/stats   ← normal API + DB browser
    ├── /api/v1/chat                  ← Phase 1: LLM chat (Ollama)
    └── PostgreSQL                    ← customers, orders, + chat history

experiments/embeddings/               ← Phase 2: learning only (RAG nahi)
    └── text → embedding numbers → cosine similarity
```

**Roman Urdu:**  
Server = FastAPI. Data = PostgreSQL. Chat = Ollama LLM. Embeddings experiment = alag classroom jahan hum vectors seekhte hain; abhi RAG nahi.

---

## 1) Folder map — har folder ka kaam

| Folder / File | Kya karti hai? |
|---|---|
| `backend/` | Asal application code (API, DB, LLM) |
| `backend/app/` | Python package `app` |
| `backend/app/api/` | HTTP routes (URLs) |
| `backend/app/core/` | Settings + logging |
| `backend/app/db/` | Database engine / session / create tables |
| `backend/app/models/` | SQLAlchemy tables (ORM) |
| `backend/app/schemas/` | Pydantic request/response shapes |
| `backend/app/services/` | Business logic (chat, stats, LLM providers) |
| `backend/app/templates/` | DB browser HTML pages |
| `backend/requirements.txt` | Python libraries list |
| `dataset/` | Fake company data generators + CSV + policy docs |
| `dataset/csv/` | Exported table CSVs |
| `dataset/documents/` | Future RAG policy markdown files |
| `experiments/` | Educational experiments (Phase 2) |
| `experiments/embeddings/` | Embedding + similarity demo |
| `tests/` | Automated tests |
| `qa/` | Audit reports |
| `docs/` | Guides (ye file yahan hai) |
| `.env` | Local secrets/config (git me commit mat karo) |
| `.env.example` | Safe template of config keys |
| `README.md` | How to install/run |

---

## 2) Config files — line meaning

### `.env` / `.env.example`

| Line / key | Meaning |
|---|---|
| `DATABASE_URL=...` | PostgreSQL connection string |
| `APP_NAME=...` | App display name |
| `APP_ENV=development` | Environment label |
| `DEBUG=true` | Debug mode flag |
| `DATASET_SEED=42` | Fake data always same numbers |
| `LLM_PROVIDER=ollama` | Which LLM backend |
| `LLM_MODEL=llama3.2` | Chat model name |
| `LLM_TEMPERATURE=0.7` | Creativity vs focused answers |
| `LLM_TIMEOUT_SECONDS=60` | Max wait for model |
| `LLM_MAX_HISTORY_MESSAGES=20` | Kitni purani messages LLM ko bhejni hain |
| `LLM_SYSTEM_PROMPT=...` | Assistant ka “role / rules” |
| `OLLAMA_BASE_URL=http://127.0.0.1:11434` | Local Ollama server |
| `OPENAI_API_KEY=` | Future cloud key (empty = unused) |
| `OPENAI_BASE_URL=...` | Future OpenAI-compatible API |
| `ANTHROPIC_API_KEY=` | Future (not wired yet) |

**Roman Urdu:** `.env` = tumhari machine ki settings. Code me password hardcode nahi; yahan se read hota hai.

---

## 3) Phase 2 — Embeddings experiment (FULL line-by-line)

Yahan har important line explain hai. Pehle ye padho — short files hain.

---

### 3.1 `experiments/embeddings/__init__.py`

| Line | Code | Explanation |
|---:|---|---|
| 1 | docstring | Package ka short intro: Phase 2 education, RAG nahi |
| 3 | `from ... import cosine_similarity` | Similarity function ko bahar se easily import karne do |
| 5 | `__all__ = [...]` | Batata hai package publicly kya export karta hai |

**File ka kaam:** chhota “door” — `from experiments.embeddings import cosine_similarity`

---

### 3.2 `experiments/embeddings/similarity.py` (har line)

| Line | Kya karti hai? |
|---:|---|
| 1–15 | Docstring: embedding / dimension / cosine kya hain (education) |
| 17 | `from __future__ import annotations` — modern type hints allow |
| 19 | `import numpy as np` — math library for vectors |
| 22–23 | `SimilarityError` class — jab compare na ho sake to clear error |
| 26 | Function start: `cosine_similarity(a, b)` |
| 27–36 | Function docstring: formula + kab error aayegi |
| 37 | `vec_a = np.asarray(...).reshape(-1)` — list ko 1D NumPy array banao |
| 38 | same for `vec_b` |
| 40–41 | empty vector? error |
| 42–45 | length different? error (768 vs 10 compare nahi) |
| 46–47 | NaN/inf values? error |
| 49–50 | `norm` = vector ki length (magnitude) |
| 51–52 | zero vector? cosine divide-by-zero avoid → error |
| 54 | **main math:** dot(a,b) / (‖a‖‖b‖) → similarity float return |

**Roman Urdu samajh:**  
Do sentences ke number-lists (vectors) ka angle check karna.  
1 ke qareeb = meaning similar. 0 ke qareeb = alag topic.

Formula:

```text
cosine = (a · b) / (|a| * |b|)
```

---

### 3.3 `experiments/embeddings/embedding_demo.py` (block + line)

#### Lines 1–25 — docstring (education)
Batata hai: embedding kya hai, vector kya hai, dimensions, aur similar sentences kyun milti embeddings banati hain.

#### Lines 27–34 — imports
| Line | Meaning |
|---:|---|
| 27 | future annotations |
| 29 | `os` — environment variables read |
| 30 | `sys` — Python import path change |
| 31 | `Path` — file/folder paths |
| 32 | `Any` — typing helper |
| 34 | `httpx` — HTTP client (Ollama ko call) |

#### Lines 36–41 — path setup
| Line | Meaning |
|---:|---|
| 37 | project root folder find karo (`.../Enterprise AI Operations Assistant`) |
| 38 | backend folder path |
| 39–41 | `sys.path` me root + backend add — taake `app` aur `experiments` import hon |

#### Lines 43–52 — imports + constants
| Line | Meaning |
|---:|---|
| 43 | similarity helpers import |
| 45 | default model name `nomic-embed-text` |
| 46 | default timeout 60 sec |
| 48–52 | 3 demo sentences list |

#### Lines 55–56 — `EmbeddingError`
Ollama fail ho to ye custom error use hoti hai.

#### Lines 59–73 — `get_ollama_base_url()`
| Line | Meaning |
|---:|---|
| 64 | pehle env `OLLAMA_BASE_URL` check |
| 65–66 | mil gaya to use (trailing `/` hatao) |
| 68–71 | warna Phase 1 `Settings.ollama_base_url` try karo |
| 72–73 | wo bhi fail → localhost default |

#### Lines 76–78 — `get_embedding_model()`
Env `EMBEDDING_MODEL` ya default `nomic-embed-text`.

#### Lines 81–159 — `embed_texts(...)` (asal embedding worker)

| Line | Meaning |
|---:|---|
| 81–88 | function signature: texts list, optional model/url/timeout/client |
| 89–104 | docstring |
| 105–106 | empty input → empty output |
| 108 | model decide |
| 109 | base URL decide |
| 110 | full endpoint: `/api/embeddings` |
| 112 | kya humne client khud banaya? (close karna hoga) |
| 113 | httpx client banao ya injected client use karo (tests) |
| 114 | results list |
| 116 | `try` block start |
| 117 | har sentence pe loop |
| 118–119 | blank text reject |
| 121 | JSON body for Ollama: model + prompt |
| 122–123 | POST request |
| 124–127 | timeout → EmbeddingError |
| 128–131 | connection fail → EmbeddingError |
| 133–137 | HTTP 400+ → error with body snippet |
| 139–142 | response JSON parse |
| 144 | `embedding` field nikaalo |
| 145–148 | missing/empty list? error |
| 149–152 | non-number values? error |
| 154 | clean float list append |
| 155–157 | `finally`: agar humne client banaya tha to close |
| 159 | saari embeddings return |

**Roman Urdu:**  
Har sentence Ollama ko bhejte ho → Ollama 768 numbers wapas deta hai → list me store.

#### Lines 162–198 — `run_demo()`
| Line | Meaning |
|---:|---|
| 164–168 | model/url print header |
| 171–176 | embed_texts call; fail → hint + exit |
| 178–182 | har sentence: text, dimensions, preview print |
| 184–189 | cosine(1,2) aur cosine(1,3) |
| 191–198 | results + expected pattern explain |

#### Lines 201–202 — script entry
Agar file directly run ho (`python -m ...`) to `run_demo()` chalao.

---

### 3.4 `experiments/embeddings/README.md`
Documentation only (install, pull model, run command, expected output). Code nahi.

---

## 4) Phase 1 — LLM files (file ka kaam + important lines)

### 4.1 `backend/app/services/llm/base.py`

**File ka kaam:** LLM ka “contract / interface”. Business code isi se baat kare, Ollama/OpenAI se seedha nahi.

| Lines | Meaning |
|---:|---|
| 3 | future annotations |
| 5–7 | ABC, dataclass, typing imports |
| 9 | `Role` = sirf system/user/assistant |
| 12–17 | `ChatMessage` — ek message (role + content) |
| 20–29 | `LLMResponse` — model ka jawab + metadata |
| 32–37 | `LLMError` — error + optional HTTP status |
| 40–63 | `LLMProvider` abstract class: `chat()` + `healthcheck()` must implement |

**Roman Urdu:** ye “plug socket” hai. Ollama ek plug hai, OpenAI dusra. Socket same rehta hai.

---

### 4.2 `backend/app/services/llm/ollama.py`

**File ka kaam:** Local Ollama chat API call (`POST /api/chat`).

Important flow:
1. settings se model/temperature/timeout lo  
2. messages JSON banao  
3. httpx POST  
4. timeout → 504, connection → 503, bad response → 502  
5. `LLMResponse` return  

---

### 4.3 `backend/app/services/llm/openai_compatible.py`

**File ka kaam:** Future cloud provider (OpenAI-compatible). Key env se aati hai. Default nahi.

---

### 4.4 `backend/app/services/llm/factory.py`

**File ka kaam:** `LLM_PROVIDER` padho → sahi class banao (`ollama` ya `openai`).

| Idea | Meaning |
|---|---|
| `build_llm_provider()` | naya provider object |
| `get_llm_provider()` | cached singleton |
| `clear_llm_provider_cache()` | tests / reload |

---

### 4.5 `backend/app/services/chat.py`

**File ka kaam:** Chat ka dimaag.

Steps:
1. conversation create/load  
2. user message DB me save  
3. history + system prompt build  
4. provider.chat()  
5. assistant message save  
6. response return  
Fail → rollback (adhoora data save na ho)

---

### 4.6 `backend/app/api/chat.py` (line-by-line)

| Line | Meaning |
|---:|---|
| 1 | file docstring |
| 3 | future annotations |
| 5 | UUID type |
| 7–8 | FastAPI + SQLAlchemy session |
| 10–14 | logger, DB dep, schemas, service, LLMError |
| 16 | router prefix `/api/v1` |
| 17 | logger |
| 20–34 | `POST /chat` — request lo, ChatService chalao, LLMError → HTTP error |
| 37–47 | `GET /conversations/{id}` — history fetch, missing → 404 |

---

### 4.7 `backend/app/models/conversation.py`

**File ka kaam:** PostgreSQL tables for chat history.

- `conversations`: id, title, timestamps  
- `messages`: id, conversation_id, role, content, model, provider, created_at  

---

### 4.8 `backend/app/schemas/chat.py`

**File ka kaam:** Request/response validation.

- `ChatRequest`: message required, optional conversation_id  
- `ChatResponse`: reply + ids + model/provider  

Galat input pe FastAPI automatically **422** deta hai.

---

### 4.9 `backend/app/main.py` (line-by-line)

| Line | Meaning |
|---:|---|
| 1 | docstring |
| 3 | lifespan helper import |
| 5–6 | FastAPI + RedirectResponse |
| 8–13 | routers, settings, logging, init_db |
| 15–16 | settings load + logging on |
| 19–23 | startup pe tables create (`conversations` etc.) |
| 26–34 | FastAPI app object |
| 36–38 | routers attach |
| 41–50 | `GET /` welcome JSON |
| 53–56 | `/admin/db` → `/db` redirect |

---

### 4.10 `backend/app/core/config.py`

**File ka kaam:** saari settings `.env` se load.

`get_settings()` cached Settings object return karta hai.

---

### 4.11 `backend/app/core/logging.py`

**File ka kaam:** logs format set (time, level, message).

---

## 5) Database / dataset files (short)

| File | Kaam |
|---|---|
| `backend/app/db/base.py` | SQLAlchemy Base class |
| `backend/app/db/session.py` | engine + `get_db()` dependency |
| `backend/app/db/init_db.py` | `create_all()` tables |
| `backend/app/models/*.py` | roles, users, customers, products, orders, payments, tickets |
| `dataset/generators/generate.py` | fake consistent data (seed 42) |
| `dataset/generators/export_csv.py` | CSV likho |
| `dataset/seed_database.py` | DB me insert (idempotent) |
| `dataset/documents/*.md` | future RAG policies (abhi use nahi in chat) |

**Roman Urdu:** Phase 0 data = company ka fake ERP. Phase 1 chat us data ko abhi directly query nahi karta (RAG baad me).

---

## 6) API / UI extras

| File | Kaam |
|---|---|
| `backend/app/api/routes.py` | `/health`, `/api/v1/database/stats` |
| `backend/app/api/db_browser.py` | `/db` HTML table browser |
| `backend/app/services/stats.py` | table counts |
| `backend/app/services/db_browser.py` | safe table row fetch |
| `backend/app/templates/db/*.html` | browser GUI pages |

---

## 7) Tests — har test file kya check karti hai

| File | Checks |
|---|---|
| `tests/test_models.py` | table/FK metadata |
| `tests/test_dataset.py` | fake data consistency |
| `tests/test_api.py` | `/`, `/health`, stats |
| `tests/test_llm.py` | provider factory + mocked Ollama |
| `tests/test_chat.py` | chat + history (mocked LLM) |
| `tests/test_embeddings_similarity.py` | cosine edge cases |
| `tests/test_embeddings_ollama.py` | embedding HTTP mocked |

---

## 8) Request journey examples

### A) Chat (Phase 1)

```text
curl POST /api/v1/chat {"message":"Hello"}
  → api/chat.py
  → services/chat.py
  → save user message (Postgres)
  → llm/factory → ollama.py
  → Ollama llama3.2
  → save assistant message
  → JSON reply back
```

### B) Embeddings demo (Phase 2)

```text
python -m experiments.embeddings.embedding_demo
  → embed_texts()
  → Ollama nomic-embed-text (/api/embeddings)
  → 768 floats per sentence
  → cosine_similarity(1,2) and (1,3)
  → print scores
```

---

## 9) Quick glossary (yaad rakhne wali words)

| Word | Simple meaning |
|---|---|
| API | URL jahan program baat karta hai |
| Endpoint | ek specific URL + method (GET/POST) |
| Schema | request/response ka shape (Pydantic) |
| Model (DB) | database table class |
| Model (LLM) | AI brain weights (llama3.2) |
| Provider | kaun AI server (Ollama/OpenAI) |
| Embedding | text → numbers |
| Vector | numbers ki list |
| Cosine similarity | do vectors kitne similar direction me hain |
| RAG | baad ki phase: docs retrieve karke LLM ko context dena (abhi nahi) |

---

## 10) Recommended reading order (tumhari learning path)

1. Ye guide (section 0–1)  
2. `experiments/embeddings/similarity.py` line-by-line  
3. `experiments/embeddings/embedding_demo.py` line-by-line  
4. `backend/app/services/llm/base.py`  
5. `backend/app/api/chat.py` + `services/chat.py`  
6. `backend/app/main.py`  
7. `dataset/generators/generate.py` (optional deep dive)

---

## 11) Commands (yaad ke liye)

```bash
# API
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --port 8000

# Embeddings demo
PYTHONPATH=backend:. python -m experiments.embeddings.embedding_demo

# Tests
PYTHONPATH=backend:. pytest -q
```

---

**Short Roman Urdu summary:**  
- `backend/` = asal product  
- `dataset/` = fake company data  
- `experiments/embeddings/` = vectors seekhne ka lab  
- `tests/` = auto-check  
- Chat = words in/out via LLM  
- Embeddings = words → numbers → similarity score  

Agar tum chaho to next message me main **sirf ek file** (jo tum bolo) ko aur bhi zyada detail me, bilkul first line se last line tak whiteboard style samjha sakta hoon.
