"""
Step 11 H2 evaluation split (Q28–Q45).

Independent of Q1–Q7 (dev) and Q8–Q27 (Step 9 H1).
Offline annotations only — never passed to guard/runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from experiments.retrieval_eval.dataset import ChunkRef, EvalQuery


def _c(document_name: str, chunk_index: int) -> ChunkRef:
    return ChunkRef(document_name=document_name, chunk_index=chunk_index)


@dataclass(frozen=True, slots=True)
class H2Query:
    query: EvalQuery
    evidence_category: str
    difficulty: str
    expects_neighbor_helpful: bool
    notes: str = ""

    @property
    def query_id(self) -> str:
        return self.query.query_id

    @property
    def question(self) -> str:
        return self.query.question


H2_QUERIES: tuple[H2Query, ...] = (
    H2Query(
        query=EvalQuery(
            query_id="Q28",
            question="When are address changes allowed after an order is placed?",
            primary_relevant=(_c("delivery_policy.md", 5),),
        ),
        evidence_category="general_policy",
        difficulty="easy",
        expects_neighbor_helpful=False,
        notes="Before shipping label creation.",
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q29",
            question="What is the first-response SLA for an urgent support ticket?",
            primary_relevant=(
                _c("customer_support_guidelines.md", 2),
                _c("customer_support_guidelines.md", 3),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q30",
            question="What is the resolution target for high-priority support tickets?",
            primary_relevant=(
                _c("customer_support_guidelines.md", 2),
                _c("customer_support_guidelines.md", 3),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q31",
            question="Which fields must every support ticket include?",
            primary_relevant=(_c("customer_support_guidelines.md", 3),),
        ),
        evidence_category="general_list",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q32",
            question=(
                "Can a ticket move from open directly to closed without a "
                "resolution note?"
            ),
            primary_relevant=(_c("customer_support_guidelines.md", 4),),
        ),
        evidence_category="chunk_boundary_policy",
        difficulty="medium",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q33",
            question="How long do card refunds typically take to appear?",
            primary_relevant=(_c("refund_policy.md", 3),),
        ),
        evidence_category="general_numerical",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q34",
            question="How long may bank-transfer refunds take?",
            primary_relevant=(_c("refund_policy.md", 3),),
        ),
        evidence_category="general_numerical",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q35",
            question="When is shipping cost refunded on a return?",
            primary_relevant=(_c("refund_policy.md", 5),),
        ),
        evidence_category="general_condition",
        difficulty="medium",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q36",
            question="What email should be used for security incidents?",
            primary_relevant=(_c("privacy_policy.md", 7),),
        ),
        evidence_category="general_contact",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q37",
            question="What retention period applies to security logs?",
            primary_relevant=(
                _c("privacy_policy.md", 4),
                _c("privacy_policy.md", 5),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q38",
            question="Does NovaForge store full payment card numbers?",
            primary_relevant=(_c("privacy_policy.md", 1),),
        ),
        evidence_category="general_policy",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q39",
            question=(
                "Backorders above what quantity require Operations Manager "
                "approval?"
            ),
            primary_relevant=(_c("product_documentation.md", 2),),
        ),
        evidence_category="general_numerical",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q40",
            question=(
                "For furniture packages over what weight are freight "
                "appointments mandatory?"
            ),
            primary_relevant=(_c("product_documentation.md", 5),),
        ),
        evidence_category="general_numerical",
        difficulty="medium",
        expects_neighbor_helpful=False,
        notes="May need expansion if #5 ranks poorly; fact is in #5.",
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q41",
            question="What is the standard warranty period for monitors?",
            primary_relevant=(
                _c("product_documentation.md", 5),
                _c("product_documentation.md", 6),
            ),
        ),
        evidence_category="multi_chunk_table",
        difficulty="medium",
        expects_neighbor_helpful=True,
        notes="Warranty table spans #5/#6; neighbor may complete rows.",
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q42",
            question=(
                "What information should agents collect when issuing a "
                "hardware replacement?"
            ),
            primary_relevant=(_c("product_documentation.md", 7),),
        ),
        evidence_category="general_list",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q43",
            question="Who must pre-approve overtime for fulfillment peaks?",
            primary_relevant=(_c("employee_handbook.md", 2),),
        ),
        evidence_category="general_policy",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q44",
            question=(
                "Within how many business hours should support agents "
                "acknowledge new tickets?"
            ),
            primary_relevant=(_c("employee_handbook.md", 4),),
        ),
        evidence_category="general_numerical",
        difficulty="easy",
        expects_neighbor_helpful=False,
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q45",
            question=(
                "What evidence is required for monitor pixel-defect "
                "replacement eligibility?"
            ),
            primary_relevant=(_c("product_documentation.md", 3),),
        ),
        evidence_category="requirement_evidence",
        difficulty="medium",
        expects_neighbor_helpful=False,
        notes="Specialized requirement_evidence phrasing (ISO 9241-307 Class II).",
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q46",
            question=(
                "What steps should support agents follow when a package "
                "is overdue?"
            ),
            primary_relevant=(_c("delivery_policy.md", 5),),
        ),
        evidence_category="procedure",
        difficulty="medium",
        expects_neighbor_helpful=False,
        notes="Specialized procedure need; overdue package agent checklist.",
    ),
    H2Query(
        query=EvalQuery(
            query_id="Q47",
            question="What is the escalation path process for support tickets?",
            primary_relevant=(_c("customer_support_guidelines.md", 6),),
        ),
        evidence_category="procedure",
        difficulty="medium",
        expects_neighbor_helpful=True,
        notes=(
            "Procedure need; escalation list may sit near chunk boundary; "
            "neighbors can add distractors."
        ),
    ),
)


def get_h2_queries() -> tuple[H2Query, ...]:
    qs = H2_QUERIES
    ids = [q.query_id for q in qs]
    if len(ids) != 20:
        raise ValueError(f"Expected 20 H2 questions, got {len(ids)}")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate H2 IDs")
    for q in qs:
        q.query.require_primary()
        n = int(q.query_id[1:])
        if n < 28 or n > 47:
            raise ValueError(f"H2 IDs must be Q28–Q47: {q.query_id}")
    return qs
