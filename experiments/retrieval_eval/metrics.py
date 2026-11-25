"""
Pure retrieval metric helpers (unit-testable, no I/O).

All metrics are computed against *primary* relevant chunks unless noted.
Optional supporting chunks are ignored for scoring so distractors and
secondary context do not inflate recall.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from experiments.retrieval_eval.dataset import ChunkRef, EvalQuery


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    document_name: str
    chunk_index: int
    similarity: float

    def key(self) -> tuple[str, int]:
        return (self.document_name, self.chunk_index)

    def label(self) -> str:
        return f"{self.document_name}#{self.chunk_index}"


@dataclass(slots=True)
class QueryMetrics:
    query_id: str
    question: str
    primary_relevant: list[str]
    retrieved: list[dict[str, object]]
    result_count: int
    recall_at_5: float | None
    recall_at_10: float | None
    precision_at_5: float | None
    mrr: float | None
    first_relevant_rank: int | None
    missing_relevant: list[str]
    source_hit: bool
    error: str | None = None


@dataclass(slots=True)
class AggregateMetrics:
    query_count: int
    mean_recall_at_5: float | None
    mean_recall_at_10: float | None
    mean_precision_at_5: float | None
    mean_mrr: float | None
    source_coverage: float | None
    scored_query_count: int
    skipped_query_ids: list[str] = field(default_factory=list)


def _dedupe_preserve_order(
    retrieved: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    """Keep first occurrence of each (document_name, chunk_index)."""
    seen: set[tuple[str, int]] = set()
    out: list[RetrievedChunk] = []
    for item in retrieved:
        key = item.key()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def recall_at_k(
    relevant: set[tuple[str, int]],
    retrieved: list[RetrievedChunk],
    k: int,
) -> float:
    """
    |relevant ∩ top-k retrieved| / |relevant|.

    Raises ValueError if ``relevant`` is empty (missing ground truth).
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    if not relevant:
        raise ValueError("relevant set must not be empty")
    top = {item.key() for item in _dedupe_preserve_order(retrieved)[:k]}
    return len(relevant & top) / len(relevant)


