"""Shared pytest fixtures.

Sets a SQLite database URL *before* the app is imported so tests never require
a running Postgres. Phase 1 has no tables, so an in-memory SQLite is sufficient
to exercise the app and the /health DB ping.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
