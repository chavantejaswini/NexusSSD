"""Drive model — one row per physical SSD in the fleet."""

from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import BigInteger, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DriveStatus(str, enum.Enum):
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    FAILED = "failed"
    DECOMMISSIONED = "decommissioned"


class Drive(Base):
    __tablename__ = "drives"

    id: Mapped[int] = mapped_column(primary_key=True)
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model: Mapped[str] = mapped_column(String(128), index=True)
    capacity_bytes: Mapped[int] = mapped_column(BigInteger)
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(20), default=DriveStatus.HEALTHY.value, index=True
    )

    telemetry: Mapped[list["Telemetry"]] = relationship(  # noqa: F821
        back_populates="drive", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        back_populates="drive", cascade="all, delete-orphan"
    )