def precision_at_k(
    relevant: set[tuple[str, int]],
    retrieved: list[RetrievedChunk],
    k: int,
) -> float:
    """
    |relevant ∩ top-k retrieved| / k.

    Empty retrieval yields 0.0. Empty ``relevant`` raises ValueError.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    if not relevant:
        raise ValueError("relevant set must not be empty")
    top = {item.key() for item in _dedupe_preserve_order(retrieved)[:k]}
    return len(relevant & top) / k


def reciprocal_rank(
    relevant: set[tuple[str, int]],
    retrieved: list[RetrievedChunk],
) -> float:
    """
    1 / rank of the first relevant hit (1-based). Returns 0.0 if none.

    Empty ``relevant`` raises ValueError.
    """
    if not relevant:
        raise ValueError("relevant set must not be empty")
    for rank, item in enumerate(_dedupe_preserve_order(retrieved), start=1):
        if item.key() in relevant:
            return 1.0 / rank
    return 0.0


def first_relevant_rank(
    relevant: set[tuple[str, int]],
    retrieved: list[RetrievedChunk],
) -> int | None:
    if not relevant:
        raise ValueError("relevant set must not be empty")
    for rank, item in enumerate(_dedupe_preserve_order(retrieved), start=1):
        if item.key() in relevant:
            return rank
    return None


def missing_relevant_chunks(
    relevant: set[tuple[str, int]],
    retrieved: list[RetrievedChunk],
    k: int | None = None,
) -> list[ChunkRef]:
    """Primary relevant chunks not present in retrieved (optionally top-k)."""
    if not relevant:
        raise ValueError("relevant set must not be empty")
    ordered = _dedupe_preserve_order(retrieved)
    if k is not None:
        ordered = ordered[:k]
    found = {item.key() for item in ordered}
    missing = sorted(relevant - found)
    return [ChunkRef(document_name=d, chunk_index=i) for d, i in missing]


def source_coverage(hits: list[bool]) -> float:
    """Fraction of questions with at least one primary relevant chunk hit."""
    if not hits:
        raise ValueError("hits list must not be empty")
    return sum(1 for h in hits if h) / len(hits)


def evaluate_query(
    query: EvalQuery,
    retrieved: list[RetrievedChunk],
    *,
    retrieval_top_k: int,
    error: str | None = None,
) -> QueryMetrics:
    """
    Score one query.

    ``retrieval_top_k`` is the API request size. Recall@10 is only computed
    when ``retrieval_top_k >= 10`` so a top_k=5 run does not silently under-
    report Recall@10. Metrics are None when ground truth or the run is invalid.
    """
    query.require_primary()
    primary = query.primary_keys()
    labels = [c.label() for c in query.primary_relevant]
    retrieved_view = [
        {
            "document_name": r.document_name,
            "chunk_index": r.chunk_index,
            "similarity": r.similarity,
            "label": r.label(),
        }
        for r in _dedupe_preserve_order(retrieved)
    ]

    if error:
        return QueryMetrics(
            query_id=query.query_id,
            question=query.question,
            primary_relevant=labels,
            retrieved=retrieved_view,
            result_count=len(retrieved_view),
            recall_at_5=None,
            recall_at_10=None,
            precision_at_5=None,
            mrr=None,
            first_relevant_rank=None,
            missing_relevant=labels,
            source_hit=False,
            error=error,
        )

    if retrieval_top_k < 1:
        raise ValueError("retrieval_top_k must be >= 1")

    deduped = _dedupe_preserve_order(retrieved)
    r5 = recall_at_k(primary, deduped, 5)
    r10 = (
        recall_at_k(primary, deduped, 10)
        if retrieval_top_k >= 10
        else None
    )
    p5 = precision_at_k(primary, deduped, 5)
    mrr = reciprocal_rank(primary, deduped)
    first_rank = first_relevant_rank(primary, deduped)
    missing = [
        c.label()
        for c in missing_relevant_chunks(primary, deduped, k=retrieval_top_k)
    ]
    hit = first_rank is not None

    return QueryMetrics(
        query_id=query.query_id,
        question=query.question,
        primary_relevant=labels,
        retrieved=retrieved_view,
        result_count=len(deduped),
        recall_at_5=r5,
        recall_at_10=r10,
        precision_at_5=p5,
        mrr=mrr,
        first_relevant_rank=first_rank,
        missing_relevant=missing,
        source_hit=hit,
        error=None,
    )


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def evaluate_run(results: list[QueryMetrics]) -> AggregateMetrics:
    """Aggregate only queries that produced valid (non-error) scores."""
    if not results:
        raise ValueError("results must not be empty")

    scored: list[QueryMetrics] = []
    skipped: list[str] = []
    for item in results:
        if item.error or item.recall_at_5 is None:
            skipped.append(item.query_id)
        else:
            scored.append(item)

    if not scored:
        return AggregateMetrics(
            query_count=len(results),
            mean_recall_at_5=None,
            mean_recall_at_10=None,
            mean_precision_at_5=None,
            mean_mrr=None,
            source_coverage=None,
            scored_query_count=0,
            skipped_query_ids=skipped,
        )

    return AggregateMetrics(
        query_count=len(results),
        mean_recall_at_5=_mean([q.recall_at_5 for q in scored if q.recall_at_5 is not None]),
        mean_recall_at_10=_mean(
            [q.recall_at_10 for q in scored if q.recall_at_10 is not None]
        ),
        mean_precision_at_5=_mean(
            [q.precision_at_5 for q in scored if q.precision_at_5 is not None]
        ),
        mean_mrr=_mean([q.mrr for q in scored if q.mrr is not None]),
        source_coverage=source_coverage([q.source_hit for q in scored]),
        scored_query_count=len(scored),
        skipped_query_ids=skipped,
    )
