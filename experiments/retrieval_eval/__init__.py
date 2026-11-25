"""
Retrieval evaluation baseline (Phase 4.2 P1 Step 2A).

Measures semantic search quality against a fixed ground-truth dataset.
Does not modify production retrieval, RAG, chunking, or embeddings.
"""

from experiments.retrieval_eval.dataset import EVAL_QUERIES, ChunkRef, EvalQuery
from experiments.retrieval_eval.metrics import (
    AggregateMetrics,
    QueryMetrics,
    evaluate_query,
    evaluate_run,
)

__all__ = [
    "EVAL_QUERIES",
    "ChunkRef",
    "EvalQuery",
    "AggregateMetrics",
    "QueryMetrics",
    "evaluate_query",
    "evaluate_run",
]
