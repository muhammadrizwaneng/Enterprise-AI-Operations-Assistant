"""Unit tests for evidence sufficiency guard (Step 8). Experiment-only."""

from __future__ import annotations

import inspect

import pytest

from app.schemas.search import SemanticSearchResult
from experiments.retrieval_eval import evidence_guard as eg
from experiments.retrieval_eval.evidence_guard import (
    EvidenceNeed,
    GuardDecision,
    assess_evidence_sufficiency,
    classify_evidence_need,
    plan_guarded_hybrid_cap2,
)
from experiments.retrieval_eval.selective_strategies import plan_hybrid


def _hit(
    doc: str,
    idx: int,
    text: str,
    *,
    sim: float = 0.7,
) -> SemanticSearchResult:
    return SemanticSearchResult(
        document_name=doc,
        chunk_index=idx,
        chunk_text=text,
        similarity=sim,
        distance=1.0 - sim,
    )


def test_classify_requirement_evidence_need():
    need = classify_evidence_need(
        "What evidence is required for defective products?"
    )
    assert need == EvidenceNeed.REQUIREMENT_EVIDENCE


def test_classify_duration_need():
    assert (
        classify_evidence_need("How long does delivery take?")
        == EvidenceNeed.DURATION_TABLE
    )


def test_classify_procedure_need():
    assert (
        classify_evidence_need(
            "What happens if a package is overdue by seven days?"
        )
        == EvidenceNeed.PROCEDURE
    )


def test_sufficient_requirement_skips_expansion():
    hits = [
        _hit(
            "refund_policy.md",
            1,
            "Defective or incorrect items: may be refunded or replaced "
            "outside the standard window when supported by photographic "
            "evidence or a support ticket.",
        ),
        _hit(
            "refund_policy.md",
            2,
            "Other refund window text without changing the requirement.",
        ),
    ]
    result = assess_evidence_sufficiency(
        "What evidence is required for defective products?", hits
    )
    assert result.decision == GuardDecision.SUFFICIENT
    assert result.skip_expansion is True


def test_incomplete_duration_allows_expansion():
    # Truncated methods table — should be insufficient.
    truncated = (
        "## Shipping Methods\n\n| Method | Transit |\n|---|---|\n"
        "| Standard Ground | 3–7 business day"
    )  # truncated mid-cell, no closing pipe / incomplete
    # Pad to look like chunk window truncation.
    truncated = truncated + ("x" * 400)
    hits = [_hit("delivery_policy.md", 1, truncated)]
    result = assess_evidence_sufficiency(
        "How long does delivery take?", hits
    )
    assert result.decision == GuardDecision.INSUFFICIENT
    assert result.skip_expansion is False


def test_complete_methods_table_is_sufficient():
    table = (
        "| Method | Typical Transit | Use Case |\n"
        "|---|---|---|\n"
        "| Standard Ground | 3–7 business days | Default |\n"
        "| Expedited | 2–3 business days | Faster |\n"
        "| Overnight | Next business day | Urgent |\n"
        "| Freight | Scheduled | Bulk |\n"
    )
    hits = [_hit("delivery_policy.md", 2, table)]
    result = assess_evidence_sufficiency(
        "How long does delivery take?", hits
    )
    assert result.decision == GuardDecision.SUFFICIENT
    assert result.skip_expansion is True


def test_empty_retrieval_handled_safely():
    result = assess_evidence_sufficiency("Any question?", [])
    assert result.decision == GuardDecision.INSUFFICIENT
    assert result.skip_expansion is True  # nothing to expand
    planned, guard = plan_guarded_hybrid_cap2([], question="Any question?")
    assert planned == []
    assert guard.skip_expansion is True


def test_multiple_chunks_requirement_detected_in_any_hit():
    hits = [
        _hit("other.md", 0, "Unrelated introduction without requirements."),
        _hit(
            "refund_policy.md",
            1,
            "Defective products require photographic evidence or a support "
            "ticket before a refund is approved.",
        ),
    ]
    result = assess_evidence_sufficiency(
        "What evidence is required for defective products?", hits
    )
    assert result.decision == GuardDecision.SUFFICIENT


def test_guard_is_deterministic():
    hits = [
        _hit(
            "refund_policy.md",
            1,
            "Photographic evidence is required for defective products.",
        )
    ]
    q = "What evidence is required for defective products?"
    a = assess_evidence_sufficiency(q, hits)
    b = assess_evidence_sufficiency(q, hits)
    assert a == b
    assert a.to_dict() == b.to_dict()


def test_runtime_guard_source_has_no_ground_truth_imports():
    src = inspect.getsource(eg)
    forbidden = [
        "primary_relevant",
        "optional_supporting",
        "EVAL_QUERIES",
        "get_eval_queries",
        "EvalQuery",
        "ground_truth",
        "query_id",
        '"Q6"',
        "'Q6'",
    ]
    for token in forbidden:
        assert token not in src, f"guard must not reference {token}"


def test_hybrid_cap2_planner_unchanged_callable():
    # plan_hybrid still exists and accepts the same signature used by Step 6.
    assert callable(plan_hybrid)
    hits = [
        _hit(
            "delivery_policy.md",
            1,
            "| Method | Transit |\n|---|---|\n| Standard Ground | 3–7 business "
            + ("y" * 460),
        )
    ]
    # Unguarded hybrid may plan neighbors; guarded with sufficient should not.
    # Here truncated table → both may expand; just ensure call works.
    planned = plan_hybrid(hits, question="How long does delivery take?", max_expanded=2)
    assert isinstance(planned, list)


def test_guarded_skips_hybrid_when_sufficient():
    hits = [
        _hit(
            "refund_policy.md",
            1,
            "Defective or incorrect items require photographic evidence or "
            "a support ticket.",
        )
    ]
    planned, guard = plan_guarded_hybrid_cap2(
        hits,
        question="What evidence is required for defective products?",
        max_expanded=2,
    )
    assert guard.skip_expansion is True
    assert planned == []


def test_guarded_calls_hybrid_when_insufficient():
    truncated = (
        "## Shipping\n\n| Method | Typical Transit |\n|---|---|\n"
        "| Standard Ground | 3–7 business day"
    ) + ("z" * 450)
    hits = [_hit("delivery_policy.md", 1, truncated, sim=0.8)]
    # Provide preview for next chunk so hybrid/C can plan.
    preview = {
        (hits[0].document_name, hits[0].chunk_index + 1): (
            "| Expedited | 2–3 business days |\n"
            "| Overnight | Next business day |\n" + ("| a | b |\n" * 5)
        )
    }
    planned, guard = plan_guarded_hybrid_cap2(
        hits,
        question="How long does delivery take?",
        neighbor_preview=preview,
        max_expanded=2,
    )
    assert guard.skip_expansion is False
    # May or may not find neighbors depending on heuristics; decision is the assert.
    assert guard.decision == GuardDecision.INSUFFICIENT


def test_eligibility_incomplete_without_lost_rule():
    hits = [
        _hit(
            "delivery_policy.md",
            4,
            "An order becomes **overdue** when the promised delivery date "
            "has passed and no delivery confirmation exists.",
        )
    ]
    result = assess_evidence_sufficiency(
        "Can I get a refund if my delivery is late?", hits
    )
    assert result.decision == GuardDecision.INSUFFICIENT


def test_off_blind_strategies_untouched_imports():
    from experiments.retrieval_eval.selective_strategies import (
        plan_blind,
        plan_off,
    )

    assert plan_off([], question="x") == []
    # blind on empty is empty
    assert plan_blind([], question="x") == []
