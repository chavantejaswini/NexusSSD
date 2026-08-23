"""Ingest SSD documentation from a directory into the RAG store.

Reads .md and .txt files from a docs directory (default: <repo>/data/docs),
embeds their chunks, and stores them for semantic retrieval.

    python -m app.rag.ingest                    # ingest <repo>/data/docs
    python -m app.rag.ingest --docs-dir path/   # custom directory
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.services import rag_service

logger = get_logger(__name__)

# backend/app/rag/ingest.py -> parents[3] == repo root (NexusSSD/)
_REPO_ROOT = Path(__file__).resolve().parents[3]
# Curated, version-controlled sample corpus (data/docs/ is for user-supplied docs).
_DEFAULT_DOCS_DIR = _REPO_ROOT / "data" / "sample_docs"


def load_docs_from_dir(docs_dir: Path) -> list[dict]:
    docs: list[dict] = []
    for path in sorted(docs_dir.glob("**/*")):
        if path.suffix.lower() not in (".md", ".txt"):
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        docs.append(
            {
                "title": path.stem.replace("_", " ").title(),
                "source": str(path.relative_to(docs_dir)),
                "doc_type": "manual",
                "content": content,
            }
        )
    return docs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest SSD docs into the RAG store.")
    parser.add_argument("--docs-dir", default=str(_DEFAULT_DOCS_DIR))
    args = parser.parse_args(argv)

    configure_logging()
    docs_dir = Path(args.docs_dir)
    docs = load_docs_from_dir(docs_dir)
    if not docs:
        print(json.dumps({"error": f"no .md/.txt files found in {docs_dir}"}))
        return 1

    session = SessionLocal()
    try:
        stats = rag_service.ingest_documents(session, docs)
    finally:
        session.close()

    print(json.dumps({"documents": stats.documents, "chunks": stats.chunks}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
