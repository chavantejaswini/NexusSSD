"""Telemetry source interface + record dataclasses.

A source yields drive metadata and daily SMART telemetry. Concrete sources
(synthetic generator, Backblaze CSV loader) implement the same contract so the
loader is source-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date


@dataclass
class DriveRecord:
    serial_number: str
    model: str
    capacity_bytes: int
    first_seen: date
    last_seen: date
    status: str  # matches app.models.drive.DriveStatus values


@dataclass
class TelemetryRecord:
    serial_number: str
    date: date
    power_on_hours: int
    temperature: float
    reallocated_sectors: int
    media_wearout_indicator: float
    pct_used: float
    raw_smart: dict = field(default_factory=dict)


class TelemetrySource(ABC):
    """Abstract source of drives + telemetry."""

    @abstractmethod
    def iter_drives(self) -> Iterable[DriveRecord]:
        """Yield one record per drive."""

    @abstractmethod
    def iter_telemetry(self) -> Iterable[TelemetryRecord]:
        """Yield one record per drive per observed day."""
