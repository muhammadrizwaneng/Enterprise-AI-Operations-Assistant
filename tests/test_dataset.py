"""Tests for synthetic dataset generation and consistency."""

from __future__ import annotations

from decimal import Decimal

from dataset.generators.constants import (
    CUSTOMER_COUNT,
    ORDER_COUNT,
    ORDER_ITEM_MAX,
    ORDER_ITEM_MIN,
    PAYMENT_MAX,
    PAYMENT_MIN,
    PRODUCT_COUNT,
    ROLE_COUNT,
    SUPPORT_TICKET_COUNT,
    USER_COUNT,
)
from dataset.generators.generate import generate_dataset, summarize_dataset


def test_dataset_counts(dataset):
    summary = summarize_dataset(dataset)
    assert summary["roles"] == ROLE_COUNT
    assert summary["users"] == USER_COUNT
    assert summary["customers"] == CUSTOMER_COUNT
    assert summary["products"] == PRODUCT_COUNT
    assert summary["orders"] == ORDER_COUNT
    assert ORDER_ITEM_MIN <= summary["order_items"] <= ORDER_ITEM_MAX
    assert PAYMENT_MIN <= summary["payments"] <= PAYMENT_MAX
    assert summary["support_tickets"] == SUPPORT_TICKET_COUNT


def test_dataset_is_deterministic():
    a = generate_dataset(seed=42)
    b = generate_dataset(seed=42)
    assert summarize_dataset(a) == summarize_dataset(b)
    assert a["orders"][0]["order_number"] == b["orders"][0]["order_number"]
    assert a["customers"][0]["email"] == b["customers"][0]["email"]
    assert a["products"][0]["sku"] == b["products"][0]["sku"]


def test_unique_natural_keys(dataset):
    assert len({r["name"] for r in dataset["roles"]}) == len(dataset["roles"])
    assert len({u["email"] for u in dataset["users"]}) == len(dataset["users"])
    assert len({c["email"] for c in dataset["customers"]}) == len(dataset["customers"])
    assert len({p["sku"] for p in dataset["products"]}) == len(dataset["products"])
    assert len({o["order_number"] for o in dataset["orders"]}) == len(dataset["orders"])
    assert len({p["payment_reference"] for p in dataset["payments"]}) == len(
        dataset["payments"]
    )
    assert len({t["ticket_number"] for t in dataset["support_tickets"]}) == len(
        dataset["support_tickets"]
    )


def test_foreign_key_integrity(dataset):
    role_ids = {r["id"] for r in dataset["roles"]}
    user_ids = {u["id"] for u in dataset["users"]}
    customer_ids = {c["id"] for c in dataset["customers"]}
    product_ids = {p["id"] for p in dataset["products"]}
    order_ids = {o["id"] for o in dataset["orders"]}

    for user in dataset["users"]:
        assert user["role_id"] in role_ids

    for order in dataset["orders"]:
        assert order["customer_id"] in customer_ids

    for item in dataset["order_items"]:
        assert item["order_id"] in order_ids
        assert item["product_id"] in product_ids

    for payment in dataset["payments"]:
        assert payment["order_id"] in order_ids

    for ticket in dataset["support_tickets"]:
        assert ticket["customer_id"] in customer_ids
        if ticket["order_id"] is not None:
            assert ticket["order_id"] in order_ids
        if ticket["assigned_to"] is not None:
            assert ticket["assigned_to"] in user_ids


def test_order_totals_match_items(dataset):
    items_by_order: dict[str, list] = {}
    for item in dataset["order_items"]:
        items_by_order.setdefault(item["order_id"], []).append(item)

    for order in dataset["orders"]:
        items = items_by_order[order["id"]]
        subtotal = sum((Decimal(i["line_total"]) for i in items), Decimal("0.00"))
        assert subtotal == Decimal(order["subtotal"])
        expected_total = (
            Decimal(order["subtotal"])
            + Decimal(order["tax_amount"])
            + Decimal(order["shipping_amount"])
        )
        assert expected_total == Decimal(order["total_amount"])


def test_order_statuses_include_edge_cases(dataset):
    statuses = {o["status"] for o in dataset["orders"]}
    for required in ("pending", "delivered", "cancelled", "returned", "overdue"):
        assert required in statuses
