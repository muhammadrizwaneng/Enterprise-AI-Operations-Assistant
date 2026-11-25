"""Unit tests for Step 11 ablation (no live LLM)."""

from __future__ import annotations

from app.schemas.search import SemanticSearchResult
from experiments.retrieval_eval.evidence_guard import (
    EvidenceNeed,
    assess_evidence_sufficiency,
    classify_evidence_need,
)
from experiments.retrieval_eval.selective_strategies import _chunk_truncated
from experiments.retrieval_eval.step11_general_no_truncation.general_no_truncation_guard import (
    assess_evidence_sufficiency_no_general_truncation,
)
from experiments.retrieval_eval.step11_general_no_truncation.h2_answer_key import (
    ANSWER_KEYS,
)
from experiments.retrieval_eval.step11_general_no_truncation.h2_dataset import (
    get_h2_queries,
)
from experiments.retrieval_eval.step11_general_no_truncation.h2_scoring import (
    score_h2_answer,
)


def _hit(name: str, idx: int, text: str, sim: float = 0.9) -> SemanticSearchResult:
    return SemanticSearchResult(
        document_name=name,
        chunk_index=idx,
        chunk_text=text,
        similarity=sim,
        distance=1.0 - sim,
    )


def test_h2_dataset_ids_and_size():
    qs = get_h2_queries()
    assert len(qs) == 20
    assert [q.query_id for q in qs] == [f"Q{i}" for i in range(28, 48)]
    assert set(ANSWER_KEYS) == {q.query_id for q in qs}


def test_h2_independent_of_prior_splits():
    ids = {q.query_id for q in get_h2_queries()}
    prior = {f"Q{i}" for i in range(1, 28)}
    assert ids.isdisjoint(prior)


def test_procedure_and_requirement_coverage():
    qs = get_h2_queries()
    cats = {q.evidence_category for q in qs}
    assert "procedure" in cats
    assert "requirement_evidence" in cats
    assert "general_policy" in cats
    needs = {classify_evidence_need(q.question) for q in qs}
    assert EvidenceNeed.PROCEDURE in needs
    assert EvidenceNeed.REQUIREMENT_EVIDENCE in needs


def test_ablation_ignores_truncation_when_other_signals_absent():
    # High lexical coverage + truncation only (no table/procedure signals).
    text = (
        "When an order is placed, address changes are allowed only before "
        "the shipping label is created. After the order is placed, customers "
        "must coordinate with the carrier if the label already exists. "
        + ("x" * 400)
    )
    assert _chunk_truncated(text)
    hits = [_hit("delivery_policy.md", 5, text)]
    question = "When are address changes allowed after an order is placed?"
    frozen = assess_evidence_sufficiency(question, hits)
    abl = assess_evidence_sufficiency_no_general_truncation(question, hits)
    assert frozen.need == EvidenceNeed.GENERAL
    assert abl.need == EvidenceNeed.GENERAL
    assert frozen.skip_expansion is False
    assert abl.skip_expansion is True
    assert "chunk_truncation_ignored_in_general" in abl.reasons
    assert "no_table_or_procedure_incompleteness" in abl.reasons


def test_specialized_paths_unchanged():
    # Requirement-style question with a clear requirement statement.
    hits = [
        _hit(
            "product_documentation.md",
            3,
            "Monitor pixel defects must meet ISO 9241-307 Class II. "
            "Evidence required: photo of the panel and diagnostic report.",
        )
    ]
    q = (
        "What evidence is required for monitor pixel-defect "
        "replacement eligibility?"
    )
    frozen = assess_evidence_sufficiency(q, hits)
    abl = assess_evidence_sufficiency_no_general_truncation(q, hits)
    assert frozen.need == EvidenceNeed.REQUIREMENT_EVIDENCE
    assert abl.need == EvidenceNeed.REQUIREMENT_EVIDENCE
    assert frozen.skip_expansion == abl.skip_expansion


def test_scoring_full_match():
    scored = score_h2_answer(
        "Q36",
        "Use security@novaforge.example for security incidents.",
        primary_in_context=["privacy_policy.md#7"],
        primary_missing=[],
    )
    assert scored["total"] == 28
    assert scored["facts_hit"] == 1


def test_scoring_miss():
    scored = score_h2_answer(
        "Q36",
        "Email support@example.com instead.",
        primary_in_context=[],
        primary_missing=["privacy_policy.md#7"],
    )
    assert scored["total"] < 14
