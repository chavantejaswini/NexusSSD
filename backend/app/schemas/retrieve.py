"""Request/response schemas for the /retrieve endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_text: str
    score: float
    document_id: int
    document_title: str
    source: str


class RetrieveResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]
