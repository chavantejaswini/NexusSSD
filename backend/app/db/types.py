"""Custom SQLAlchemy column types.

`EmbeddingVector` uses pgvector's native `vector` type on PostgreSQL and falls
back to JSON on other dialects (SQLite) so the schema can be created for tests
without a Postgres server.
"""

from __future__ import annotations

from sqlalchemy.types import JSON, TypeDecorator


class EmbeddingVector(TypeDecorator):
    """A fixed-dimension embedding column.

    - PostgreSQL: `vector(dim)` (requires the `vector` extension).
    - Other dialects: JSON array of floats.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int) -> None:
        self.dim = dim
        super().__init__()

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())
