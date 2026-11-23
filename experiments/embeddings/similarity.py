"""
Cosine similarity helpers for embedding vectors.

Educational notes
-----------------
* An **embedding** is a list of numbers (a vector) that represents the meaning
  of a piece of text in a high-dimensional space.
* Each number in that vector is one **dimension**. Models such as
  ``nomic-embed-text`` often use hundreds or thousands of dimensions.
* **Cosine similarity** measures how aligned two vectors are (angle between
  them), ignoring length. Values near **1.0** mean similar direction/meaning;
  near **0.0** means unrelated; near **-1.0** means opposite direction.
* Semantically similar sentences tend to land near each other in embedding
  space, so their cosine similarity is usually higher than for unrelated text.
"""

from __future__ import annotations

import numpy as np


class SimilarityError(ValueError):
    """Raised when vectors cannot be compared."""


def cosine_similarity(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine(a, b) = (a · b) / (||a|| * ||b||)

    Raises
    ------
    SimilarityError
        If lengths differ, vectors are empty, or either vector has zero norm.
    """
    vec_a = np.asarray(a, dtype=np.float64).reshape(-1)
    vec_b = np.asarray(b, dtype=np.float64).reshape(-1)

    if vec_a.size == 0 or vec_b.size == 0:
        raise SimilarityError("Vectors must be non-empty")
    if vec_a.shape != vec_b.shape:
        raise SimilarityError(
            f"Vector length mismatch: {vec_a.shape[0]} vs {vec_b.shape[0]}"
        )
    if not np.all(np.isfinite(vec_a)) or not np.all(np.isfinite(vec_b)):
        raise SimilarityError("Vectors must contain only finite values")

    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise SimilarityError("Cannot compute cosine similarity for a zero vector")

    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
