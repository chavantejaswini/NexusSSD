"""Shared pytest fixtures.

Sets a SQLite database URL *before* the app is imported so tests never require
a running Postgres. The schema is created from ORM metadata (StaticPool keeps
the in-memory DB alive across sessions).
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401  register all models on Base.metadata
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.etl.loader import load_source  # noqa: E402
from app.etl.sources.synthetic import SyntheticSource  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables(_schema):
    """Empty every table before each test for isolation."""
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture(autouse=True)
def _reset_model_cache():
    """Clear the cached prediction model so tests never share model state."""
    from app.services import prediction_service

    prediction_service.reload_model()
    yield
    prediction_service.reload_model()


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def seeded(db_session):
    """Load a small deterministic synthetic fleet into the test DB."""
    source = SyntheticSource(
        num_drives=12, days=40, seed=7, failure_rate=0.25, end_date=date(2026, 1, 31)
    )
    stats = load_source(source, db_session)
    return stats
