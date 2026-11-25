"""Checklist scoring for H2 (Q28–Q45). Offline answer key only."""

from __future__ import annotations

from typing import Any

from experiments.retrieval_eval.hybrid_scoring import METRICS
from experiments.retrieval_eval.step11_general_no_truncation.h2_answer_key import (
    get_answer_key,
)


def _any(text: str, *needles: str) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


def score_h2_answer(
    query_id: str,
    answer: str,
    *,
    primary_in_context: list[str],
    primary_missing: list[str],
) -> dict[str, Any]:
    key = get_answer_key(query_id)
    a = answer or ""
    facts_hit = sum(1 for f in key.expected_facts if f.lower() in a.lower())
    facts_total = max(1, len(key.expected_facts))
    groups_ok = (
        all(_any(a, *group) for group in key.required_any_groups)
        if key.required_any_groups
        else True
    )

    if facts_hit == facts_total and groups_ok:
        scores = {
            "correctness": 4,
            "completeness": 4,
            "evidence_utilization": 4 if not primary_missing else 3,
            "unsupported_claims": 4,
            "conditions_exceptions": 4,
            "relevance": 4,
            "source_consistency": 4,
        }
    elif facts_hit >= max(1, facts_total - 1) and (
        groups_ok or facts_hit == facts_total
    ):
        scores = {
            "correctness": 3,
            "completeness": 3 if groups_ok else 2,
            "evidence_utilization": 3 if primary_in_context else 2,
            "unsupported_claims": 3,
            "conditions_exceptions": 3 if groups_ok else 2,
            "relevance": 4,
            "source_consistency": 3,
        }
    elif facts_hit >= 1 or any(_any(a, f) for f in key.expected_facts):
        scores = {
            "correctness": 2,
            "completeness": 2,
            "evidence_utilization": 2,
            "unsupported_claims": 3,
            "conditions_exceptions": 2,
            "relevance": 3,
            "source_consistency": 2,
        }
    else:
        scores = {
            "correctness": 1,
            "completeness": 1,
            "evidence_utilization": 1 if primary_in_context else 0,
            "unsupported_claims": 3,
            "conditions_exceptions": 1,
            "relevance": 2,
            "source_consistency": 1,
        }

    if primary_missing and not primary_in_context:
        scores["evidence_utilization"] = min(scores["evidence_utilization"], 1)
        scores["completeness"] = min(scores["completeness"], 2)

    total = sum(scores[m] for m in METRICS)
    return {
        "scores": scores,
        "total": total,
        "note": (
            f"facts={facts_hit}/{facts_total} groups_ok={groups_ok} "
            f"missing={primary_missing}"
        ),
        "key_summary": key.summary,
        "facts_hit": facts_hit,
        "facts_total": facts_total,
        "groups_ok": groups_ok,
    }
