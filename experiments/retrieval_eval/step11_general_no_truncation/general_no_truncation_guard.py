"""
Step 11 ablation planner: GENERAL_NO_TRUNCATION.

Copies Step 8 guard behavior except the GENERAL path no longer treats
``_chunk_truncated`` as an incompleteness signal.

Preserved unchanged:
- Need classification
- Specialized sufficiency checkers (requirement/procedure/duration/eligibility/contact)
- HYBRID_CAP2 planner when expansion is allowed

Does NOT modify ``experiments/retrieval_eval/evidence_guard.py``.
"""

from __future__ import annotations

from typing import Sequence

from app.schemas.search import SemanticSearchResult

from experiments.retrieval_eval.evidence_guard import (
    EvidenceGuardResult,
    EvidenceNeed,
    GuardDecision,
    _complete_duration_table,
    _complete_procedure,
    _contact_support_complete,
    _eligibility_complete,
    _has_requirement_statement,
    _joined,
    classify_evidence_need,
)
from experiments.retrieval_eval.selective_strategies import (
    _procedure_needs_next,
    _question_terms,
    _table_appears_incomplete,
    plan_hybrid,
)


def assess_evidence_sufficiency_no_general_truncation(
    question: str,
    hits: Sequence[SemanticSearchResult],
) -> EvidenceGuardResult:
    """Same as Step 8 assess_evidence_sufficiency, minus GENERAL truncation trigger."""
    need = classify_evidence_need(question)
    reasons: list[str] = [f"need={need.value}", "ablation=general_no_truncation"]

    if not hits:
        reasons.append("empty_retrieval")
        return EvidenceGuardResult(
            decision=GuardDecision.INSUFFICIENT,
            need=need,
            reasons=tuple(reasons),
            skip_expansion=True,
        )

    if need == EvidenceNeed.REQUIREMENT_EVIDENCE:
        ok, detail = _has_requirement_statement(hits, question)
        reasons.append(detail)
        decision = (
            GuardDecision.SUFFICIENT if ok else GuardDecision.INSUFFICIENT
        )
    elif need == EvidenceNeed.PROCEDURE:
        ok, detail = _complete_procedure(hits)
        reasons.append(detail)
        decision = (
            GuardDecision.SUFFICIENT if ok else GuardDecision.INSUFFICIENT
        )
    elif need == EvidenceNeed.DURATION_TABLE:
        ok, detail = _complete_duration_table(hits)
        reasons.append(detail)
        decision = (
            GuardDecision.SUFFICIENT if ok else GuardDecision.INSUFFICIENT
        )
    elif need == EvidenceNeed.ELIGIBILITY:
        ok, detail = _eligibility_complete(hits, question)
        reasons.append(detail)
        decision = (
            GuardDecision.SUFFICIENT if ok else GuardDecision.INSUFFICIENT
        )
    elif need == EvidenceNeed.CONTACT_SUPPORT:
        ok, detail = _contact_support_complete(hits)
        reasons.append(detail)
        decision = (
            GuardDecision.SUFFICIENT if ok else GuardDecision.INSUFFICIENT
        )
    else:
        # ABLATION: do NOT use _chunk_truncated here.
        joined = _joined(hits)
        qterms = _question_terms(question)
        coverage = (
            sum(1 for t in qterms if t in joined.lower()) / len(qterms)
            if qterms
            else 0.0
        )
        incomplete = any(
            _table_appears_incomplete(h.chunk_text)
            or _procedure_needs_next(h.chunk_text)
            for h in hits
        )
        reasons.append(f"lexical_coverage={coverage:.2f}")
        reasons.append(
            "table_or_procedure_incompleteness"
            if incomplete
            else "no_table_or_procedure_incompleteness"
        )
        reasons.append("chunk_truncation_ignored_in_general")
        if coverage >= 0.6 and not incomplete:
            decision = GuardDecision.SUFFICIENT
            reasons.append("general_sufficient_ablation")
        else:
            decision = GuardDecision.INSUFFICIENT
            reasons.append("general_insufficient_ablation")

    return EvidenceGuardResult(
        decision=decision,
        need=need,
        reasons=tuple(reasons),
        skip_expansion=(decision == GuardDecision.SUFFICIENT),
    )


def plan_general_no_truncation(
    hits: list[SemanticSearchResult],
    *,
    question: str,
    neighbor_preview: dict[tuple[str, int], str] | None = None,
    max_expanded: int = 2,
):
    """Guard with ablation, then unchanged plan_hybrid if expansion allowed."""
    guard = assess_evidence_sufficiency_no_general_truncation(question, hits)
    if guard.skip_expansion:
        return [], guard
    planned = plan_hybrid(
        hits,
        question=question,
        neighbor_preview=neighbor_preview,
        max_expanded=max(max_expanded, 8),
    )
    return planned, guard
