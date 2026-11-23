"""Safe read-only database browser helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData, Table, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (  # noqa: F401 — register metadata
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Role,
    SupportTicket,
    User,
)

# Only these tables can be browsed (prevents arbitrary SQL / table access)
ALLOWED_TABLES: tuple[str, ...] = (
    "roles",
    "users",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "support_tickets",
)


def list_tables_with_counts(db: Session) -> list[dict[str, Any]]:
    """Return allowed tables with row counts."""
    results: list[dict[str, Any]] = []
    for name in ALLOWED_TABLES:
        table = Base.metadata.tables[name]
        count = int(db.scalar(select(func.count()).select_from(table)) or 0)
        results.append(
            {
                "name": name,
                "count": count,
                "columns": [column.name for column in table.columns],
            }
        )
    return results


def get_table_rows(
    db: Session,
    table_name: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Fetch a page of rows for an allowed table."""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table not allowed: {table_name}")

    table: Table = Base.metadata.tables[table_name]
    total = int(db.scalar(select(func.count()).select_from(table)) or 0)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    rows = db.execute(
        select(table).order_by(table.c.id).limit(limit).offset(offset)
    ).mappings().all()

    columns = [column.name for column in table.columns]
    data = [{col: _serialize(row[col]) for col in columns} for row in rows]

    return {
        "name": table_name,
        "columns": columns,
        "rows": data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_prev": offset > 0,
        "has_next": offset + limit < total,
        "prev_offset": max(0, offset - limit),
        "next_offset": offset + limit,
    }


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    # UUID, Decimal, date/datetime → string for HTML rendering
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if not isinstance(value, (str, int, float, bool)) else value


def reflect_ok(engine: Engine) -> bool:
    """Optional connectivity check."""
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine, only=list(ALLOWED_TABLES))
        return True
    except Exception:
        return False
