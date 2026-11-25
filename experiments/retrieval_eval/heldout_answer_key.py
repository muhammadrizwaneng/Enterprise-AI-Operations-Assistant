"""
Offline answer key for held-out Q8–Q27 (Step 9).

CRITICAL: Import this module ONLY from scoring / analysis code.
Never import it from evidence_guard, selective_strategies, or answer-generation
runtime paths.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnswerKey:
    query_id: str
    expected_facts: tuple[str, ...]  # lowercase needles; all should appear ideally
    required_any_groups: tuple[tuple[str, ...], ...] = ()
    # Each group: at least one needle in the group must match
    forbidden_fabrications: tuple[str, ...] = ()
    summary: str = ""


ANSWER_KEYS: dict[str, AnswerKey] = {
    "Q8": AnswerKey(
        query_id="Q8",
        expected_facts=("$150", "free shipping"),
        required_any_groups=(("150.00", "150"),),
        summary="Free shipping at merchandise subtotal of $150.00+",
    ),
    "Q9": AnswerKey(
        query_id="Q9",
        expected_facts=("$9.99",),
        summary="Standard flat shipping below threshold is $9.99",
    ),
    "Q10": AnswerKey(
        query_id="Q10",
        expected_facts=("$1,000", "signature"),
        required_any_groups=(("$1,000.00", "$1000", "1,000", "1000"),),
        summary="Orders above $1,000 require adult signature unless opt-out",
    ),
    "Q11": AnswerKey(
        query_id="Q11",
        expected_facts=("48 hours", "photos"),
        summary="Report visible damage within 48 hours with photos",
    ),
    "Q12": AnswerKey(
        query_id="Q12",
        expected_facts=("30 calendar days",),
        summary="Physical products: 30 calendar days from delivery",
    ),
    "Q13": AnswerKey(
        query_id="Q13",
        expected_facts=("14 calendar days",),
        required_any_groups=(("not been activated", "not activated", "license has not"),),
        summary="Digital: 14 days and only if license not activated",
    ),
    "Q14": AnswerKey(
        query_id="Q14",
        expected_facts=("15%",),
        summary="Restocking fee of 15% may apply",
    ),
    "Q15": AnswerKey(
        query_id="Q15",
        expected_facts=("custom-configured",),
        required_any_groups=(
            ("consumables", "sealed software", "final sale", "services already"),
        ),
        summary="Non-refundable: custom hardware, opened consumables, services, final sale",
    ),
    "Q16": AnswerKey(
        query_id="Q16",
        expected_facts=("$2,500", "operations manager"),
        required_any_groups=(("$2,500", "$2500", "2,500", "2500"),),
        summary="Urgent refund disputes above $2,500 escalate within one business day",
    ),
    "Q17": AnswerKey(
        query_id="Q17",
        expected_facts=("4 business hours",),
        summary="Medium priority first response: 4 business hours",
    ),
    "Q18": AnswerKey(
        query_id="Q18",
        expected_facts=("support agent", "operations manager"),
        required_any_groups=(
            ("senior support", "queue lead"),
            ("finance", "admin"),
        ),
        summary="Agent → Senior/Lead → Ops Manager → Finance → Admin/Security",
    ),
    "Q19": AnswerKey(
        query_id="Q19",
        expected_facts=("open", "resolved", "closed"),
        required_any_groups=(
            ("in_progress", "in progress", "waiting_customer", "waiting customer"),
        ),
        summary="Statuses: open, in_progress, waiting_customer, resolved, closed",
    ),
    "Q20": AnswerKey(
        query_id="Q20",
        expected_facts=("10:00", "16:00"),
        summary="Collaboration hours 10:00–16:00 local, Mon–Fri",
    ),
    "Q21": AnswerKey(
        query_id="Q21",
        expected_facts=("1 hour",),
        summary="Report suspected data leaks within 1 hour",
    ),
    "Q22": AnswerKey(
        query_id="Q22",
        expected_facts=("14 days", "vpn"),
        summary="OS patches within 14 days of release when using VPN for production",
    ),
    "Q23": AnswerKey(
        query_id="Q23",
        expected_facts=("7 years",),
        required_any_groups=(("orders", "invoices"),),
        summary="Orders & invoices retained 7 years",
    ),
    "Q24": AnswerKey(
        query_id="Q24",
        expected_facts=("3 years",),
        summary="Support tickets retained 3 years after closure",
    ),
    "Q25": AnswerKey(
        query_id="Q25",
        expected_facts=("privacy@novaforge.example",),
        summary="Privacy questions: privacy@novaforge.example",
    ),
    "Q26": AnswerKey(
        query_id="Q26",
        expected_facts=("10 units",),
        required_any_groups=(("10 units", "reaches **10**", "reaches 10"),),
        summary="Reorder alert at 10 units",
    ),
    "Q27": AnswerKey(
        query_id="Q27",
        expected_facts=("12 months",),
        summary="Laptops standard warranty 12 months",
    ),
}


def get_answer_key(query_id: str) -> AnswerKey:
    return ANSWER_KEYS[query_id]
