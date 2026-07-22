"""Backblaze SMART dataset source.

Reads Backblaze daily drive-stats CSV snapshots from a directory and maps them
onto the common source interface. Each CSV row is one drive on one day with a
`failure` flag and many `smart_N_raw` columns.

This is a functional loader for the real dataset (download the daily CSVs into
`data/backblaze/`), kept intentionally minimal. The synthetic source is the
default for development; swap to this with `--source backblaze`.
"""

from __future__ import annotations

import csv
import glob
import os
from collections.abc import Iterable
from datetime import date, datetime

from app.etl.sources.base import DriveRecord, TelemetryRecord, TelemetrySource
from app.models.drive import DriveStatus

# Backblaze SMART attribute → our column (raw values).
_SMART_POWER_ON_HOURS = "smart_9_raw"
_SMART_TEMPERATURE = "smart_194_raw"
_SMART_REALLOCATED = "smart_5_raw"
_SMART_WEAROUT = "smart_233_raw"  # media wearout indicator (varies by vendor)


def _to_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


def _to_int(value: str | None, default: int = 0) -> int:
    return int(_to_float(value, default))


class BackblazeSource(TelemetrySource):
    def __init__(self, csv_dir: str) -> None:
        self.csv_dir = csv_dir
        self._paths = sorted(glob.glob(os.path.join(csv_dir, "*.csv")))
        if not self._paths:
            raise FileNotFoundError(
                f"No Backblaze CSVs found in {csv_dir!r}. "
                "Download daily drive-stats snapshots into this directory."
            )
        # Aggregate drive-level metadata across all daily files.
        self._drives: dict[str, DriveRecord] = {}
        self._built = False

    def _parse_date(self, raw: str) -> date:
        return datetime.strptime(raw, "%Y-%m-%d").date()

    def _build_drive_index(self) -> None:
        if self._built:
            return
        for path in self._paths:
            with open(path, newline="") as fh:
                for row in csv.DictReader(fh):
                    serial = row["serial_number"]
                    day = self._parse_date(row["date"])
                    failed = row.get("failure", "0") == "1"
                    existing = self._drives.get(serial)
                    if existing is None:
                        self._drives[serial] = DriveRecord(
                            serial_number=serial,
                            model=row.get("model", "unknown"),
                            capacity_bytes=_to_int(row.get("capacity_bytes")),
                            first_seen=day,
                            last_seen=day,
                            status=DriveStatus.FAILED.value
                            if failed
                            else DriveStatus.HEALTHY.value,
                        )
                    else:
                        existing.first_seen = min(existing.first_seen, day)
                        existing.last_seen = max(existing.last_seen, day)
                        if failed:
                            existing.status = DriveStatus.FAILED.value
        self._built = True

    def iter_drives(self) -> Iterable[DriveRecord]:
        self._build_drive_index()
        yield from self._drives.values()

    def iter_telemetry(self) -> Iterable[TelemetryRecord]:
        for path in self._paths:
            with open(path, newline="") as fh:
                for row in csv.DictReader(fh):
                    yield TelemetryRecord(
                        serial_number=row["serial_number"],
                        date=self._parse_date(row["date"]),
                        power_on_hours=_to_int(row.get(_SMART_POWER_ON_HOURS)),
                        temperature=_to_float(row.get(_SMART_TEMPERATURE)),
                        reallocated_sectors=_to_int(row.get(_SMART_REALLOCATED)),
                        media_wearout_indicator=_to_float(row.get(_SMART_WEAROUT)),
                        pct_used=_to_float(row.get(_SMART_WEAROUT)),
                        raw_smart={
                            k: v for k, v in row.items() if k.startswith("smart_")
                        },
                    )
