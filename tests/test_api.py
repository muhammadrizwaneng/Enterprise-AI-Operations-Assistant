"""API endpoint tests."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert "message" in payload
    assert payload["health"] == "/health"
    assert payload["db_browser"] == "/db"
    assert payload["chat"] == "/api/v1/chat"


def test_db_browser_home(client):
    try:
        response = client.get("/db")
    except OperationalError:
        pytest.skip("PostgreSQL is not available for DB browser test")

    if response.status_code >= 500:
        pytest.skip("Database connection failed; seed the DB to exercise /db")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "customers" in body
    assert "orders" in body
    assert "Database tables" in body


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "app_name" in payload
    assert "environment" in payload


def test_database_stats_endpoint_shape(client):
    """
    Hits /api/v1/database/stats when PostgreSQL is reachable.
    Skips cleanly when the database is not available locally.
    """
    try:
        response = client.get("/api/v1/database/stats")
    except OperationalError:
        pytest.skip("PostgreSQL is not available for stats endpoint test")

    if response.status_code >= 500:
        pytest.skip("Database connection failed; seed the DB to exercise this endpoint")

    assert response.status_code == 200
    payload = response.json()
    for key in (
        "roles",
        "users",
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "support_tickets",
        "total_records",
    ):
        assert key in payload
        assert isinstance(payload[key], int)
        assert payload[key] >= 0
