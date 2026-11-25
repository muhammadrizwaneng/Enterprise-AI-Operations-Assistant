"""
Controlled neighboring-chunk expansion for RAG context (Phase 4.2 P1 Step 2B).

Semantic search ranking is unchanged. This module only plans same-document
±N neighbors, deduplicates references, and optionally strips character-window
prefix overlap when formatting supporting context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.schemas.search import SemanticSearchResult


class ContextRole(str, Enum):
    RETRIEVED = "retrieved"
    NEIGHBOR_PREVIOUS = "neighbor_previous"
    NEIGHBOR_NEXT = "neighbor_next"


@dataclass(frozen=True, slots=True)
class NeighborPlanItem:
    """A same-document neighbor to load for supporting context."""

    document_name: str
    chunk_index: int
    origin_document_name: str
    origin_chunk_index: int
    direction: str  # "previous" | "next"

    def key(self) -> tuple[str, int]:
        return (self.document_name, self.chunk_index)


@dataclass(frozen=True, slots=True)
class ContextBlock:
    """One block that will be rendered into the LLM CONTEXT."""

    document_name: str
    chunk_index: int
    role: ContextRole
    text: str
    similarity: float | None = None
    origin_chunk_index: int | None = None

    def key(self) -> tuple[str, int]:
        return (self.document_name, self.chunk_index)


def plan_neighbors(
    hits: list[SemanticSearchResult],
    *,
    window: int = 1,
    max_expanded: int = 10,
) -> list[NeighborPlanItem]:
    """
    Plan previous/next neighbors for each retrieved hit.

    - Same ``document_name`` only (never cross documents).
    - Skip indices < 0.
    - Skip keys already present in the original hit set.
    - Cap total unique expanded neighbors at ``max_expanded`` (retrieval order).
    """
    if window < 1 or max_expanded < 1:
        return []
    if not hits:
        return []

    original_keys = {(h.document_name, h.chunk_index) for h in hits}
    planned: list[NeighborPlanItem] = []
    seen_neighbors: set[tuple[str, int]] = set()

    for hit in hits:
        if len(seen_neighbors) >= max_expanded:
            break
        for offset in range(1, window + 1):
            candidates = (
                (hit.chunk_index - offset, "previous"),
                (hit.chunk_index + offset, "next"),
            )
            for neighbor_index, direction in candidates:
                if len(seen_neighbors) >= max_expanded:
                    break
                if neighbor_index < 0:
                    continue
                key = (hit.document_name, neighbor_index)
                if key in original_keys or key in seen_neighbors:
                    continue
                seen_neighbors.add(key)
                planned.append(
                    NeighborPlanItem(
                        document_name=hit.document_name,
                        chunk_index=neighbor_index,
                        origin_document_name=hit.document_name,
                        origin_chunk_index=hit.chunk_index,
                        direction=direction,
                    )
                )
    return planned


def longest_prefix_overlap(
    previous: str,
    current: str,
    *,
    min_overlap: int = 20,
    max_overlap: int = 100,
) -> int:
    """
    Return length of the longest suffix of ``previous`` that equals a prefix
    of ``current``, constrained to ``[min_overlap, max_overlap]``.

    Tuned for the project's 500/100 character chunk windows. Short accidental
    matches below ``min_overlap`` are ignored so unique sentences are kept.
    """
    if not previous or not current:
        return 0
    limit = min(len(previous), len(current), max_overlap)
    for size in range(limit, min_overlap - 1, -1):
        if previous[-size:] == current[:size]:
            return size
    return 0


def strip_prefix_overlap(
    previous: str,
    current: str,
    *,
    min_overlap: int = 20,
    max_overlap: int = 100,
) -> str:
    """Remove confirmed prefix overlap from ``current``; otherwise return as-is."""
    overlap = longest_prefix_overlap(
        previous,
        current,
        min_overlap=min_overlap,
        max_overlap=max_overlap,
    )
    if overlap <= 0:
        return current
    return current[overlap:]


def build_context_blocks(
    hits: list[SemanticSearchResult],
    neighbor_texts: dict[tuple[str, int], str],
    planned: list[NeighborPlanItem],
    *,
    strip_overlap: bool = True,
    min_overlap: int = 20,
    max_overlap: int = 100,
) -> list[ContextBlock]:
    """
    Build ordered context blocks: each retrieved hit, then its available
    previous/next supporting neighbors (only those present in ``neighbor_texts``).
    """
    blocks: list[ContextBlock] = []
    # Track last emitted full text per document for overlap stripping.
    last_full_text_by_doc: dict[str, str] = {}
    emitted_keys: set[tuple[str, int]] = set()

    neighbors_by_origin: dict[tuple[str, int], list[NeighborPlanItem]] = {}
    for item in planned:
        origin = (item.origin_document_name, item.origin_chunk_index)
        neighbors_by_origin.setdefault(origin, []).append(item)

    for hit in hits:
        hit_key = (hit.document_name, hit.chunk_index)
        full_text = hit.chunk_text
        display_text = full_text
        if strip_overlap and hit.document_name in last_full_text_by_doc:
            display_text = strip_prefix_overlap(
                last_full_text_by_doc[hit.document_name],
                full_text,
                min_overlap=min_overlap,
                max_overlap=max_overlap,
            )
        blocks.append(
            ContextBlock(
                document_name=hit.document_name,
                chunk_index=hit.chunk_index,
                role=ContextRole.RETRIEVED,
                text=display_text,
                similarity=hit.similarity,
            )
        )
        emitted_keys.add(hit_key)
        last_full_text_by_doc[hit.document_name] = full_text

        for neighbor in neighbors_by_origin.get(hit_key, []):
            nkey = neighbor.key()
            if nkey in emitted_keys:
                continue
            raw = neighbor_texts.get(nkey)
            if raw is None:
                continue
            display = raw
            if strip_overlap and hit.document_name in last_full_text_by_doc:
                # Prefer overlap vs the origin hit text for next; vs stored
                # previous full text for previous neighbors.
                anchor = (
                    full_text
                    if neighbor.direction == "next"
                    else last_full_text_by_doc[hit.document_name]
                )
                # For previous neighbors, strip overlap of neighbor→origin by
                # comparing neighbor as "previous" chronologically: neighbor
                # comes before origin in the document, so when displaying
                # neighbor first we should not strip using origin. Display
                # previous neighbor with overlap removed from *origin* side
                # only when origin was already shown — here origin is shown
                # first, so strip the neighbor's *suffix* overlap? Safer:
                # only strip prefix overlap when the neighbor is *next*
                # (document order after the last emitted same-doc text).
                if neighbor.direction == "next":
                    display = strip_prefix_overlap(
                        anchor,
                        raw,
                        min_overlap=min_overlap,
                        max_overlap=max_overlap,
                    )
                elif neighbor.chunk_index < hit.chunk_index:
                    # previous neighbor appears after origin in CONTEXT; the
                    # shared overlap is a suffix of neighbor / prefix of
                    # origin. Do not strip neighbor content (would drop the
                    # unique head). Keep full previous-neighbor text.
                    display = raw

            role = (
                ContextRole.NEIGHBOR_NEXT
                if neighbor.direction == "next"
                else ContextRole.NEIGHBOR_PREVIOUS
            )
            blocks.append(
                ContextBlock(
                    document_name=neighbor.document_name,
                    chunk_index=neighbor.chunk_index,
                    role=role,
                    text=display,
                    similarity=None,
                    origin_chunk_index=neighbor.origin_chunk_index,
                )
            )
            emitted_keys.add(nkey)
            # Only advance document cursor for next neighbors (doc order).
            if neighbor.direction == "next":
                last_full_text_by_doc[hit.document_name] = raw

    return blocks


def format_context_blocks(blocks: list[ContextBlock]) -> str:
    """Render CONTEXT blocks. Retrieved keep similarity; neighbors are marked."""
    parts: list[str] = []
    for i, block in enumerate(blocks, start=1):
        if block.role is ContextRole.RETRIEVED:
            header = (
                f"[{i}] role=retrieved "
                f"source={block.document_name} "
                f"chunk_index={block.chunk_index} "
                f"similarity={block.similarity:.4f}"
            )
        else:
            header = (
                f"[{i}] role={block.role.value} "
                f"source={block.document_name} "
                f"chunk_index={block.chunk_index} "
                f"expanded_from_chunk_index={block.origin_chunk_index} "
                f"(supporting context; not an independent semantic match)"
            )
        parts.append(f"{header}\n{block.text}")
    return "\n\n".join(parts)
