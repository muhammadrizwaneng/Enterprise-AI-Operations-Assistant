"""
Held-out evaluation questions Q8–Q27 (Phase 4.2 P1 Step 9).

Development battery remains Q1–Q7 in ``dataset.py`` (unchanged).
This module is for offline evaluation only. Runtime guard / generation
must never import answer-key fields from ``heldout_answer_key.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from experiments.retrieval_eval.dataset import ChunkRef, EvalQuery


def _c(document_name: str, chunk_index: int) -> ChunkRef:
    return ChunkRef(document_name=document_name, chunk_index=chunk_index)


@dataclass(frozen=True, slots=True)
class HeldOutQuery:
    """Held-out question with offline annotation metadata (not for runtime)."""

    query: EvalQuery
    evidence_category: str
    difficulty: str  # easy | medium | hard
    notes: str = ""

    @property
    def query_id(self) -> str:
        return self.query.query_id

    @property
    def question(self) -> str:
        return self.query.question


# Categories describe evaluation intent only; they are NOT passed to the guard.
HELDOUT_QUERIES: tuple[HeldOutQuery, ...] = (
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q8",
            question="What is the free shipping merchandise threshold?",
            primary_relevant=(
                _c("delivery_policy.md", 2),
                _c("delivery_policy.md", 3),
            ),
        ),
        evidence_category="multi_chunk_numerical",
        difficulty="medium",
        notes="Threshold statement spans truncated #2 into #3.",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q9",
            question="How much is standard flat shipping for below-threshold orders?",
            primary_relevant=(_c("delivery_policy.md", 3),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q10",
            question="When do deliveries require adult signature confirmation?",
            primary_relevant=(_c("delivery_policy.md", 6),),
        ),
        evidence_category="single_chunk_policy_condition",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q11",
            question="How soon must customers report visible damage in transit?",
            primary_relevant=(_c("delivery_policy.md", 6),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q12",
            question="What is the refund request window for standard physical products?",
            primary_relevant=(_c("refund_policy.md", 1),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q13",
            question="What is the refund window for software licenses and digital products?",
            primary_relevant=(_c("refund_policy.md", 1),),
        ),
        evidence_category="single_chunk_condition",
        difficulty="medium",
        notes="Must include 14 days and not-activated condition.",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q14",
            question="What restocking fee percentage may apply to opened unused returns?",
            primary_relevant=(_c("refund_policy.md", 5),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q15",
            question="Which items are listed as non-refundable?",
            primary_relevant=(
                _c("refund_policy.md", 4),
                _c("refund_policy.md", 5),
            ),
        ),
        evidence_category="multi_chunk_list",
        difficulty="hard",
        notes="List starts in #4 and continues into #5 (final sale).",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q16",
            question="When must urgent refund disputes be escalated to an Operations Manager?",
            primary_relevant=(_c("refund_policy.md", 7),),
            optional_supporting=(_c("customer_support_guidelines.md", 2),),
        ),
        evidence_category="single_chunk_threshold",
        difficulty="medium",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q17",
            question="What is the first-response SLA for a medium-priority support ticket?",
            primary_relevant=(
                _c("customer_support_guidelines.md", 2),
                _c("customer_support_guidelines.md", 3),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
        notes="SLA table spans #2/#3.",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q18",
            question="What is the support escalation path from agent to admin?",
            primary_relevant=(
                _c("customer_support_guidelines.md", 6),
                _c("customer_support_guidelines.md", 7),
            ),
        ),
        evidence_category="procedural_neighbor",
        difficulty="medium",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q19",
            question="What ticket status values are used in the support workflow?",
            primary_relevant=(
                _c("customer_support_guidelines.md", 3),
                _c("customer_support_guidelines.md", 4),
            ),
        ),
        evidence_category="multi_chunk_procedure",
        difficulty="hard",
        notes="Status list starts at end of #3 / continues in #4.",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q20",
            question="What are NovaForge collaboration hours for employees?",
            primary_relevant=(_c("employee_handbook.md", 2),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q21",
            question="How quickly must employees report suspected data leaks to IT Security?",
            primary_relevant=(_c("employee_handbook.md", 4),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q22",
            question="How soon must OS patches be applied on company laptops used with VPN?",
            primary_relevant=(
                _c("employee_handbook.md", 5),
                _c("employee_handbook.md", 6),
            ),
        ),
        evidence_category="neighbor_completion",
        difficulty="hard",
        notes="VPN/patch sentence straddles #5/#6 boundary.",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q23",
            question="What retention period applies to orders and invoices?",
            primary_relevant=(_c("privacy_policy.md", 4),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
        notes=(
            "Replaced an unretrievable 'sell personal data' probe; "
            "orders/invoices retention is answerable from #4."
        ),
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q24",
            question="How long are support tickets retained after closure?",
            primary_relevant=(
                _c("privacy_policy.md", 4),
                _c("privacy_policy.md", 5),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q25",
            question="What email should be used for privacy questions?",
            primary_relevant=(
                _c("privacy_policy.md", 6),
                _c("privacy_policy.md", 7),
            ),
        ),
        evidence_category="neighbor_completion",
        difficulty="medium",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q26",
            question="At what stock quantity does Procurement receive an automatic reorder alert?",
            primary_relevant=(_c("product_documentation.md", 2),),
        ),
        evidence_category="single_chunk_numerical",
        difficulty="easy",
    ),
    HeldOutQuery(
        query=EvalQuery(
            query_id="Q27",
            question="What is the standard warranty period for laptops?",
            primary_relevant=(
                _c("product_documentation.md", 5),
                _c("product_documentation.md", 6),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
        notes="Warranty table begins in #5 and continues in #6.",
    ),
)


def get_heldout_queries() -> tuple[HeldOutQuery, ...]:
    ids = [h.query_id for h in HELDOUT_QUERIES]
    if len(ids) != 20:
        raise ValueError(f"Expected 20 held-out questions, found {len(ids)}")
    if len(set(ids)) != 20:
        raise ValueError("Held-out query IDs must be unique")
    for h in HELDOUT_QUERIES:
        h.query.require_primary()
        if not h.query_id.startswith("Q") or int(h.query_id[1:]) < 8:
            raise ValueError(f"Held-out IDs must be Q8+: {h.query_id}")
    return HELDOUT_QUERIES


def get_heldout_eval_queries() -> tuple[EvalQuery, ...]:
    """EvalQuery view for runners (no answer-key fields)."""
    return tuple(h.query for h in get_heldout_queries())
