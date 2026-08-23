"""LlamaIndex-backed RAG, orchestrated over a pgvector store.

This is the RAG backend used on PostgreSQL (see settings.rag_backend). It reuses
the same pluggable embeddings as the native path via a thin `BaseEmbedding`
adapter, so switching backends never changes which embedder is in effect.

LlamaIndex manages its own pgvector-backed table (separate from the native
`embeddings` table); retrieval returns the same `RetrievedChunk` shape as the
native service so the API is identical regardless of backend.

Requires the `llamaindex` extra and a running PostgreSQL with pgvector.
"""

from __future__ import annotations

import hashlib

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings import Embedder, get_embedder
from app.services.rag_service import IngestStats, RetrievedChunk

logger = get_logger(__name__)

_TABLE_NAME = "rag"  # PGVectorStore creates/uses table "data_rag"


class NexusEmbedding(BaseEmbedding):
    """Adapts our pluggable Embedder to LlamaIndex's BaseEmbedding interface."""

    _embedder: Embedder = PrivateAttr()

    def __init__(self, embedder: Embedder, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._embedder = embedder

    @classmethod
    def class_name(cls) -> str:
        return "nexus_embedding"

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embedder.embed([query])[0]

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embedder.embed([text])[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.embed(texts)


def _source_to_id(source: str) -> int:
    """Deterministic non-negative int id from a source path (for the API shape)."""
    return int(hashlib.md5(source.encode()).hexdigest()[:8], 16)


def _vector_store() -> PGVectorStore:
    url = make_url(settings.database_url)
    return PGVectorStore.from_params(
        host=url.host or "localhost",
        port=str(url.port or 5432),
        database=url.database,
        user=url.username,
        password=url.password,
        table_name=_TABLE_NAME,
        embed_dim=settings.embedding_dim,
    )


def _embed_model() -> NexusEmbedding:
    return NexusEmbedding(get_embedder())


def ingest_documents(docs: list[dict]) -> IngestStats:
    vector_store = _vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    splitter = SentenceSplitter(chunk_size=800, chunk_overlap=100)

    li_docs = [
        Document(
            text=doc["content"],
            doc_id=doc["source"],  # ref_doc_id, enables idempotent re-ingest
            metadata={
                "title": doc["title"],
                "source": doc["source"],
                "doc_type": doc.get("doc_type", "manual"),
            },
        )
        for doc in docs
    ]

    # Best-effort idempotency: drop prior nodes for these sources first.
    for doc in li_docs:
        try:
            vector_store.delete(ref_doc_id=doc.doc_id)
        except Exception:  # noqa: BLE001 - table may not exist on first ingest
            pass

    nodes = splitter.get_nodes_from_documents(li_docs)
    VectorStoreIndex(
        nodes, storage_context=storage_context, embed_model=_embed_model()
    )
    stats = IngestStats(documents=len(li_docs), chunks=len(nodes))
    logger.info(
        "ingested documents (llamaindex)",
        extra={"documents": stats.documents, "chunks": stats.chunks},
    )
    return stats


def retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    index = VectorStoreIndex.from_vector_store(
        _vector_store(), embed_model=_embed_model()
    )
    nodes = index.as_retriever(similarity_top_k=top_k).retrieve(query)
    results: list[RetrievedChunk] = []
    for scored in nodes:
        meta = scored.node.metadata or {}
        source = meta.get("source", "")
        results.append(
            RetrievedChunk(
                chunk_text=scored.node.get_content(),
                score=float(scored.score or 0.0),
                document_id=_source_to_id(source),
                document_title=meta.get("title", ""),
                source=source,
            )
        )
    return results
