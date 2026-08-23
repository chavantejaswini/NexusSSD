"""Retrieval-Augmented Generation service: chunk, embed, ingest, and retrieve.

Retrieval uses pgvector's cosine-distance operator (`<=>`) on PostgreSQL so it
rides the vector index; on SQLite (tests/dev) it falls back to an in-Python
cosine over all stored embeddings. Both return the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.knowledge import Document, Embedding
from app.services.embeddings import get_embedder

logger = get_logger(__name__)


def chunk_text(content: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping character windows."""
    content = content.strip()
    if len(content) <= max_chars:
        return [content] if content else []
    chunks: list[str] = []
    start = 0
    while start < len(content):
        chunk = content[start : start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        start += max_chars - overlap
    return chunks


@dataclass
class IngestStats:
    documents: int = 0
    chunks: int = 0


def ingest_documents(session: Session, docs: list[dict]) -> IngestStats:
    """Ingest documents (dicts with title/source/content/doc_type).

    Idempotent per `source`: an existing document with the same source is
    replaced (its chunks cascade-delete) so re-ingesting picks up edits.
    """
    embedder = get_embedder()
    stats = IngestStats()

    for doc in docs:
        source = doc["source"]
        existing = session.execute(
            select(Document).where(Document.source == source)
        ).scalars().all()
        for old in existing:
            session.delete(old)
        session.flush()

        document = Document(
            title=doc["title"],
            source=source,
            doc_type=doc.get("doc_type", "manual"),
            content=doc["content"],
        )
        session.add(document)
        session.flush()  # assign id

        chunks = chunk_text(doc["content"])
        if not chunks:
            stats.documents += 1
            continue
        vectors = embedder.embed(chunks)
        for chunk, vector in zip(chunks, vectors):
            session.add(
                Embedding(document_id=document.id, chunk_text=chunk, embedding=vector)
            )
        stats.documents += 1
        stats.chunks += len(chunks)

    session.commit()
    logger.info(
        "ingested documents",
        extra={"documents": stats.documents, "chunks": stats.chunks, "embedder": embedder.name},
    )
    return stats


@dataclass
class RetrievedChunk:
    chunk_text: str
    score: float
    document_id: int
    document_title: str
    source: str


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return dot / (na * nb)


def retrieve(session: Session, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    embedder = get_embedder()
    qvec = embedder.embed([query])[0]
    dialect = session.get_bind().dialect.name

    if dialect == "postgresql":
        return _retrieve_pgvector(session, qvec, top_k)
    return _retrieve_python(session, qvec, top_k)


def _retrieve_pgvector(session: Session, qvec: list[float], top_k: int) -> list[RetrievedChunk]:
    literal = "[" + ",".join(repr(float(x)) for x in qvec) + "]"
    rows = session.execute(
        text(
            """
            SELECT e.chunk_text, e.document_id, d.title, d.source,
                   (e.embedding <=> CAST(:q AS vector)) AS distance
            FROM embeddings e
            JOIN documents d ON d.id = e.document_id
            ORDER BY distance ASC
            LIMIT :k
            """
        ),
        {"q": literal, "k": top_k},
    ).all()
    return [
        RetrievedChunk(
            chunk_text=r.chunk_text,
            score=1.0 - float(r.distance),
            document_id=r.document_id,
            document_title=r.title,
            source=r.source,
        )
        for r in rows
    ]


def _retrieve_python(session: Session, qvec: list[float], top_k: int) -> list[RetrievedChunk]:
    rows = session.execute(
        select(Embedding, Document).join(Document, Document.id == Embedding.document_id)
    ).all()
    scored = [
        RetrievedChunk(
            chunk_text=emb.chunk_text,
            score=_cosine(qvec, emb.embedding),
            document_id=doc.id,
            document_title=doc.title,
            source=doc.source,
        )
        for emb, doc in rows
    ]
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_k]
