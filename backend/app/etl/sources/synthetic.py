"""Synthetic SMART telemetry generator.

Produces a deterministic (seeded) fleet of SSDs with realistic daily telemetry.
A configurable fraction of drives are "failing": in the weeks before failure
their temperature, reallocated-sector count, and wear indicators trend upward,
and their telemetry stops on the failure date. This gives the downstream
prediction model (Phase 3) a learnable failure signal without any external data.
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from datetime import date, timedelta

from app.etl.sources.base import DriveRecord, TelemetryRecord, TelemetrySource
from app.models.drive import DriveStatus

# (model name, capacity in bytes)
_MODELS: list[tuple[str, int]] = [
    ("Samsung PM883", 960_197_124_096),
    ("Seagate Nytro 1351", 1_920_383_410_176),
    ("Micron 5200 ECO", 480_103_981_056),
    ("Intel SSD S4510", 960_197_124_096),
    ("WD Ultrastar DC SS530", 1_920_383_410_176),
]

_RAMP_DAYS = 21  # days before failure over which degradation ramps up


class _DriveSpec:
    """Deterministic per-drive parameters used to regenerate telemetry."""

    def __init__(self, index: int, rng: random.Random, days: int, failing: bool):
        self.serial_number = f"NX-{index:06d}"
        self.model, self.capacity_bytes = rng.choice(_MODELS)
        self.days = days
        self.failing = failing
        self.temp_baseline = rng.uniform(28.0, 39.0)
        self.poh_start = rng.randint(2_000, 42_000)
        self.wear_start = rng.uniform(1.0, 35.0)
        self.wear_rate = rng.uniform(0.01, 0.06)  # % consumed per day (healthy)
        # Failure happens in the second half of the observed window.
        self.failure_day = rng.randint(days // 2, days - 1) if failing else None
        # Per-day noise seeds so regeneration is stable.
        self._noise = [rng.uniform(-2.5, 2.5) for _ in range(days)]


class SyntheticSource(TelemetrySource):
    def __init__(
        self,
        num_drives: int = 200,
        days: int = 90,
        seed: int = 42,
        failure_rate: float = 0.15,
        end_date: date | None = None,
    ) -> None:
        if num_drives <= 0 or days <= 0:
            raise ValueError("num_drives and days must be positive")
        self.num_drives = num_drives
        self.days = days
        self.seed = seed
        self.failure_rate = failure_rate
        self.end_date = end_date or date.today()
        self.start_date = self.end_date - timedelta(days=days - 1)

        rng = random.Random(seed)
        self._specs: list[_DriveSpec] = [
            _DriveSpec(i, rng, days, failing=rng.random() < failure_rate)
            for i in range(num_drives)
        ]

    # ---- drives ----
    def iter_drives(self) -> Iterable[DriveRecord]:
        for spec in self._specs:
            if spec.failing and spec.failure_day is not None:
                last_seen = self.start_date + timedelta(days=spec.failure_day)
                status = DriveStatus.FAILED.value
            else:
                last_seen = self.end_date
                status = DriveStatus.HEALTHY.value
            yield DriveRecord(
                serial_number=spec.serial_number,
                model=spec.model,
                capacity_bytes=spec.capacity_bytes,
                first_seen=self.start_date,
                last_seen=last_seen,
                status=status,
            )

    # ---- telemetry ----
    def iter_telemetry(self) -> Iterable[TelemetryRecord]:
        for spec in self._specs:
            last_day = spec.failure_day if spec.failing else spec.days - 1
            assert last_day is not None
            reallocated = 0
            for day in range(last_day + 1):
                yield self._telemetry_for_day(spec, day, reallocated)
                reallocated = self._reallocated_after(spec, day, reallocated)

    def _reallocated_after(self, spec: _DriveSpec, day: int, current: int) -> int:
        """Cumulative reallocated-sector count evolving day to day."""
        rng = random.Random(f"{self.seed}:{spec.serial_number}:{day}")
        if spec.failing and spec.failure_day is not None:
            days_to_fail = spec.failure_day - day
            if days_to_fail <= _RAMP_DAYS:
                return current + rng.randint(3, 45)
        # Healthy drives very rarely reallocate a sector.
        return current + (1 if rng.random() < 0.02 else 0)

    def _telemetry_for_day(
        self, spec: _DriveSpec, day: int, reallocated: int
    ) -> TelemetryRecord:
        the_date = self.start_date + timedelta(days=day)
        noise = spec._noise[day]

        power_on_hours = spec.poh_start + day * 24 + int(noise)
        wear = min(100.0, spec.wear_start + day * spec.wear_rate)
        temp = spec.temp_baseline + noise

        if spec.failing and spec.failure_day is not None:
            days_to_fail = spec.failure_day - day
            if days_to_fail <= _RAMP_DAYS:
                ramp = (_RAMP_DAYS - days_to_fail) / _RAMP_DAYS  # 0 -> 1
                temp += ramp * 16.0  # runs hot near failure
                wear = min(100.0, wear + ramp * 25.0)

        pct_used = min(130.0, wear + spec._noise[day] * 0.5)

        return TelemetryRecord(
            serial_number=spec.serial_number,
            date=the_date,
            power_on_hours=power_on_hours,
            temperature=round(temp, 1),
            reallocated_sectors=reallocated,
            media_wearout_indicator=round(wear, 2),
            pct_used=round(max(0.0, pct_used), 2),
            raw_smart={
                "smart_5_raw": reallocated,
                "smart_9_raw": power_on_hours,
                "smart_194_raw": round(temp, 1),
                "smart_233_raw": round(wear, 2),
            },
        )
