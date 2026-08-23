"""Tests for chunking, embedding, ingestion, and retrieval."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models.knowledge import Document, Embedding
from app.services import rag_service
from app.services.embeddings import HashingEmbedder, get_embedder

_DOC_A = {
    "title": "Reallocated Sectors",
    "source": "a.md",
    "content": "Reallocated sectors count SMART 5 climbs sharply before drive failure "
    "once the spare area is exhausted.",
}
_DOC_B = {
    "title": "Temperature",
    "source": "b.md",
    "content": "Drive temperature in Celsius depends on airflow, cooling, and ambient "
    "conditions in the datacenter.",
}


def test_chunk_text_overlap() -> None:
    chunks = rag_service.chunk_text("x" * 2000, max_chars=800, overlap=100)
    assert len(chunks) >= 3
    assert all(len(c) <= 800 for c in chunks)


def test_default_embedder_is_offline() -> None:
    embedder = get_embedder()
    assert isinstance(embedder, HashingEmbedder)
    vecs = embedder.embed(["hello world", "hello world"])
    assert len(vecs[0]) == embedder.dim
    assert vecs[0] == vecs[1]  # deterministic


def test_ingest_creates_documents_and_embeddings(db_session) -> None:
    stats = rag_service.ingest_documents(db_session, [_DOC_A, _DOC_B])
    assert stats.documents == 2
    assert stats.chunks >= 2

    n_docs = db_session.execute(select(func.count()).select_from(Document)).scalar_one()
    n_emb = db_session.execute(select(func.count()).select_from(Embedding)).scalar_one()
    assert n_docs == 2
    assert n_emb == stats.chunks


def test_ingest_is_idempotent_per_source(db_session) -> None:
    rag_service.ingest_documents(db_session, [_DOC_A])
    rag_service.ingest_documents(db_session, [_DOC_A])
    n_docs = db_session.execute(select(func.count()).select_from(Document)).scalar_one()
    assert n_docs == 1  # replaced, not duplicated


def test_retrieve_ranks_relevant_doc_first(db_session) -> None:
    rag_service.ingest_documents(db_session, [_DOC_A, _DOC_B])
    hits = rag_service.retrieve(db_session, "reallocated sectors failure", top_k=2)
    assert hits
    assert hits[0].source == "a.md"
    # Scores are sorted descending.
    assert all(hits[i].score >= hits[i + 1].score for i in range(len(hits) - 1))


def test_retrieve_endpoint(db_session, client: TestClient) -> None:
    rag_service.ingest_documents(db_session, [_DOC_A, _DOC_B])
    resp = client.post("/retrieve", json={"query": "temperature airflow cooling", "top_k": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "temperature airflow cooling"
    assert len(body["results"]) == 1
    assert body["results"][0]["source"] == "b.md"
    assert body["results"][0]["document_title"] == "Temperature"
