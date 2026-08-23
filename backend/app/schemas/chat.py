"""Request/response schemas for the /chat endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class AgentStep(BaseModel):
    agent: str
    detail: dict[str, Any] = {}


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    agents: list[str]
    trace: list[AgentStep]
