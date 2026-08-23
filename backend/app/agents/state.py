"""Shared state for the chat agent graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class ChatState(TypedDict, total=False):
    query: str
    tools: Any  # Tools instance bound to a DB session (in-memory only)
    plan: list[str]
    retries: int

    sql_result: dict | None
    prediction_result: dict | None
    rag_result: list[dict] | None
    evaluation: dict | None
    answer: str

    # Accumulated agent trace (reducer appends across nodes).
    trace: Annotated[list[dict], operator.add]
