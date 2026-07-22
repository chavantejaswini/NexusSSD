"""Telemetry model — one row per drive per day of SMART data."""

from __future__ import annotations

from datetime import date

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Telemetry(Base):
    __tablename__ = "telemetry"
    __table_args__ = (
        UniqueConstraint("drive_id", "date", name="uq_telemetry_drive_date"),
        Index("ix_telemetry_drive_date", "drive_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    drive_id: Mapped[int] = mapped_column(
        ForeignKey("drives.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date)

    power_on_hours: Mapped[int] = mapped_column(Integer)
    temperature: Mapped[float] = mapped_column(Float)  # Celsius
    reallocated_sectors: Mapped[int] = mapped_column(Integer)  # SMART 5 raw
    media_wearout_indicator: Mapped[float] = mapped_column(Float)  # 0-100, % consumed
    pct_used: Mapped[float] = mapped_column(Float)  # NVMe "Percentage Used"
    raw_smart: Mapped[dict] = mapped_column(JSON, default=dict)  # extra SMART attrs

    drive: Mapped["Drive"] = relationship(back_populates="telemetry")  # noqa: F821
