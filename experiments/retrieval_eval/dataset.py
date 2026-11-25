"""
Fixed retrieval evaluation dataset (Phase 4.2 P1 Step 2A).

Ground-truth chunk IDs were verified against live ``document_embeddings``
rows and ``dataset/documents/*.md``. Primary and optional supporting
chunks are kept separate.

Ambiguity notes (do not silently rewrite ground truth):
- Q4 ``employee_handbook.md#4`` only contains the truncated start of the
  PTO bullet (``Submit PTO requests``); the ``7 days`` notice period text
  is in ``#5``. Both remain listed as primary per the approved baseline.
- Q5 has no public phone/email in the corpus; ticket-category chunks are
  the contact-path evidence.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChunkRef:
    """Stable chunk identity: exact document_name + chunk_index."""

    document_name: str
    chunk_index: int

    def key(self) -> tuple[str, int]:
        return (self.document_name, self.chunk_index)

    def label(self) -> str:
        return f"{self.document_name}#{self.chunk_index}"


@dataclass(frozen=True, slots=True)
class EvalQuery:
    """One evaluation question with verified ground truth."""

    query_id: str
    question: str
    primary_relevant: tuple[ChunkRef, ...]
    optional_supporting: tuple[ChunkRef, ...] = ()
    notes: str = ""

    def primary_keys(self) -> set[tuple[str, int]]:
        return {c.key() for c in self.primary_relevant}

    def require_primary(self) -> None:
        if not self.primary_relevant:
            raise ValueError(
                f"{self.query_id}: ground truth has no primary relevant chunks"
            )


def _c(document_name: str, chunk_index: int) -> ChunkRef:
    return ChunkRef(document_name=document_name, chunk_index=chunk_index)


EVAL_QUERIES: tuple[EvalQuery, ...] = (
    EvalQuery(
        query_id="Q1",
        question="How long does delivery take?",
        primary_relevant=(
            _c("delivery_policy.md", 1),
            _c("delivery_policy.md", 2),
        ),
        optional_supporting=(),
        notes=(
            "#1: processing times + truncated Standard Ground row; "
            "#2: complete shipping-methods table."
        ),
    ),
    EvalQuery(
        query_id="Q2",
        question="What happens if a package is overdue by seven days?",
        primary_relevant=(
            _c("delivery_policy.md", 4),
            _c("delivery_policy.md", 5),
        ),
        optional_supporting=(),
        notes=(
            "#4: overdue definition / section start; "
            "#5: 7 calendar day lost-package replacement/refund action."
        ),
    ),
    EvalQuery(
        query_id="Q3",
        question="Can I get a refund if my delivery is late?",
        primary_relevant=(
            _c("delivery_policy.md", 4),
            _c("delivery_policy.md", 5),
            _c("refund_policy.md", 3),
        ),
        optional_supporting=(),
        notes=(
            "Photo-evidence text in refund_policy.md#1 is a distractor for "
            "late-delivery eligibility, not primary evidence."
        ),
    ),
    EvalQuery(
        query_id="Q4",
        question="What is the employee PTO notice period?",
        primary_relevant=(
            _c("employee_handbook.md", 4),
            _c("employee_handbook.md", 5),
        ),
        optional_supporting=(),
        notes=(
            "#4 ends mid-bullet without the 7-day period; #5 has the full rule. "
            "Both listed as primary per approved baseline."
        ),
    ),
    EvalQuery(
        query_id="Q5",
        question="How do I contact customer support?",
        primary_relevant=(
            _c("customer_support_guidelines.md", 0),
            _c("customer_support_guidelines.md", 1),
        ),
        optional_supporting=(_c("refund_policy.md", 6),),
        notes=(
            "Ticket categories / support process only. Do not treat unrelated "
            "refund eligibility chunks as relevant. No public phone/email in corpus."
        ),
    ),
    EvalQuery(
        query_id="Q6",
        question="What evidence is required for defective products?",
        primary_relevant=(_c("refund_policy.md", 1),),
        optional_supporting=(_c("delivery_policy.md", 6),),
        notes=(
            "Primary: photographic evidence for defective/incorrect items. "
            "Optional: delivery damaged-in-transit 48-hour photo rule."
        ),
    ),
    EvalQuery(
        query_id="Q7",
        question="What is the refund process?",
        primary_relevant=(_c("refund_policy.md", 6),),
        optional_supporting=(
            _c("refund_policy.md", 0),
            _c("refund_policy.md", 1),
        ),
        notes="Primary: How to Request a Refund procedure (refund_request ticket).",
    ),
)


EVAL_CONFIGS: tuple[dict[str, object], ...] = (
    {
        "name": "rag_current",
        "description": "Current RAG configuration",
        "top_k": 5,
        "min_similarity": 0.5,
    },
    {
        "name": "extended_inspection",
        "description": "Extended retrieval inspection",
        "top_k": 10,
        "min_similarity": 0.5,
    },
)


def get_eval_queries() -> tuple[EvalQuery, ...]:
    for q in EVAL_QUERIES:
        q.require_primary()
    return EVAL_QUERIES
