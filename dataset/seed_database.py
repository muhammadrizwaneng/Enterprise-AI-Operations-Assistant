"""
Seed PostgreSQL with the synthetic enterprise dataset.

Usage (from project root):
    PYTHONPATH=backend:. python dataset/seed_database.py
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Ensure project root and backend/ are importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
for path in (str(PROJECT_ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

load_dotenv(PROJECT_ROOT / ".env")

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Role,
    SupportTicket,
    User,
)
from dataset.generators.constants import DEFAULT_SEED  # noqa: E402
from dataset.generators.export_csv import export_dataset_to_csv  # noqa: E402
from dataset.generators.generate import generate_dataset, summarize_dataset  # noqa: E402


def _parse_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    return UUID(str(value))


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def _parse_decimal(value: str | float | int | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _role_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "name": r["name"],
            "description": r["description"],
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _user_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "role_id": _parse_uuid(r["role_id"]),
            "email": r["email"],
            "full_name": r["full_name"],
            "department": r["department"],
            "is_active": bool(r["is_active"]),
            "hired_at": _parse_dt(r["hired_at"]),
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _customer_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "email": r["email"],
            "full_name": r["full_name"],
            "phone": r["phone"],
            "company_name": r["company_name"],
            "city": r["city"],
            "country": r["country"],
            "address_line": r["address_line"],
            "is_active": bool(r["is_active"]),
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _product_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "sku": r["sku"],
            "name": r["name"],
            "category": r["category"],
            "description": r["description"],
            "unit_price": _parse_decimal(r["unit_price"]),
            "stock_quantity": int(r["stock_quantity"]),
            "is_active": bool(r["is_active"]),
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _order_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "customer_id": _parse_uuid(r["customer_id"]),
            "order_number": r["order_number"],
            "status": r["status"],
            "order_date": _parse_date(r["order_date"]),
            "shipped_date": _parse_date(r["shipped_date"]),
            "delivered_date": _parse_date(r["delivered_date"]),
            "subtotal": _parse_decimal(r["subtotal"]),
            "tax_amount": _parse_decimal(r["tax_amount"]),
            "shipping_amount": _parse_decimal(r["shipping_amount"]),
            "total_amount": _parse_decimal(r["total_amount"]),
            "shipping_address": r["shipping_address"],
            "notes": r["notes"],
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _order_item_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "order_id": _parse_uuid(r["order_id"]),
            "product_id": _parse_uuid(r["product_id"]),
            "quantity": int(r["quantity"]),
            "unit_price": _parse_decimal(r["unit_price"]),
            "line_total": _parse_decimal(r["line_total"]),
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _payment_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "order_id": _parse_uuid(r["order_id"]),
            "payment_reference": r["payment_reference"],
            "amount": _parse_decimal(r["amount"]),
            "method": r["method"],
            "status": r["status"],
            "paid_at": _parse_dt(r["paid_at"]),
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _ticket_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _parse_uuid(r["id"]),
            "ticket_number": r["ticket_number"],
            "customer_id": _parse_uuid(r["customer_id"]),
            "order_id": _parse_uuid(r["order_id"]),
            "assigned_to": _parse_uuid(r["assigned_to"]),
            "subject": r["subject"],
            "description": r["description"],
            "status": r["status"],
            "priority": r["priority"],
            "category": r["category"],
            "opened_at": _parse_dt(r["opened_at"]),
            "resolved_at": _parse_dt(r["resolved_at"]),
            "created_at": _parse_dt(r["created_at"]),
            "updated_at": _parse_dt(r["updated_at"]),
        }
        for r in rows
    ]


def _upsert(
    session,
    model,
    rows: list[dict[str, Any]],
    conflict_column: str,
) -> int:
    """Insert rows; skip conflicts on the given unique column. Returns inserted count."""
    if not rows:
        return 0

    before = session.scalar(select(model.id).limit(1))
    # Count existing by conflict key for a useful inserted estimate
    existing_keys = set(
        session.scalars(select(getattr(model, conflict_column))).all()
    )
    new_rows = [r for r in rows if r[conflict_column] not in existing_keys]
    if not new_rows:
        return 0

    # Batch inserts for performance.
    # Use len(new_rows) for the summary: drivers often return rowcount=-1 for
    # multi-row INSERT ... ON CONFLICT DO NOTHING.
    batch_size = 500
    for i in range(0, len(new_rows), batch_size):
        batch = new_rows[i : i + batch_size]
        stmt = pg_insert(model).values(batch).on_conflict_do_nothing(
            index_elements=[conflict_column]
        )
        session.execute(stmt)
    session.flush()
    _ = before  # reserved for future logging
    return len(new_rows)


def seed_database(
    seed: int | None = None,
    export_csv: bool = True,
) -> dict[str, int]:
    """Create tables, generate data, insert records, optionally export CSVs."""
    seed = seed if seed is not None else int(os.getenv("DATASET_SEED", DEFAULT_SEED))

    print(f"Generating synthetic dataset (seed={seed})...")
    dataset = generate_dataset(seed=seed)
    summary = summarize_dataset(dataset)
    print("Generated in-memory summary:")
    for table, count in summary.items():
        print(f"  {table}: {count}")

    if export_csv:
        paths = export_dataset_to_csv(dataset)
        print(f"CSV files written to: {paths['roles'].parent}")

    print("Creating database tables if missing...")
    Base.metadata.create_all(bind=engine)

    inserted: dict[str, int] = {}
    with SessionLocal() as session:
        try:
            inserted["roles"] = _upsert(session, Role, _role_rows(dataset["roles"]), "name")
            inserted["users"] = _upsert(session, User, _user_rows(dataset["users"]), "email")
            inserted["customers"] = _upsert(
                session, Customer, _customer_rows(dataset["customers"]), "email"
            )
            inserted["products"] = _upsert(
                session, Product, _product_rows(dataset["products"]), "sku"
            )
            inserted["orders"] = _upsert(
                session, Order, _order_rows(dataset["orders"]), "order_number"
            )
            inserted["order_items"] = _upsert(
                session, OrderItem, _order_item_rows(dataset["order_items"]), "id"
            )
            inserted["payments"] = _upsert(
                session, Payment, _payment_rows(dataset["payments"]), "payment_reference"
            )
            inserted["support_tickets"] = _upsert(
                session,
                SupportTicket,
                _ticket_rows(dataset["support_tickets"]),
                "ticket_number",
            )
            session.commit()
        except Exception:
            session.rollback()
            raise

    print("\nSeed complete. Newly inserted records:")
    for table, count in inserted.items():
        print(f"  {table}: {count}")
    print(f"  TOTAL newly inserted: {sum(inserted.values())}")
    print(
        "\nNote: counts of 0 on re-run mean unique keys already existed "
        "(safe idempotent seed)."
    )
    return inserted


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL is not set. Copy .env.example to .env and configure it."
        )
        sys.exit(1)
    seed_database()


if __name__ == "__main__":
    main()
