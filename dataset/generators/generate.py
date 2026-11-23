"""Generate a consistent, deterministic synthetic enterprise dataset."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from faker import Faker

from dataset.generators.constants import (
    CUSTOMER_COUNT,
    DEFAULT_SEED,
    DEPARTMENTS,
    ORDER_COUNT,
    ORDER_ITEM_MAX,
    ORDER_ITEM_MIN,
    ORDER_STATUS_WEIGHTS,
    ORDER_STATUSES,
    PAYMENT_MAX,
    PAYMENT_METHODS,
    PAYMENT_MIN,
    PAYMENT_STATUSES,
    PRODUCT_CATEGORIES,
    PRODUCT_COUNT,
    ROLE_COUNT,
    ROLE_DEFINITIONS,
    SHIPPING_FLAT,
    SHIPPING_FREE_THRESHOLD,
    SUPPORT_TICKET_COUNT,
    TAX_RATE,
    TICKET_CATEGORIES,
    TICKET_PRIORITIES,
    TICKET_PRIORITY_WEIGHTS,
    TICKET_STATUSES,
    USER_COUNT,
)


def _money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _seeded_uuid(rng: random.Random) -> uuid.UUID:
    """Create a UUID v4-compatible value from a seeded RNG (deterministic)."""
    return uuid.UUID(int=rng.getrandbits(128), version=4)


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def generate_dataset(seed: int = DEFAULT_SEED) -> dict[str, list[dict[str, Any]]]:
    """
    Build the full synthetic dataset in memory.

    Returns a dict keyed by table name with lists of row dicts.
    Foreign-key relationships and financial totals are internally consistent.
    """
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)
    fake.seed_instance(seed)

    now = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    start_date = date(2024, 1, 1)

    # --- Roles ---
    roles: list[dict[str, Any]] = []
    for name, description in ROLE_DEFINITIONS[:ROLE_COUNT]:
        created = _utc(fake.date_time_between(start_date=datetime(2023, 1, 1), end_date=now))
        roles.append(
            {
                "id": str(_seeded_uuid(rng)),
                "name": name,
                "description": description,
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )
    role_ids = {r["name"]: r["id"] for r in roles}

    # --- Users ---
    users: list[dict[str, Any]] = []
    used_emails: set[str] = set()
    role_cycle = ["admin"] + ["operations_manager"] * 3 + ["support_agent"] * 16
    for i in range(USER_COUNT):
        email = fake.unique.company_email().lower()
        while email in used_emails:
            email = fake.unique.company_email().lower()
        used_emails.add(email)
        hired = _utc(
            fake.date_time_between(start_date=datetime(2020, 1, 1), end_date=now)
        )
        role_name = role_cycle[i % len(role_cycle)]
        users.append(
            {
                "id": str(_seeded_uuid(rng)),
                "role_id": role_ids[role_name],
                "email": email,
                "full_name": fake.name(),
                "department": rng.choice(DEPARTMENTS),
                "is_active": rng.random() > 0.05,
                "hired_at": hired.isoformat(),
                "created_at": hired.isoformat(),
                "updated_at": hired.isoformat(),
            }
        )
    support_agent_ids = [
        u["id"]
        for u in users
        if u["role_id"] == role_ids["support_agent"] and u["is_active"]
    ]
    if not support_agent_ids:
        support_agent_ids = [u["id"] for u in users]

    # --- Customers ---
    customers: list[dict[str, Any]] = []
    for _ in range(CUSTOMER_COUNT):
        email = fake.unique.email().lower()
        while email in used_emails:
            email = fake.unique.email().lower()
        used_emails.add(email)
        created = _utc(
            fake.date_time_between(start_date=datetime(2023, 6, 1), end_date=now)
        )
        customers.append(
            {
                "id": str(_seeded_uuid(rng)),
                "email": email,
                "full_name": fake.name(),
                "phone": fake.phone_number()[:40],
                "company_name": fake.company() if rng.random() > 0.35 else None,
                "city": fake.city(),
                "country": fake.country()[:100],
                "address_line": fake.street_address(),
                "is_active": rng.random() > 0.08,
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )
    customer_ids = [c["id"] for c in customers]

    # --- Products ---
    products: list[dict[str, Any]] = []
    used_skus: set[str] = set()
    for i in range(PRODUCT_COUNT):
        category = PRODUCT_CATEGORIES[i % len(PRODUCT_CATEGORIES)]
        sku = f"SKU-{category[:3].upper()}-{1000 + i:04d}"
        while sku in used_skus:
            sku = f"SKU-{category[:3].upper()}-{rng.randint(1000, 9999)}"
        used_skus.add(sku)
        unit_price = _money(rng.uniform(19.99, 2499.99))
        created = _utc(
            fake.date_time_between(start_date=datetime(2023, 1, 1), end_date=now)
        )
        products.append(
            {
                "id": str(_seeded_uuid(rng)),
                "sku": sku,
                "name": f"{fake.word().title()} {category.rstrip('s')} {100 + i}",
                "category": category,
                "description": fake.sentence(nb_words=12),
                "unit_price": str(unit_price),
                "stock_quantity": rng.randint(0, 500),
                "is_active": rng.random() > 0.1,
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )
    product_by_id = {p["id"]: p for p in products}
    product_ids = list(product_by_id.keys())

    # --- Orders + Order Items ---
    # Plan items per order so total items land in [ORDER_ITEM_MIN, ORDER_ITEM_MAX]
    target_items = rng.randint(ORDER_ITEM_MIN, ORDER_ITEM_MAX)
    base = target_items // ORDER_COUNT
    remainder = target_items % ORDER_COUNT
    items_per_order = [base + (1 if i < remainder else 0) for i in range(ORDER_COUNT)]
    # Ensure every order has at least 1 item; redistribute if base was 0
    if base == 0:
        items_per_order = [1] * ORDER_COUNT
        extra = target_items - ORDER_COUNT
        for i in range(max(0, extra)):
            items_per_order[i % ORDER_COUNT] += 1

    orders: list[dict[str, Any]] = []
    order_items: list[dict[str, Any]] = []
    used_order_numbers: set[str] = set()

    for idx in range(ORDER_COUNT):
        order_id = str(_seeded_uuid(rng))
        customer = customers[rng.randrange(len(customers))]
        order_date = fake.date_between(start_date=start_date, end_date=now.date())
        status = rng.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0]

        shipped_date = None
        delivered_date = None
        if status in {"shipped", "delivered", "returned", "overdue"}:
            shipped_date = order_date + timedelta(days=rng.randint(1, 5))
        if status == "delivered":
            delivered_date = (shipped_date or order_date) + timedelta(days=rng.randint(1, 7))
        if status == "returned":
            delivered_date = (shipped_date or order_date) + timedelta(days=rng.randint(1, 7))
        if status == "overdue":
            # Overdue: past expected delivery with no delivery date
            shipped_date = order_date + timedelta(days=rng.randint(1, 3))
            delivered_date = None

        order_number = f"ORD-{order_date.strftime('%Y%m%d')}-{idx + 1:05d}"
        while order_number in used_order_numbers:
            order_number = f"ORD-{order_date.strftime('%Y%m%d')}-{rng.randint(1, 99999):05d}"
        used_order_numbers.add(order_number)

        # Build line items
        n_items = max(1, items_per_order[idx])
        chosen_products = rng.sample(product_ids, k=min(n_items, len(product_ids)))
        # If we need more lines than unique products, allow reuse with different qty
        while len(chosen_products) < n_items:
            chosen_products.append(rng.choice(product_ids))

        subtotal = Decimal("0.00")
        for product_id in chosen_products:
            product = product_by_id[product_id]
            qty = rng.randint(1, 5)
            unit_price = Decimal(product["unit_price"])
            line_total = _money(unit_price * qty)
            subtotal += line_total
            created_item = _utc(
                datetime.combine(order_date, datetime.min.time())
                + timedelta(hours=rng.randint(0, 20))
            )
            order_items.append(
                {
                    "id": str(_seeded_uuid(rng)),
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": qty,
                    "unit_price": str(unit_price),
                    "line_total": str(line_total),
                    "created_at": created_item.isoformat(),
                    "updated_at": created_item.isoformat(),
                }
            )

        tax_amount = _money(subtotal * Decimal(str(TAX_RATE)))
        shipping_amount = (
            Decimal("0.00")
            if float(subtotal) >= SHIPPING_FREE_THRESHOLD
            else _money(SHIPPING_FLAT)
        )
        if status == "cancelled":
            # Cancelled orders still keep computed totals for audit consistency
            pass
        total_amount = _money(subtotal + tax_amount + shipping_amount)

        created = _utc(
            datetime.combine(order_date, datetime.min.time())
            + timedelta(hours=rng.randint(8, 18), minutes=rng.randint(0, 59))
        )
        orders.append(
            {
                "id": order_id,
                "customer_id": customer["id"],
                "order_number": order_number,
                "status": status,
                "order_date": order_date.isoformat(),
                "shipped_date": shipped_date.isoformat() if shipped_date else None,
                "delivered_date": delivered_date.isoformat() if delivered_date else None,
                "subtotal": str(subtotal),
                "tax_amount": str(tax_amount),
                "shipping_amount": str(shipping_amount),
                "total_amount": str(total_amount),
                "shipping_address": (
                    f"{customer['address_line']}, {customer['city']}, {customer['country']}"
                ),
                "notes": fake.sentence() if rng.random() > 0.7 else None,
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )

    payable_orders = [
        o
        for o in orders
        if o["status"] not in {"cancelled"}
    ]
    # Always leave some orders without payment (pending payment)
    payment_count = rng.randint(PAYMENT_MIN, min(PAYMENT_MAX, len(payable_orders)))
    # Prefer non-cancelled; if not enough, fill from all orders
    payment_candidates = payable_orders[:]
    rng.shuffle(payment_candidates)
    if len(payment_candidates) < payment_count:
        extras = [o for o in orders if o not in payment_candidates]
        payment_candidates.extend(extras[: payment_count - len(payment_candidates)])
    selected_for_payment = payment_candidates[:payment_count]

    # --- Payments ---
    payments: list[dict[str, Any]] = []
    used_payment_refs: set[str] = set()
    for i, order in enumerate(selected_for_payment):
        status = rng.choice(PAYMENT_STATUSES)
        # Align payment status somewhat with order status
        if order["status"] == "delivered":
            status = rng.choices(
                ["completed", "refunded", "partially_refunded"],
                weights=[85, 8, 7],
                k=1,
            )[0]
        elif order["status"] == "returned":
            status = rng.choice(["refunded", "partially_refunded", "completed"])
        elif order["status"] == "pending":
            status = rng.choice(["pending", "failed", "completed"])

        amount = Decimal(order["total_amount"])
        if status == "partially_refunded":
            amount = _money(amount * Decimal(str(rng.uniform(0.3, 0.9))))

        paid_at = None
        order_dt = datetime.fromisoformat(order["created_at"])
        if status in {"completed", "refunded", "partially_refunded"}:
            paid_at = _utc(order_dt + timedelta(hours=rng.randint(1, 72)))

        pref = f"PAY-{order['order_number'][-8:]}-{i + 1:04d}"
        while pref in used_payment_refs:
            pref = f"PAY-{rng.randint(10000000, 99999999)}-{i + 1:04d}"
        used_payment_refs.add(pref)

        created = _utc(order_dt + timedelta(minutes=rng.randint(5, 180)))
        payments.append(
            {
                "id": str(_seeded_uuid(rng)),
                "order_id": order["id"],
                "payment_reference": pref,
                "amount": str(amount),
                "method": rng.choice(PAYMENT_METHODS),
                "status": status,
                "paid_at": paid_at.isoformat() if paid_at else None,
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )

    # --- Support tickets ---
    tickets: list[dict[str, Any]] = []
    used_ticket_numbers: set[str] = set()
    for i in range(SUPPORT_TICKET_COUNT):
        customer_id = rng.choice(customer_ids)
        # ~60% of tickets linked to an order from the same customer when possible
        order_id = None
        customer_orders = [o for o in orders if o["customer_id"] == customer_id]
        if customer_orders and rng.random() < 0.6:
            order_id = rng.choice(customer_orders)["id"]
        elif rng.random() < 0.15:
            order_id = rng.choice(orders)["id"]

        status = rng.choice(TICKET_STATUSES)
        priority = rng.choices(
            TICKET_PRIORITIES, weights=TICKET_PRIORITY_WEIGHTS, k=1
        )[0]
        opened_at = _utc(
            fake.date_time_between(start_date=datetime(2024, 3, 1), end_date=now)
        )
        resolved_at = None
        if status in {"resolved", "closed"}:
            resolved_at = _utc(opened_at + timedelta(hours=rng.randint(2, 240)))

        ticket_number = f"TKT-{opened_at.strftime('%Y%m%d')}-{i + 1:05d}"
        while ticket_number in used_ticket_numbers:
            ticket_number = f"TKT-{opened_at.strftime('%Y%m%d')}-{rng.randint(1, 99999):05d}"
        used_ticket_numbers.add(ticket_number)

        assigned_to = None
        if rng.random() > 0.12:
            assigned_to = rng.choice(support_agent_ids)

        category = rng.choice(TICKET_CATEGORIES)
        tickets.append(
            {
                "id": str(_seeded_uuid(rng)),
                "ticket_number": ticket_number,
                "customer_id": customer_id,
                "order_id": order_id,
                "assigned_to": assigned_to,
                "subject": f"{category.replace('_', ' ').title()}: {fake.sentence(nb_words=6)}",
                "description": fake.paragraph(nb_sentences=4),
                "status": status,
                "priority": priority,
                "category": category,
                "opened_at": opened_at.isoformat(),
                "resolved_at": resolved_at.isoformat() if resolved_at else None,
                "created_at": opened_at.isoformat(),
                "updated_at": (resolved_at or opened_at).isoformat(),
            }
        )

    dataset = {
        "roles": roles,
        "users": users,
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "support_tickets": tickets,
    }

    _validate_dataset(dataset)
    return dataset


def _validate_dataset(dataset: dict[str, list[dict[str, Any]]]) -> None:
    """Raise AssertionError if referential or financial integrity fails."""
    role_ids = {r["id"] for r in dataset["roles"]}
    user_ids = {u["id"] for u in dataset["users"]}
    customer_ids = {c["id"] for c in dataset["customers"]}
    product_ids = {p["id"] for p in dataset["products"]}
    order_ids = {o["id"] for o in dataset["orders"]}

    assert len({r["name"] for r in dataset["roles"]}) == len(dataset["roles"])
    assert len({u["email"] for u in dataset["users"]}) == len(dataset["users"])
    assert len({c["email"] for c in dataset["customers"]}) == len(dataset["customers"])
    assert len({p["sku"] for p in dataset["products"]}) == len(dataset["products"])
    assert len({o["order_number"] for o in dataset["orders"]}) == len(dataset["orders"])

    for user in dataset["users"]:
        assert user["role_id"] in role_ids

    for order in dataset["orders"]:
        assert order["customer_id"] in customer_ids

    items_by_order: dict[str, list[dict[str, Any]]] = {}
    for item in dataset["order_items"]:
        assert item["order_id"] in order_ids
        assert item["product_id"] in product_ids
        items_by_order.setdefault(item["order_id"], []).append(item)

    for order in dataset["orders"]:
        items = items_by_order.get(order["id"], [])
        assert items, f"Order {order['order_number']} has no items"
        computed = sum((Decimal(i["line_total"]) for i in items), Decimal("0.00"))
        assert _money(computed) == Decimal(order["subtotal"]), (
            f"Subtotal mismatch for {order['order_number']}: "
            f"{computed} != {order['subtotal']}"
        )
        expected_total = _money(
            Decimal(order["subtotal"])
            + Decimal(order["tax_amount"])
            + Decimal(order["shipping_amount"])
        )
        assert expected_total == Decimal(order["total_amount"])

    for payment in dataset["payments"]:
        assert payment["order_id"] in order_ids

    for ticket in dataset["support_tickets"]:
        assert ticket["customer_id"] in customer_ids
        if ticket["order_id"] is not None:
            assert ticket["order_id"] in order_ids
        if ticket["assigned_to"] is not None:
            assert ticket["assigned_to"] in user_ids

    assert ORDER_ITEM_MIN <= len(dataset["order_items"]) <= ORDER_ITEM_MAX
    assert PAYMENT_MIN <= len(dataset["payments"]) <= PAYMENT_MAX


def summarize_dataset(dataset: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """Return table -> count summary."""
    return {name: len(rows) for name, rows in dataset.items()}


if __name__ == "__main__":
    data = generate_dataset()
    summary = summarize_dataset(data)
    print("Generated dataset summary:")
    for table, count in summary.items():
        print(f"  {table}: {count}")
