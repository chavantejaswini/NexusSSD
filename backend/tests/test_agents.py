"""Tests for the LangGraph multi-agent chat workflow (offline template path)."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.agents import planner
from app.agents.graph import run_chat
from app.agents.tools import Tools
from app.etl.loader import load_source
from app.etl.sources.synthetic import SyntheticSource
from app.models.chat import ChatHistory
from app.services import rag_service

_DOCS = [
    {
        "title": "Failure Signatures",
        "source": "failure_signatures.md",
        "content": "Reallocated sectors climbing sharply is the classic pre-failure signal. "
        "Replace high-risk drives during a maintenance window.",
    }
]


@pytest.fixture()
def fleet(db_session):
    source = SyntheticSource(
        num_drives=15, days=45, seed=3, failure_rate=0.3, end_date=date(2026, 1, 31)
    )
    load_source(source, db_session)
    rag_service.ingest_documents(db_session, _DOCS)
    return db_session


def test_planner_routes_risk_query() -> None:
    steps = planner.plan("which drives are most likely to fail?")
    assert "prediction" in steps
    assert "sql" in steps


def test_planner_routes_doc_query() -> None:
    assert "rag" in planner.plan("why do SSDs fail and how should I do maintenance?")


def test_planner_default_when_unmatched() -> None:
    assert planner.plan("hello there") == ["sql", "rag"]


def test_tools_sql_fleet_summary(fleet) -> None:
    result = Tools(fleet).sql("give me a fleet summary")
    assert result["intent"] == "fleet_summary"
    assert any(r["metric"] == "total_drives" for r in result["rows"])


def test_tools_sql_failed(fleet) -> None:
    result = Tools(fleet).sql("list failed drives")
    assert result["intent"] == "drives_by_status"


def test_run_chat_grounds_with_docs(fleet) -> None:
    out = run_chat(fleet, "why do drives fail and when should I replace them?")
    assert out["answer"]
    assert "planner" in out["agents"]
    assert "summary" in out["agents"]
    assert "rag" in out["agents"]


def test_run_chat_persists_history(fleet) -> None:
    out = run_chat(fleet, "how many drives are in the fleet?")
    n = fleet.execute(
        select(func.count()).select_from(ChatHistory).where(
            ChatHistory.session_id == out["session_id"]
        )
    ).scalar_one()
    assert n == 2  # user + assistant

    assistant = fleet.execute(
        select(ChatHistory).where(
            ChatHistory.session_id == out["session_id"], ChatHistory.role == "assistant"
        )
    ).scalars().one()
    assert assistant.agent_trace is not None
    assert "trace" in assistant.agent_trace


def test_chat_endpoint(fleet, client: TestClient) -> None:
    resp = client.post("/chat", json={"message": "which drives are hottest right now?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["session_id"]
    assert "sql" in body["agents"]
    # Continuing the same session reuses the id.
    resp2 = client.post(
        "/chat", json={"message": "and how many failed?", "session_id": body["session_id"]}
    )
    assert resp2.json()["session_id"] == body["session_id"]
