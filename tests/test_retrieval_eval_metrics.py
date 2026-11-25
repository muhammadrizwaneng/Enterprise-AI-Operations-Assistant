"""Unit tests for retrieval evaluation metrics (no live API required)."""

from __future__ import annotations

import pytest

from experiments.retrieval_eval.dataset import (
    EVAL_QUERIES,
    ChunkRef,
    EvalQuery,
    get_eval_queries,
)
from experiments.retrieval_eval.metrics import (
    RetrievedChunk,
    evaluate_query,
    evaluate_run,
    first_relevant_rank,
    missing_relevant_chunks,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    source_coverage,
)


def _hit(doc: str, index: int, sim: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(document_name=doc, chunk_index=index, similarity=sim)


def _query(
    *chunks: tuple[str, int],
    query_id: str = "T1",
) -> EvalQuery:
    return EvalQuery(
        query_id=query_id,
        question="test question",
        primary_relevant=tuple(
            ChunkRef(document_name=d, chunk_index=i) for d, i in chunks
        ),
    )


def test_recall_at_k_partial_and_full():
    relevant = {("a.md", 1), ("a.md", 2)}
    retrieved = [_hit("a.md", 1), _hit("b.md", 0), _hit("a.md", 2)]
    assert recall_at_k(relevant, retrieved, 1) == pytest.approx(0.5)
    assert recall_at_k(relevant, retrieved, 3) == pytest.approx(1.0)


def test_recall_at_k_empty_retrieval():
    relevant = {("a.md", 1)}
    assert recall_at_k(relevant, [], 5) == pytest.approx(0.0)


def test_recall_rejects_empty_ground_truth():
    with pytest.raises(ValueError, match="relevant set must not be empty"):
        recall_at_k(set(), [_hit("a.md", 1)], 5)


def test_precision_at_k():
    relevant = {("a.md", 1), ("a.md", 2)}
    retrieved = [_hit("a.md", 1), _hit("b.md", 0), _hit("c.md", 0)]
    # 1 relevant in top-5 denominator 5
    assert precision_at_k(relevant, retrieved, 5) == pytest.approx(0.2)
    assert precision_at_k(relevant, [], 5) == pytest.approx(0.0)


def test_precision_rejects_empty_ground_truth():
    with pytest.raises(ValueError, match="relevant set must not be empty"):
        precision_at_k(set(), [_hit("a.md", 1)], 5)


def test_mrr_first_hit_and_miss():
    relevant = {("a.md", 2)}
    retrieved = [_hit("b.md", 0), _hit("a.md", 2)]
    assert reciprocal_rank(relevant, retrieved) == pytest.approx(0.5)
    assert reciprocal_rank(relevant, [_hit("b.md", 0)]) == pytest.approx(0.0)
    assert first_relevant_rank(relevant, retrieved) == 2
    assert first_relevant_rank(relevant, [_hit("b.md", 0)]) is None


def test_mrr_rejects_empty_ground_truth():
    with pytest.raises(ValueError, match="relevant set must not be empty"):
        reciprocal_rank(set(), [_hit("a.md", 1)])


def test_source_coverage():
    assert source_coverage([True, False, True]) == pytest.approx(2 / 3)
    with pytest.raises(ValueError, match="hits list must not be empty"):
        source_coverage([])


def test_missing_relevant_chunks():
    relevant = {("a.md", 1), ("a.md", 2), ("b.md", 3)}
    retrieved = [_hit("a.md", 1), _hit("x.md", 0)]
    missing = missing_relevant_chunks(relevant, retrieved, k=5)
    assert [c.label() for c in missing] == ["a.md#2", "b.md#3"]


def test_duplicate_retrieved_chunks_counted_once():
    relevant = {("a.md", 1)}
    retrieved = [_hit("a.md", 1, 0.9), _hit("a.md", 1, 0.8), _hit("b.md", 0)]
    assert recall_at_k(relevant, retrieved, 2) == pytest.approx(1.0)
    assert precision_at_k(relevant, retrieved, 2) == pytest.approx(0.5)
    assert reciprocal_rank(relevant, retrieved) == pytest.approx(1.0)


def test_evaluate_query_top_k_five_skips_recall_at_10():
    query = _query(("delivery_policy.md", 1), ("delivery_policy.md", 2))
    retrieved = [
        _hit("delivery_policy.md", 6),
        _hit("delivery_policy.md", 1),
        _hit("delivery_policy.md", 0),
    ]
    metrics = evaluate_query(query, retrieved, retrieval_top_k=5)
    assert metrics.recall_at_5 == pytest.approx(0.5)
    assert metrics.recall_at_10 is None
    assert metrics.precision_at_5 == pytest.approx(0.2)
    assert metrics.mrr == pytest.approx(0.5)
    assert metrics.missing_relevant == ["delivery_policy.md#2"]
    assert metrics.source_hit is True


def test_evaluate_query_top_k_ten_computes_recall_at_10():
    query = _query(("delivery_policy.md", 1), ("delivery_policy.md", 2))
    retrieved = [
        _hit("delivery_policy.md", 6),
        _hit("delivery_policy.md", 4),
        _hit("delivery_policy.md", 1),
        _hit("delivery_policy.md", 0),
        _hit("delivery_policy.md", 5),
        _hit("delivery_policy.md", 3),
        _hit("delivery_policy.md", 2),
    ]
    metrics = evaluate_query(query, retrieved, retrieval_top_k=10)
    assert metrics.recall_at_5 == pytest.approx(0.5)
    assert metrics.recall_at_10 == pytest.approx(1.0)
    assert metrics.first_relevant_rank == 3


def test_evaluate_query_empty_retrieval():
    query = _query(("a.md", 1))
    metrics = evaluate_query(query, [], retrieval_top_k=5)
    assert metrics.result_count == 0
    assert metrics.recall_at_5 == pytest.approx(0.0)
    assert metrics.precision_at_5 == pytest.approx(0.0)
    assert metrics.mrr == pytest.approx(0.0)
    assert metrics.first_relevant_rank is None
    assert metrics.missing_relevant == ["a.md#1"]
    assert metrics.source_hit is False


def test_evaluate_query_error_does_not_score():
    query = _query(("a.md", 1))
    metrics = evaluate_query(
        query,
        [],
        retrieval_top_k=5,
        error="API unavailable",
    )
    assert metrics.error == "API unavailable"
    assert metrics.recall_at_5 is None
    assert metrics.mrr is None


def test_evaluate_query_rejects_missing_ground_truth_identifiers():
    bad = EvalQuery(
        query_id="BAD",
        question="x",
        primary_relevant=(),
    )
    with pytest.raises(ValueError, match="no primary relevant"):
        evaluate_query(bad, [], retrieval_top_k=5)


def test_aggregate_skips_errored_queries():
    ok = evaluate_query(
        _query(("a.md", 1), query_id="OK"),
        [_hit("a.md", 1)],
        retrieval_top_k=5,
    )
    bad = evaluate_query(
        _query(("a.md", 1), query_id="BAD"),
        [],
        retrieval_top_k=5,
        error="down",
    )
    aggregate = evaluate_run([ok, bad])
    assert aggregate.scored_query_count == 1
    assert aggregate.skipped_query_ids == ["BAD"]
    assert aggregate.source_coverage == pytest.approx(1.0)
    assert aggregate.mean_mrr == pytest.approx(1.0)


def test_dataset_has_seven_queries_with_primary_truth():
    queries = get_eval_queries()
    assert len(queries) == 7
    assert [q.query_id for q in queries] == [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
        "Q7",
    ]
    assert EVAL_QUERIES[0].question == "How long does delivery take?"
    # Q5 must not treat refund eligibility chunks as primary
    q5 = next(q for q in queries if q.query_id == "Q5")
    assert all(
        c.document_name == "customer_support_guidelines.md"
        for c in q5.primary_relevant
    )
    # Q6 / Q7 primary sets match the approved baseline
    q6 = next(q for q in queries if q.query_id == "Q6")
    q7 = next(q for q in queries if q.query_id == "Q7")
    assert [c.label() for c in q6.primary_relevant] == ["refund_policy.md#1"]
    assert [c.label() for c in q7.primary_relevant] == ["refund_policy.md#6"]
