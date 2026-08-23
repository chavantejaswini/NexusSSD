"""Semantic retrieval endpoint (RAG over ingested SSD documentation)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.retrieve import RetrievedChunk, RetrieveRequest, RetrieveResponse
from app.services import rag_service

router = APIRouter(tags=["rag"])


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest, db: Session = Depends(get_db)) -> RetrieveResponse:
    hits = rag_service.retrieve(db, request.query, top_k=request.top_k)
    return RetrieveResponse(
        query=request.query,
        results=[RetrievedChunk(**hit.__dict__) for hit in hits],
    )
