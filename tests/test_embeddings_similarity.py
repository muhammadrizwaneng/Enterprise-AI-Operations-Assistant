"""Unit tests for cosine similarity (no Ollama required)."""

from __future__ import annotations

import math

import pytest

from experiments.embeddings.similarity import SimilarityError, cosine_similarity


def test_identical_vectors_similarity_is_one():
    vector = [1.0, 2.0, 3.0]
    assert cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_orthogonal_vectors_similarity_is_zero():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_opposite_vectors_similarity_is_minus_one():
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(-1.0)


def test_known_angle_similarity():
    # 45 degrees between [1,0] and [1,1] => cos(45°)=1/sqrt(2)
    a = [1.0, 0.0]
    b = [1.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(1 / math.sqrt(2))


def test_zero_vector_raises():
    with pytest.raises(SimilarityError, match="zero vector"):
        cosine_similarity([0.0, 0.0], [1.0, 2.0])


def test_empty_vector_raises():
    with pytest.raises(SimilarityError, match="non-empty"):
        cosine_similarity([], [1.0])


def test_length_mismatch_raises():
    with pytest.raises(SimilarityError, match="mismatch"):
        cosine_similarity([1.0, 2.0], [1.0])


def test_non_finite_values_raise():
    with pytest.raises(SimilarityError, match="finite"):
        cosine_similarity([1.0, float("nan")], [1.0, 2.0])
