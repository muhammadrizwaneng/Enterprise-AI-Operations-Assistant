# Embeddings Experiment (Phase 2 — educational)

Isolated experiment that shows how **text embeddings** and **cosine similarity** work using a local **Ollama** embedding model.

This does **not** implement RAG, LangChain, LangGraph, AI agents, or a vector database.

## Concepts

| Term | Meaning |
|---|---|
| Embedding | A numeric vector that represents the meaning of text |
| Vector | An ordered list of floats (one value per dimension) |
| Dimensions | Length of the vector (e.g. 768). More dims → richer encoding, more storage |
| Cosine similarity | Measures the angle between two vectors (`1` ≈ same direction/meaning) |

Semantically related sentences usually produce vectors pointing in similar directions, so their cosine similarity is higher.

## Prerequisites

- Project virtualenv already set up (`pip install -r backend/requirements.txt`)
- NumPy is already available in this project (pulled in by Pandas)
- httpx is already listed in `backend/requirements.txt`
- Ollama running locally

## Install / download the embedding model

```bash
# if Ollama is not running:
brew services start ollama   # or: ollama serve

ollama pull nomic-embed-text
```

## How to run

From the **project root**:

```bash
source .venv/bin/activate
PYTHONPATH=backend:. python -m experiments.embeddings.embedding_demo
```

Optional environment overrides (existing app config is used when possible):

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export EMBEDDING_MODEL=nomic-embed-text
```

`OLLAMA_BASE_URL` is also read from the existing Phase 1 settings (`.env` → `Settings.ollama_base_url`) when the env var is unset.

## Demo sentences

1. How can I return a product?
2. What is the product refund procedure?
3. How do I install Python?

## Expected output format

```text
=== Enterprise AI — Embeddings Experiment (Phase 2) ===
Ollama URL : http://127.0.0.1:11434
Model      : nomic-embed-text

Sentence : How can I return a product?
Dimensions: <N>
Preview   : [<f0>, <f1>, ..., <fN>]

Sentence : What is the product refund procedure?
Dimensions: <N>
Preview   : ...

Sentence : How do I install Python?
Dimensions: <N>
Preview   : ...

--- Cosine similarity ---
Sentence 1 vs 2 (return vs refund): 0.8xxxxx
Sentence 1 vs 3 (return vs Python): 0.4xxxxx

Expected pattern: similarity(1,2) should be higher than similarity(1,3) ...
```

Exact floats vary by model version, but **1↔2 should score higher than 1↔3**.

## Tests (no live Ollama required)

```bash
source .venv/bin/activate
PYTHONPATH=backend:. pytest -q tests/test_embeddings_similarity.py tests/test_embeddings_ollama.py
```

Unit tests mock HTTP responses and cover cosine edge cases (identical, orthogonal, zero/invalid vectors).
