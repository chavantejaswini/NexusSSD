"""Multi-agent chat endpoint (LangGraph workflow)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.graph import run_chat
from app.db.session import get_db
from app.schemas.chat import ChatResponse, ChatRequest

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    result = run_chat(db, request.message, session_id=request.session_id)
    return ChatResponse(**result)
