"""
Educational demo: generate text embeddings with Ollama + compare similarity.

What is an embedding?
    An embedding turns text into a fixed-length list of floating-point numbers
    (a vector). Nearby vectors usually mean similar meaning.

What does a vector represent?
    Each dimension captures a latent feature the model learned (topic, intent,
    wording patterns, etc.). Humans do not read individual dimensions; we use
    distances/angles between whole vectors.

What do embedding dimensions mean?
    The dimension count is the vector length (e.g. 768). More dimensions can
    encode richer structure, but increase storage and compute cost.

Why similar sentences get similar embeddings?
    Embedding models are trained so paraphrases and related questions map to
    nearby points. "How can I return a product?" and "What is the refund
    procedure?" should score higher cosine similarity than an unrelated
    Python-install question.

This module is intentionally isolated from Phase 1 chat services and does not
implement RAG, LangChain, vector DBs, or document ingestion.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx

# Allow `python -m experiments.embeddings.embedding_demo` from project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
for _path in (str(_PROJECT_ROOT), str(_BACKEND_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from experiments.embeddings.similarity import SimilarityError, cosine_similarity

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_TIMEOUT_SECONDS = 60.0

DEMO_SENTENCES = [
    "How can I return a product?",
    "What is the product refund procedure?",
    "How do I install Python?",
]


class EmbeddingError(RuntimeError):
    """Raised when the Ollama embedding API fails."""


def get_ollama_base_url() -> str:
    """
    Read Ollama base URL from existing app settings when available,
    otherwise from OLLAMA_BASE_URL / a safe local default.
    """
    env_url = os.getenv("OLLAMA_BASE_URL")
    if env_url:
        return env_url.rstrip("/")

    try:
        from app.core.config import get_settings

        return get_settings().ollama_base_url.rstrip("/")
    except Exception:
        return "http://127.0.0.1:11434"


def get_embedding_model() -> str:
    """Embedding model name (overridable via EMBEDDING_MODEL)."""
    return os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def embed_texts(
    texts: list[str],
    *,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    client: httpx.Client | None = None,
) -> list[list[float]]:
    """
    Generate embeddings for each text via Ollama ``POST /api/embeddings``.

    Parameters
    ----------
    texts:
        Input sentences / paragraphs.
    model:
        Ollama embedding model (default: nomic-embed-text).
    base_url:
        Ollama server URL.
    timeout:
        HTTP timeout in seconds.
    client:
        Optional injected httpx client (useful for tests).
    """
    if not texts:
        return []

    model_name = model or get_embedding_model()
    url_base = (base_url or get_ollama_base_url()).rstrip("/")
    endpoint = f"{url_base}/api/embeddings"

    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout)
    embeddings: list[list[float]] = []

    try:
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise EmbeddingError("Each input text must be a non-empty string")

            payload = {"model": model_name, "prompt": text}
            try:
                response = http_client.post(endpoint, json=payload)
            except httpx.TimeoutException as exc:
                raise EmbeddingError(
                    f"Ollama embedding request timed out after {timeout}s"
                ) from exc
            except httpx.HTTPError as exc:
                raise EmbeddingError(
                    f"Failed to reach Ollama at {url_base}: {exc}"
                ) from exc

            if response.status_code >= 400:
                raise EmbeddingError(
                    f"Ollama embeddings HTTP {response.status_code}: "
                    f"{response.text[:400]}"
                )

            try:
                data: dict[str, Any] = response.json()
            except ValueError as exc:
                raise EmbeddingError("Ollama returned non-JSON embedding response") from exc

            vector = data.get("embedding")
            if not isinstance(vector, list) or not vector:
                raise EmbeddingError(
                    "Invalid Ollama embedding response: missing 'embedding' list"
                )
            if not all(isinstance(x, (int, float)) for x in vector):
                raise EmbeddingError(
                    "Invalid Ollama embedding response: non-numeric values"
                )

            embeddings.append([float(x) for x in vector])
    finally:
        if owns_client:
            http_client.close()

    return embeddings


def run_demo() -> None:
    """Fetch embeddings for the demo sentences and print similarity results."""
    model = get_embedding_model()
    base_url = get_ollama_base_url()
    print("=== Enterprise AI — Embeddings Experiment (Phase 2) ===")
    print(f"Ollama URL : {base_url}")
    print(f"Model      : {model}")
    print()

    try:
        vectors = embed_texts(DEMO_SENTENCES, model=model, base_url=base_url)
    except EmbeddingError as exc:
        print(f"ERROR: {exc}")
        print("Hint: run `ollama pull nomic-embed-text` and ensure Ollama is running.")
        raise SystemExit(1) from exc

    for sentence, vector in zip(DEMO_SENTENCES, vectors, strict=True):
        print(f"Sentence : {sentence}")
        print(f"Dimensions: {len(vector)}")
        print(f"Preview   : [{vector[0]:.6f}, {vector[1]:.6f}, ..., {vector[-1]:.6f}]")
        print()

    try:
        sim_12 = cosine_similarity(vectors[0], vectors[1])
        sim_13 = cosine_similarity(vectors[0], vectors[2])
    except SimilarityError as exc:
        print(f"ERROR computing similarity: {exc}")
        raise SystemExit(1) from exc

    print("--- Cosine similarity ---")
    print(f"Sentence 1 vs 2 (return vs refund): {sim_12:.6f}")
    print(f"Sentence 1 vs 3 (return vs Python): {sim_13:.6f}")
    print()
    print(
        "Expected pattern: similarity(1,2) should be higher than similarity(1,3) "
        "because return/refund are semantically closer than a Python install question."
    )


if __name__ == "__main__":
    run_demo()
