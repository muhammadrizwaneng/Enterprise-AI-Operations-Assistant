"""Offline answer key for H2 (Q28–Q45). Scoring-only — never import in guard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnswerKey:
    query_id: str
    expected_facts: tuple[str, ...]
    required_any_groups: tuple[tuple[str, ...], ...] = ()
    summary: str = ""


ANSWER_KEYS: dict[str, AnswerKey] = {
    "Q28": AnswerKey(
        "Q28",
        ("before the shipping label",),
        (("shipping label", "before"),),
        "Address changes only before shipping label created",
    ),
    "Q29": AnswerKey(
        "Q29",
        ("30 minutes",),
        (("urgent",),),
        "Urgent first response: 30 minutes",
    ),
    "Q30": AnswerKey(
        "Q30",
        ("1 business day",),
        (("high",),),
        "High priority resolution: 1 business day",
    ),
    "Q31": AnswerKey(
        "Q31",
        ("customer reference", "subject", "category"),
        (("priority", "description"),),
        "Required ticket fields list",
    ),
    "Q32": AnswerKey(
        "Q32",
        ("resolution note",),
        (("do not skip", "not skip", "without a resolution"),),
        "Cannot skip open→closed without resolution note",
    ),
    "Q33": AnswerKey(
        "Q33",
        ("3–5 business days",),
        (("3-5 business days", "3–5 business days", "3 to 5"),),
        "Card refunds typically 3–5 business days",
    ),
    "Q34": AnswerKey(
        "Q34",
        ("5–10 business days",),
        (("5-10 business days", "5–10 business days", "5 to 10"),),
        "Bank transfers may take 5–10 business days",
    ),
    "Q35": AnswerKey(
        "Q35",
        ("entire order",),
        (("novaforge error", "entire order is returned", "whole order"),),
        "Shipping refunded if entire order returned or NovaForge error",
    ),
    "Q36": AnswerKey(
        "Q36",
        ("security@novaforge.example",),
        (),
        "Security incidents email",
    ),
    "Q37": AnswerKey(
        "Q37",
        ("12 months",),
        (("security log", "security logs"),),
        "Security logs retained 12 months",
    ),
    "Q38": AnswerKey(
        "Q38",
        ("not", "card"),
        (
            ("does **not** store full payment card", "does not store full payment card", "not store full payment card"),
        ),
        "NovaForge does not store full payment card numbers",
    ),
    "Q39": AnswerKey(
        "Q39",
        ("50 units",),
        (("50", "operations manager"),),
        "Backorders above 50 units need Ops Manager approval",
    ),
    "Q40": AnswerKey(
        "Q40",
        ("70 lb",),
        (("70", "freight"),),
        "Freight appointments mandatory over 70 lb",
    ),
    "Q41": AnswerKey(
        "Q41",
        ("24 months",),
        (("monitor",),),
        "Monitors standard warranty 24 months",
    ),
    "Q42": AnswerKey(
        "Q42",
        ("sku", "serial", "order number"),
        (("failure", "photo", "diagnostic"),),
        "Hardware replacement collection checklist",
    ),
    "Q43": AnswerKey(
        "Q43",
        ("operations manager",),
        (("pre-approved", "pre-approve", "overtime"),),
        "Overtime pre-approved by Operations Manager",
    ),
    "Q44": AnswerKey(
        "Q44",
        ("4 business hours",),
        (("acknowledge",),),
        "Acknowledge tickets within 4 business hours",
    ),
    "Q45": AnswerKey(
        "Q45",
        ("iso 9241-307",),
        (("class ii", "class 2", "pixel"),),
        "Monitor pixel defects follow ISO 9241-307 Class II",
    ),
    "Q46": AnswerKey(
        "Q46",
        ("verify carrier", "7 calendar days"),
        (
            ("contact the carrier", "contact carrier"),
            ("replacement", "refund"),
        ),
        "Overdue: verify tracking, contact carrier in 1 day, replace/refund after 7 calendar days",
    ),
    "Q47": AnswerKey(
        "Q47",
        ("support agent", "operations manager"),
        (
            ("senior support", "queue lead"),
            ("finance",),
        ),
        "Escalation: Agent → Senior/Queue Lead → Ops Manager → Finance → Admin/Security",
    ),
}


def get_answer_key(query_id: str) -> AnswerKey:
    return ANSWER_KEYS[query_id]
