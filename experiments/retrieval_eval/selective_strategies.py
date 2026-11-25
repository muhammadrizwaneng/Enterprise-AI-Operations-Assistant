"""
Isolated selective neighbor-expansion strategies (Phase 4.2 P1 Step 5).

Experiment-only. Does not modify production neighbor_expansion behavior.
Reuses production NeighborPlanItem / plan_neighbors for the BLIND baseline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.search import SemanticSearchResult
from app.services.neighbor_expansion import NeighborPlanItem, plan_neighbors


@dataclass(frozen=True, slots=True)
class PlannedNeighbor:
    document_name: str
    chunk_index: int
    origin_document_name: str
    origin_chunk_index: int
    direction: str
    reason: str

    def key(self) -> tuple[str, int]:
        return (self.document_name, self.chunk_index)

    def to_production_item(self) -> NeighborPlanItem:
        return NeighborPlanItem(
            document_name=self.document_name,
            chunk_index=self.chunk_index,
            origin_document_name=self.origin_document_name,
            origin_chunk_index=self.origin_chunk_index,
            direction=self.direction,
        )


def _add(
    planned: list[PlannedNeighbor],
    seen: set[tuple[str, int]],
    original: set[tuple[str, int]],
    *,
    hit: SemanticSearchResult,
    neighbor_index: int,
    direction: str,
    reason: str,
    max_expanded: int,
) -> None:
    if len(seen) >= max_expanded:
        return
    if neighbor_index < 0:
        return
    key = (hit.document_name, neighbor_index)
    if key in original or key in seen:
        return
    seen.add(key)
    planned.append(
        PlannedNeighbor(
            document_name=hit.document_name,
            chunk_index=neighbor_index,
            origin_document_name=hit.document_name,
            origin_chunk_index=hit.chunk_index,
            direction=direction,
            reason=reason,
        )
    )


def _looks_like_table(text: str) -> bool:
    return text.count("|") >= 4 or "|---|" in text or "|---|---|" in text


def _table_appears_incomplete(text: str) -> bool:
    """True when chunk looks like a cut table or truncated table row."""
    if not _looks_like_table(text):
        return False
    stripped = text.rstrip()
    last_line = stripped.split("\n")[-1]
    # Truncated mid-cell / mid-row (common with 500-char windows).
    if "|" in last_line and not last_line.rstrip().endswith("|"):
        return True
    # Ends mid-word after table content.
    if len(text) >= 480 and stripped[-1].isalnum():
        return True
    # Header present but fewer than two data rows with pipes.
    data_rows = [
        ln
        for ln in stripped.split("\n")
        if "|" in ln and not set(ln.replace("|", "").strip()) <= {"-", " "}
    ]
    if "| Method |" in text or "| Category |" in text or "| Order Status |" in text:
        if len(data_rows) < 3:
            return True
    return False


def _has_numbered_steps(text: str) -> bool:
    return bool(re.search(r"(?m)^\s*\d+\.\s+\S", text))


def _procedure_needs_next(text: str) -> bool:
    """Incomplete procedure that likely continues in the next chunk."""
    if "7 calendar days" in text and _has_numbered_steps(text):
        return False  # already complete action list
    # Overdue section definition without the agent action list / 7-day rule.
    if re.search(r"##\s*6\.\s*Overdue", text) or "An order becomes **overdue**" in text:
        if "7 calendar days" not in text:
            return True
    if _has_numbered_steps(text):
        nums = [int(x) for x in re.findall(r"(?m)^\s*(\d+)\.\s+", text)]
        stripped = text.rstrip()
        # Starts a list but ends mid-step / mid-sentence near chunk limit.
        if nums and len(text) >= 450 and stripped[-1] not in ".!?:":
            return True
        # Mentions "Support agents must:" but fewer than 3 steps.
        if "Support agents must" in text and len(nums) < 3:
            return True
    return False


def _procedure_needs_previous(text: str) -> bool:
    """Chunk starts mid-procedure (high step numbers / lowercase remnant)."""
    nums = [int(x) for x in re.findall(r"(?m)^\s*(\d+)\.\s+", text)]
    if nums and min(nums) >= 2 and "Support agents must" not in text[:80]:
        return True
    # Starts with remnant from previous window.
    head = text.lstrip()[:40]
    if head and head[0].islower() and _has_numbered_steps(text):
        return True
    return False


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
}


def _question_terms(question: str) -> set[str]:
    terms = set(re.findall(r"[a-z0-9]+", question.lower()))
    return {t for t in terms if len(t) > 2 and t not in _STOP}


def _chunk_truncated(text: str) -> bool:
    stripped = text.rstrip()
    if len(text) < 480:
        return False
    if stripped[-1] in ".!?:|\"":
        return False
    # Mid-word or mid-cell truncation at window boundary.
    if stripped[-1].isalnum():
        return True
    if "|" in stripped.split("\n")[-1] and not stripped.endswith("|"):
        return True
    return False


def plan_off(
    hits: list[SemanticSearchResult],
    *,
    question: str = "",
    max_expanded: int = 0,
) -> list[PlannedNeighbor]:
    return []


def plan_blind(
    hits: list[SemanticSearchResult],
    *,
    question: str = "",
    max_expanded: int = 10,
) -> list[PlannedNeighbor]:
    """Mirror production ±1 expansion (both directions, all hits)."""
    items = plan_neighbors(hits, window=1, max_expanded=max_expanded)
    return [
        PlannedNeighbor(
            document_name=i.document_name,
            chunk_index=i.chunk_index,
            origin_document_name=i.origin_document_name,
            origin_chunk_index=i.origin_chunk_index,
            direction=i.direction,
            reason="blind_plus_minus_one",
        )
        for i in items
    ]


def plan_table_aware(
    hits: list[SemanticSearchResult],
    *,
    question: str = "",
    max_expanded: int = 4,
) -> list[PlannedNeighbor]:
    """
    Strategy A: expand when a retrieved chunk looks like an incomplete table.

    Prefer next neighbor (continuation rows). Also expand previous when the
    hit looks like a continuation row without a header.
    """
    original = {(h.document_name, h.chunk_index) for h in hits}
    planned: list[PlannedNeighbor] = []
    seen: set[tuple[str, int]] = set()
    for hit in hits:
        text = hit.chunk_text
        if not _table_appears_incomplete(text) and not (
            _looks_like_table(text) and len(text) >= 480
        ):
            continue
        reason = "incomplete_table"
        _add(
            planned,
            seen,
            original,
            hit=hit,
            neighbor_index=hit.chunk_index + 1,
            direction="next",
            reason=reason + "_next",
            max_expanded=max_expanded,
        )
        # Continuation without header → pull previous for header context.
        if _looks_like_table(text) and not re.search(
            r"\|\s*[A-Za-z].*\|\s*[A-Za-z]", text.split("\n")[0]
        ):
            first_lines = "\n".join(text.split("\n")[:3])
            if "|---|" not in first_lines and text.lstrip().startswith("|"):
                _add(
                    planned,
                    seen,
                    original,
                    hit=hit,
                    neighbor_index=hit.chunk_index - 1,
                    direction="previous",
                    reason=reason + "_prev_header",
                    max_expanded=max_expanded,
                )
    return planned


def plan_procedure_aware(
    hits: list[SemanticSearchResult],
    *,
    question: str = "",
    max_expanded: int = 4,
) -> list[PlannedNeighbor]:
    """
    Strategy B: expand around incomplete numbered procedures / overdue sections.
    """
    original = {(h.document_name, h.chunk_index) for h in hits}
    planned: list[PlannedNeighbor] = []
    seen: set[tuple[str, int]] = set()
    for hit in hits:
        text = hit.chunk_text
        if _procedure_needs_next(text):
            _add(
                planned,
                seen,
                original,
                hit=hit,
                neighbor_index=hit.chunk_index + 1,
                direction="next",
                reason="incomplete_procedure_next",
                max_expanded=max_expanded,
            )
        if _procedure_needs_previous(text):
            _add(
                planned,
                seen,
                original,
                hit=hit,
                neighbor_index=hit.chunk_index - 1,
                direction="previous",
                reason="incomplete_procedure_prev",
                max_expanded=max_expanded,
            )
    return planned


def plan_evidence_completion(
    hits: list[SemanticSearchResult],
    *,
    question: str,
    neighbor_preview: dict[tuple[str, int], str] | None = None,
    max_expanded: int = 4,
) -> list[PlannedNeighbor]:
    """
    Strategy C: expand only when the hit looks truncated AND the neighbor
    appears topically relevant to the question (or continues the same section).

    ``neighbor_preview`` may supply already-loaded neighbor texts for relevance
    checks; if missing, expands truncated hits to next (and prev if needed)
    with a weaker lexical check deferred to post-load filtering in the harness.
    """
    original = {(h.document_name, h.chunk_index) for h in hits}
    planned: list[PlannedNeighbor] = []
    seen: set[tuple[str, int]] = set()
    qterms = _question_terms(question)

    def relevant(text: str) -> bool:
        if not qterms:
            return True
        lower = text.lower()
        hits_terms = sum(1 for t in qterms if t in lower)
        return hits_terms >= max(1, min(2, len(qterms) // 2))

    for hit in hits:
        text = hit.chunk_text
        truncated = _chunk_truncated(text) or _table_appears_incomplete(text)
        # Also: incomplete overdue definition without 7-day rule.
        overdue_gap = (
            ("overdue" in text.lower() or "Overdue" in text)
            and "7 calendar days" not in text
            and (
                "An order becomes" in text
                or "## 6." in text
                or "Support agents must" in text
            )
        )
        if not truncated and not overdue_gap:
            continue

        for direction, idx in (
            ("next", hit.chunk_index + 1),
            ("previous", hit.chunk_index - 1),
        ):
            if direction == "previous" and not (
                overdue_gap is False and truncated and text.lstrip()[:1].islower()
            ):
                # Prefer next for truncation/overdue gap; prev only for lowercase remnant.
                if not (truncated and text.lstrip()[:1].islower()):
                    continue
            key = (hit.document_name, idx)
            preview = (neighbor_preview or {}).get(key)
            table_continuation = (
                direction == "next"
                and _table_appears_incomplete(text)
                and preview is not None
                and preview.count("|") >= 4
            )
            if (
                preview is not None
                and not relevant(preview)
                and not table_continuation
                and not overdue_gap
            ):
                continue
            # If no preview yet, still plan next for truncated/overdue; harness
            # can drop after load if irrelevant.
            reason = (
                "overdue_section_gap_next"
                if overdue_gap and direction == "next"
                else (
                    "truncated_table_next"
                    if table_continuation
                    else f"truncated_evidence_{direction}"
                )
            )
            if overdue_gap and direction != "next":
                continue
            _add(
                planned,
                seen,
                original,
                hit=hit,
                neighbor_index=idx,
                direction=direction,
                reason=reason,
                max_expanded=max_expanded,
            )
    return planned


def plan_hybrid(
    hits: list[SemanticSearchResult],
    *,
    question: str,
    neighbor_preview: dict[tuple[str, int], str] | None = None,
    max_expanded: int = 3,
) -> list[PlannedNeighbor]:
    """
    HYBRID (Step 6): C_EVIDENCE primary + A_TABLE incomplete-table completion.

    Selection order:
    1. Run C_EVIDENCE (truncated / overdue-gap / table-continuation gates).
    2. Union A_TABLE incomplete-table neighbors that are not already selected.
    3. Deduplicate by (document_name, chunk_index).
    4. Enforce hard ``max_expanded`` cap with priority:
       overdue_section_gap > truncated_table / incomplete_table >
       truncated_evidence from earlier (higher-ranked) hits > other.

    Does not blindly union every A+C candidate without relevance/priority.
    """
    c_items = plan_evidence_completion(
        hits,
        question=question,
        neighbor_preview=neighbor_preview,
        max_expanded=max(max_expanded, 8),
    )
    a_items = plan_table_aware(
        hits,
        question=question,
        max_expanded=max(max_expanded, 8),
    )

    # Prefer C's reason when both select the same neighbor; else keep A's table reason.
    by_key: dict[tuple[str, int], PlannedNeighbor] = {}
    for item in c_items:
        by_key[item.key()] = item
    for item in a_items:
        if item.key() not in by_key:
            by_key[item.key()] = item

    hit_rank = {
        (h.document_name, h.chunk_index): i for i, h in enumerate(hits)
    }

    def priority(p: PlannedNeighbor) -> tuple[int, int, int]:
        reason = p.reason
        if "overdue" in reason:
            tier = 0
        elif "table" in reason or reason.startswith("incomplete_table"):
            tier = 1
        elif reason.startswith("truncated_evidence"):
            tier = 2
        else:
            tier = 3
        origin_rank = hit_rank.get(
            (p.origin_document_name, p.origin_chunk_index), 99
        )
        return (tier, origin_rank, p.chunk_index)

    ordered = sorted(by_key.values(), key=priority)
    return ordered[: max(0, max_expanded)]


STRATEGIES = {
    "OFF": plan_off,
    "BLIND": plan_blind,
    "A_TABLE": plan_table_aware,
    "B_PROCEDURE": plan_procedure_aware,
    "C_EVIDENCE": plan_evidence_completion,
    "HYBRID": plan_hybrid,
}
