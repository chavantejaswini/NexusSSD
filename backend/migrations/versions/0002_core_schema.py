"""core schema: drives, telemetry, predictions, maintenance, alerts, documents, embeddings, chat_history

Revision ID: 0002_core_schema
Revises: 0001_enable_pgvector
Create Date: 2026-07-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.types import JSON

from app.core.config import settings
from app.db.types import EmbeddingVector

# revision identifiers, used by Alembic.
revision: str = "0002_core_schema"
down_revision: str | None = "0001_enable_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drives",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("serial_number", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("capacity_bytes", sa.BigInteger, nullable=False),
        sa.Column("first_seen", sa.Date, nullable=False),
        sa.Column("last_seen", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="healthy"),
    )
    op.create_index("ix_drives_serial_number", "drives", ["serial_number"], unique=True)
    op.create_index("ix_drives_model", "drives", ["model"])
    op.create_index("ix_drives_status", "drives", ["status"])

    op.create_table(
        "telemetry",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "drive_id",
            sa.Integer,
            sa.ForeignKey("drives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("power_on_hours", sa.Integer, nullable=False),
        sa.Column("temperature", sa.Float, nullable=False),
        sa.Column("reallocated_sectors", sa.Integer, nullable=False),
        sa.Column("media_wearout_indicator", sa.Float, nullable=False),
        sa.Column("pct_used", sa.Float, nullable=False),
        sa.Column("raw_smart", JSON, nullable=True),
        sa.UniqueConstraint("drive_id", "date", name="uq_telemetry_drive_date"),
    )
    op.create_index("ix_telemetry_drive_id", "telemetry", ["drive_id"])
    op.create_index("ix_telemetry_drive_date", "telemetry", ["drive_id", "date"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "drive_id",
            sa.Integer,
            sa.ForeignKey("drives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("failure_probability", sa.Float, nullable=False),
        sa.Column("horizon_days", sa.Integer, nullable=False),
        sa.Column("features", JSON, nullable=True),
        sa.Column(
            "predicted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_predictions_drive_id", "predictions", ["drive_id"])
    op.create_index("ix_predictions_predicted_at", "predictions", ["predicted_at"])

    op.create_table(
        "maintenance",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "drive_id",
            sa.Integer,
            sa.ForeignKey("drives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "performed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_maintenance_drive_id", "maintenance", ["drive_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "drive_id",
            sa.Integer,
            sa.ForeignKey("drives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("acknowledged", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_alerts_drive_id", "alerts", ["drive_id"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("source", sa.String(256), nullable=False),
        sa.Column("doc_type", sa.String(64), nullable=False, server_default="manual"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", EmbeddingVector(settings.embedding_dim), nullable=False),
    )
    op.create_index("ix_embeddings_document_id", "embeddings", ["document_id"])

    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("agent_trace", JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_chat_history_session_id", "chat_history", ["session_id"])
    op.create_index("ix_chat_history_created_at", "chat_history", ["created_at"])


def downgrade() -> None:
    op.drop_table("chat_history")
    op.drop_table("embeddings")
    op.drop_table("documents")
    op.drop_table("alerts")
    op.drop_table("maintenance")
    op.drop_table("predictions")
    op.drop_table("telemetry")
    op.drop_table("drives")
