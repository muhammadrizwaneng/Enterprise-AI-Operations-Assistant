"""Safe database browser helpers (browse, search, update, delete)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import MetaData, String, Table, cast, delete, func, or_, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (  # noqa: F401 — register metadata
    Conversation,
    Customer,
    Message,
    Order,
    OrderItem,
    Payment,
    Product,
    Role,
    SupportTicket,
    User,
)

# Only these tables can be browsed/edited (prevents arbitrary SQL / table access)
ALLOWED_TABLES: tuple[str, ...] = (
    "roles",
    "users",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "support_tickets",
    "conversations",
    "messages",
)

# Columns users should not edit from the browser UI
READONLY_COLUMNS = frozenset({"id", "created_at"})


def _get_table(table_name: str) -> Table:
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table not allowed: {table_name}")
    return Base.metadata.tables[table_name]


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
    search: str | None = None,
) -> dict[str, Any]:
    """Fetch a page of rows for an allowed table, optionally filtered by search."""
    table = _get_table(table_name)
    q = (search or "").strip()
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    stmt = select(table)
    count_stmt = select(func.count()).select_from(table)

    if q:
        pattern = f"%{q}%"
        filters = [cast(column, String).ilike(pattern) for column in table.columns]
        condition = or_(*filters)
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    rows = db.execute(
        stmt.order_by(table.c.id).limit(limit).offset(offset)
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
        "search": q,
        "has_prev": offset > 0,
        "has_next": offset + limit < total,
        "prev_offset": max(0, offset - limit),
        "next_offset": offset + limit,
    }


def get_row(db: Session, table_name: str, row_id: str) -> dict[str, Any]:
    """Fetch one row by primary key."""
    table = _get_table(table_name)
    pk = _parse_uuid(row_id)
    row = db.execute(select(table).where(table.c.id == pk)).mappings().first()
    if row is None:
        raise ValueError(f"Row not found in {table_name}: {row_id}")

    columns = [column.name for column in table.columns]
    editable = [c for c in columns if c not in READONLY_COLUMNS]
    return {
        "name": table_name,
        "id": str(pk),
        "columns": columns,
        "editable_columns": editable,
        "row": {col: _serialize(row[col]) for col in columns},
        "column_meta": {
            col.name: {
                "nullable": bool(col.nullable),
                "type": type(col.type).__name__,
            }
            for col in table.columns
        },
    }


def update_row(
    db: Session,
    table_name: str,
    row_id: str,
    values: dict[str, Any],
) -> None:
    """Update editable columns for one row."""
    table = _get_table(table_name)
    pk = _parse_uuid(row_id)

    exists = db.execute(select(table.c.id).where(table.c.id == pk)).first()
    if exists is None:
        raise ValueError(f"Row not found in {table_name}: {row_id}")

    payload: dict[str, Any] = {}
    for column in table.columns:
        name = column.name
        if name in READONLY_COLUMNS:
            continue
        if name not in values:
            continue
        raw = values[name]
        payload[name] = _coerce_value(column, raw)

    if "updated_at" in table.c.keys() and "updated_at" not in payload:
        # touch updated_at when present
        payload["updated_at"] = datetime.now().astimezone()

    if not payload:
        raise ValueError("No editable fields provided")

    db.execute(update(table).where(table.c.id == pk).values(**payload))
    db.commit()


def delete_row(db: Session, table_name: str, row_id: str) -> None:
    """Delete one row by primary key."""
    table = _get_table(table_name)
    pk = _parse_uuid(row_id)
    result = db.execute(delete(table).where(table.c.id == pk))
    if result.rowcount == 0:
        raise ValueError(f"Row not found in {table_name}: {row_id}")
    db.commit()


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid row id: {value}") from exc


def _coerce_value(column, raw: Any) -> Any:
    """Convert form/string input into a Python value matching the column type."""
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if text == "" or text.upper() == "NULL":
            if column.nullable:
                return None
            raise ValueError(f"Column '{column.name}' cannot be empty")
        raw = text

    type_name = type(column.type).__name__.lower()

    if "uuid" in type_name:
        return UUID(str(raw))
    if type_name in {"boolean", "bool"}:
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in {"1", "true", "t", "yes", "on"}
    if type_name in {"integer", "smallinteger", "biginteger"}:
        return int(raw)
    if type_name in {"numeric", "float", "real", "decimal"}:
        try:
            return Decimal(str(raw))
        except InvalidOperation as exc:
            raise ValueError(f"Invalid number for '{column.name}'") from exc
    if type_name == "date":
        if isinstance(raw, date) and not isinstance(raw, datetime):
            return raw
        return date.fromisoformat(str(raw)[:10])
    if "datetime" in type_name or type_name in {"timestamp", "timestamptz"}:
        if isinstance(raw, datetime):
            return raw
        text = str(raw).replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    return str(raw)


def _serialize(value: Any) -> Any:
    if value is None:
        return None
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
