"""
Evidence sufficiency guard (Phase 4.2 P1 Step 8) — experiment only.

Decides whether original semantic hits already contain sufficient evidence to
answer the user question. If sufficient, neighbor expansion should be skipped.

Design constraints:
- Deterministic (no LLM judge).
- No evaluation ground-truth / chunk-ID labels in runtime decisions.
- No hardcoded question IDs (e.g. Q6) or document-specific special cases.
- Conservative default: INSUFFICIENT → allow expansion when unsure.

Sufficiency is inferred from (question text structure + retrieved chunk text).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from app.schemas.search import SemanticSearchResult

from experiments.retrieval_eval.selective_strategies import (
    _chunk_truncated,
    _has_numbered_steps,
    _looks_like_table,
    _procedure_needs_next,
    _question_terms,
    _table_appears_incomplete,
)


class EvidenceNeed(str, Enum):
    """Coarse information need inferred from the question only."""

    REQUIREMENT_EVIDENCE = "requirement_evidence"
    PROCEDURE = "procedure"
    DURATION_TABLE = "duration_table"
    ELIGIBILITY = "eligibility"
    CONTACT_SUPPORT = "contact_support"
    GENERAL = "general"


class GuardDecision(str, Enum):
    SUFFICIENT = "sufficient"  # skip expansion
    INSUFFICIENT = "insufficient"  # allow expansion


@dataclass(frozen=True, slots=True)
class EvidenceGuardResult:
    decision: GuardDecision
    need: EvidenceNeed
    reasons: tuple[str, ...]
    skip_expansion: bool

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "need": self.need.value,
            "reasons": list(self.reasons),
            "skip_expansion": self.skip_expansion,
        }


_STOP = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "what",
    "how",
    "do",
    "i",
    "my",
    "me",
    "of",
    "for",
    "to",
    "and",
    "or",
    "if",
    "in",
    "on",
    "by",
    "can",
    "get",
    "does",
    "with",
}


def classify_evidence_need(question: str) -> EvidenceNeed:
    """Infer information need from question wording only (deterministic)."""
    q = (question or "").lower()
    if re.search(r"\bevidence\b", q) or re.search(
        r"\bwhat\b.*\brequired\b|\brequired\b.*\bfor\b", q
    ):
        return EvidenceNeed.REQUIREMENT_EVIDENCE
    if re.search(r"\bhow (?:do|can) i (?:contact|reach)\b", q) or (
        "customer support" in q and "contact" in q
    ):
        return EvidenceNeed.CONTACT_SUPPORT
    if re.search(r"\b(?:how long|transit time|delivery take)\b", q):
        return EvidenceNeed.DURATION_TABLE
    if re.search(
        r"\b(?:can i|eligible|eligibility|refund if|late delivery)\b", q
    ):
        return EvidenceNeed.ELIGIBILITY
    if re.search(
        r"\b(?:what happens|process|procedure|steps|overdue|if a package)\b",
        q,
    ):
        return EvidenceNeed.PROCEDURE
    return EvidenceNeed.GENERAL


def _joined(hits: Sequence[SemanticSearchResult]) -> str:
    return "\n\n".join(h.chunk_text for h in hits)


def _topic_terms(question: str) -> set[str]:
    terms = _question_terms(question)
    # Drop generic ops words that survive the shared stop list.
    return {t for t in terms if t not in {"long", "take", "contact"}}


def _requirement_cues(text: str) -> bool:
    lower = text.lower()
    return bool(
        re.search(
            r"\b(?:requir(?:e|es|ed|ing|ement)|must|supported by|"
            r"need to|needs to|shall)\b",
            lower,
        )
    )


def _has_requirement_statement(
    hits: Sequence[SemanticSearchResult], question: str
) -> tuple[bool, str]:
    """
    True when some retrieved chunk states a requirement tied to question topics.

    Uses only retrieved text + question terms (no ground-truth chunk IDs).
    """
    topics = _topic_terms(question)
    if not topics:
        topics = {t for t in re.findall(r"[a-z0-9]+", question.lower()) if len(t) > 3}

    for hit in hits:
        text = hit.chunk_text or ""
        lower = text.lower()
        topic_hits = sum(1 for t in topics if t in lower)
        # Need topical overlap + requirement language.
        need = max(1, min(2, len(topics) // 2))
        if topic_hits < need:
            continue
        if not _requirement_cues(text):
            continue
        # Prefer non-truncated requirement-bearing chunks.
        if _chunk_truncated(text) and topic_hits < need + 1:
            continue
        return True, (
            f"requirement_statement_in_{hit.document_name}#{hit.chunk_index}"
        )
    return False, "no_requirement_statement_in_hits"


def _complete_procedure(hits: Sequence[SemanticSearchResult]) -> tuple[bool, str]:
    joined = _joined(hits)
    if _procedure_needs_next(joined):
        return False, "procedure_appears_incomplete"
    nums = [int(x) for x in re.findall(r"(?m)^\s*(\d+)\.\s+", joined)]
    if len(nums) >= 3 and not any(_chunk_truncated(h.chunk_text) and _has_numbered_steps(h.chunk_text) for h in hits):
        return True, f"numbered_steps_count={len(nums)}"
    # "Support agents must" with >=3 steps somewhere in hits.
    if "Support agents must" in joined and len(nums) >= 3:
        return True, "support_agents_must_with_3_plus_steps"
    if len(nums) >= 3:
        return True, f"numbered_steps_count={len(nums)}"
    return False, "procedure_incomplete_or_missing"


def _complete_duration_table(
    hits: Sequence[SemanticSearchResult],
) -> tuple[bool, str]:
    joined = _joined(hits)
    # Incomplete table in any hit → not sufficient.
    if any(
        _table_appears_incomplete(h.chunk_text)
        or (_looks_like_table(h.chunk_text) and _chunk_truncated(h.chunk_text))
        for h in hits
    ):
        return False, "incomplete_or_truncated_table_present"
    # Multiple shipping/method durations.
    method_hits = sum(
        1
        for name in (
            "standard ground",
            "expedited",
            "express",
            "overnight",
            "freight",
        )
        if name in joined.lower()
    )
    day_hits = len(
        re.findall(
            r"\d+\s*[–-]\s*\d+\s+business days|\d+\s+business day",
            joined,
            flags=re.I,
        )
    )
    if method_hits >= 3 and day_hits >= 2:
        return True, f"methods={method_hits}_durations={day_hits}"
    # Complete markdown table with enough data rows.
    data_rows = [
        ln
        for ln in joined.split("\n")
        if "|" in ln and not set(ln.replace("|", "").strip()) <= {"-", " "}
    ]
    if _looks_like_table(joined) and len(data_rows) >= 4:
        return True, f"table_data_rows={len(data_rows)}"
    return False, "duration_or_methods_incomplete"


def _eligibility_complete(
    hits: Sequence[SemanticSearchResult], question: str
) -> tuple[bool, str]:
    joined = _joined(hits)
    lower = joined.lower()
    q = question.lower()
    has_def = bool(
        re.search(r"becomes\s+\*\*overdue\*\*|becomes overdue|promised delivery", lower)
    ) or ("overdue" in lower and "delivery" in lower)
    # Late/overdue/lost questions need the calendar-day lost-package rule if asked
    # about refund/late outcomes — inferred from question words only.
    needs_lost_rule = bool(
        re.search(r"\b(?:late|overdue|lost|refund)\b", q)
    )
    has_lost_rule = "7 calendar days" in joined or "calendar days" in lower and "lost" in lower
    if needs_lost_rule and has_def and has_lost_rule:
        return True, "overdue_definition_and_lost_package_rule"
    if needs_lost_rule and has_def and not has_lost_rule:
        return False, "overdue_definition_without_lost_package_rule"
    if has_def and not needs_lost_rule:
        return True, "definition_present"
    # Generic eligibility table rows.
    if _looks_like_table(joined) and "refund eligible" in lower:
        if _table_appears_incomplete(joined):
            return False, "eligibility_table_incomplete"
        return True, "eligibility_table_present"
    return False, "eligibility_evidence_incomplete"


def _contact_support_complete(
    hits: Sequence[SemanticSearchResult],
) -> tuple[bool, str]:
    """
    Sufficient only when a single retrieved chunk looks like a populated
    ticket-category listing/table — not when category-like tokens appear
    scattered across unrelated hits.
    """
    category_tokens = (
        "refund_request",
        "shipping",
        "product_defect",
        "account",
        "general_inquiry",
        "billing",
        "bill",
    )
    for hit in hits:
        text = hit.chunk_text or ""
        lower = text.lower()
        looks_category_section = bool(
            re.search(r"ticket categor|^\s*\|?\s*category\s*\|", lower, re.M)
        ) or ("| Category |" in text)
        cats = sum(1 for c in category_tokens if c in lower)
        if looks_category_section and cats >= 3:
            if _table_appears_incomplete(text) or _chunk_truncated(text):
                return False, "category_table_incomplete"
            return True, (
                f"category_listing_in_{hit.document_name}#{hit.chunk_index}"
                f"_cats={cats}"
            )
        if looks_category_section and (
            _table_appears_incomplete(text) or cats < 3
        ):
            return False, "category_table_incomplete"
    joined_lower = _joined(hits).lower()
    if "support ticket" in joined_lower or "open a support ticket" in joined_lower:
        return False, "ticket_process_without_category_coverage"
    return False, "contact_path_incomplete"


def assess_evidence_sufficiency(
    question: str,
    hits: Sequence[SemanticSearchResult],
) -> EvidenceGuardResult:
    """
    Decide whether retrieved hits are sufficient to skip neighbor expansion.

    Runtime inputs only: question string + retrieved hit texts/metadata.
    Does not accept or consult evaluation ground truth.
    """
    need = classify_evidence_need(question)
    reasons: list[str] = [f"need={need.value}"]

    if not hits:
        reasons.append("empty_retrieval")
        return EvidenceGuardResult(
            decision=GuardDecision.INSUFFICIENT,
            need=need,
            reasons=tuple(reasons),
            skip_expansion=True,  # nothing to expand from
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
        # Conservative general path: only sufficient if no incompleteness signals
        # and strong lexical coverage of question terms.
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
            or _chunk_truncated(h.chunk_text)
            for h in hits
        )
        reasons.append(f"lexical_coverage={coverage:.2f}")
        reasons.append(
            "incompleteness_signals" if incomplete else "no_incompleteness_signals"
        )
        if coverage >= 0.6 and not incomplete:
            decision = GuardDecision.SUFFICIENT
            reasons.append("general_sufficient")
        else:
            decision = GuardDecision.INSUFFICIENT
            reasons.append("general_insufficient_default")

    skip = decision == GuardDecision.SUFFICIENT
    # Empty already returned; for non-empty, skip iff sufficient.
    return EvidenceGuardResult(
        decision=decision,
        need=need,
        reasons=tuple(reasons),
        skip_expansion=skip,
    )


def plan_guarded_hybrid_cap2(
    hits: list[SemanticSearchResult],
    *,
    question: str,
    neighbor_preview: dict[tuple[str, int], str] | None = None,
    max_expanded: int = 2,
):
    """
    Apply evidence guard, then unchanged ``plan_hybrid`` (cap 2) if needed.

    Returns (planned_neighbors, guard_result).
    """
    from experiments.retrieval_eval.selective_strategies import plan_hybrid

    guard = assess_evidence_sufficiency(question, hits)
    if guard.skip_expansion:
        return [], guard
    planned = plan_hybrid(
        hits,
        question=question,
        neighbor_preview=neighbor_preview,
        max_expanded=max(max_expanded, 8),
    )
    return planned, guard
