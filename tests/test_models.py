"""Tests for SQLAlchemy models and relationships."""

from __future__ import annotations

from sqlalchemy import inspect

from app.db.base import Base
from app.models import (
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Role,
    SupportTicket,
    User,
)


EXPECTED_TABLES = {
    "roles",
    "users",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "support_tickets",
}


def test_all_models_registered_on_metadata():
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables.keys()))


def test_uuid_primary_keys():
    for table_name in EXPECTED_TABLES:
        table = Base.metadata.tables[table_name]
        pk_cols = list(table.primary_key.columns)
        assert len(pk_cols) == 1
        assert pk_cols[0].name == "id"


def test_foreign_key_relationships():
    mapper = inspect(User)
    assert "role" in mapper.relationships
    assert "assigned_tickets" in mapper.relationships

    order_mapper = inspect(Order)
    assert "customer" in order_mapper.relationships
    assert "items" in order_mapper.relationships
    assert "payments" in order_mapper.relationships

    item_mapper = inspect(OrderItem)
    assert "order" in item_mapper.relationships
    assert "product" in item_mapper.relationships

    ticket_mapper = inspect(SupportTicket)
    assert "customer" in ticket_mapper.relationships
    assert "order" in ticket_mapper.relationships
    assert "assignee" in ticket_mapper.relationships


def test_unique_constraints_present():
    assert any(c.unique for c in Role.__table__.columns if c.name == "name")
    assert any(c.unique for c in User.__table__.columns if c.name == "email")
    assert any(c.unique for c in Customer.__table__.columns if c.name == "email")
    assert any(c.unique for c in Product.__table__.columns if c.name == "sku")
    assert any(c.unique for c in Order.__table__.columns if c.name == "order_number")
    assert any(
        c.unique for c in Payment.__table__.columns if c.name == "payment_reference"
    )
    assert any(
        c.unique for c in SupportTicket.__table__.columns if c.name == "ticket_number"
    )


def test_order_item_fk_targets():
    targets = {
        (fk.column.table.name, fk.column.name)
        for fk in OrderItem.__table__.foreign_keys
    }
    assert ("orders", "id") in targets
    assert ("products", "id") in targets
