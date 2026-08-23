"""Tests for the LlamaIndex RAG backend wiring.

The pgvector-backed path needs a live Postgres, so here we verify the pieces we
can offline: the NexusEmbedding adapter drives a LlamaIndex in-memory index and
retrieves the relevant node using our pluggable embedder. This proves the
adapter + LlamaIndex integration; the only unexercised piece is PGVectorStore's
connection, which is standard.
"""

from __future__ import annotations

import pytest

pytest.importorskip("llama_index.core")

from llama_index.core import Document, VectorStoreIndex  # noqa: E402
from llama_index.core.node_parser import SentenceSplitter  # noqa: E402

from app.services.embeddings import get_embedder  # noqa: E402
from app.services.rag_llamaindex import NexusEmbedding, _source_to_id  # noqa: E402


def test_nexus_embedding_powers_llamaindex_retrieval() -> None:
    embed_model = NexusEmbedding(get_embedder())
    docs = [
        Document(
            text="Reallocated sectors count SMART 5 climbs sharply before drive failure.",
            metadata={"source": "a.md", "title": "Reallocated Sectors"},
        ),
        Document(
            text="Drive temperature in Celsius depends on airflow and cooling.",
            metadata={"source": "b.md", "title": "Temperature"},
        ),
    ]
    nodes = SentenceSplitter().get_nodes_from_documents(docs)
    index = VectorStoreIndex(nodes, embed_model=embed_model)

    hits = index.as_retriever(similarity_top_k=1).retrieve("reallocated sectors failure")
    assert hits
    assert hits[0].node.metadata["source"] == "a.md"


def test_source_to_id_is_deterministic_and_nonnegative() -> None:
    assert _source_to_id("a.md") == _source_to_id("a.md")
    assert _source_to_id("a.md") >= 0
    assert _source_to_id("a.md") != _source_to_id("b.md")
