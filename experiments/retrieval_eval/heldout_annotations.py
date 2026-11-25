"""
Offline human evidence annotations for held-out evaluation (Step 9).

These annotations are for analysis only. They must never be passed into
``evidence_guard`` or answer-generation runtime paths.
"""

from __future__ import annotations

from experiments.retrieval_eval.heldout_dataset import (
    HELDOUT_QUERIES,
    HeldOutQuery,
    get_heldout_queries,
)


def annotation_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in get_heldout_queries():
        q = item.query
        rows.append(
            {
                "query_id": q.query_id,
                "question": q.question,
                "evidence_category": item.evidence_category,
                "difficulty": item.difficulty,
                "primary_relevant": [c.label() for c in q.primary_relevant],
                "optional_supporting": [
                    c.label() for c in q.optional_supporting
                ],
                "notes": item.notes,
            }
        )
    return rows


def by_category() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for item in HELDOUT_QUERIES:
        out.setdefault(item.evidence_category, []).append(item.query_id)
    return out
