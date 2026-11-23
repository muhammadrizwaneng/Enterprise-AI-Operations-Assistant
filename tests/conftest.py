"""Pytest fixtures and path setup."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"

for path in (str(PROJECT_ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def dataset():
    """Session-scoped generated dataset (seed=42)."""
    from dataset.generators.generate import generate_dataset

    return generate_dataset(seed=42)


@pytest.fixture
def client():
    """FastAPI test client (no DB required for health/root)."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
