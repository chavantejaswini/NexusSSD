"""ETL loader — persists a telemetry source into the database.

Idempotent: drives are upserted by serial number and telemetry rows are skipped
if a row for that (drive, date) already exists, so re-running is safe.

CLI:
    python -m app.etl.loader --source synthetic --drives 200 --days 90
    python -m app.etl.loader --source backblaze --csv-dir data/backblaze
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.etl.sources.base import TelemetrySource
from app.models.drive import Drive
from app.models.telemetry import Telemetry

logger = get_logger(__name__)

_BATCH = 1000


@dataclass
class LoadStats:
    drives_inserted: int = 0
    drives_updated: int = 0
    telemetry_inserted: int = 0
    telemetry_skipped: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "drives_inserted": self.drives_inserted,
            "drives_updated": self.drives_updated,
            "telemetry_inserted": self.telemetry_inserted,
            "telemetry_skipped": self.telemetry_skipped,
        }


def load_source(source: TelemetrySource, session: Session) -> LoadStats:
    stats = LoadStats()

    # ---- upsert drives, build serial -> id map ----
    existing = {d.serial_number: d for d in session.execute(select(Drive)).scalars()}
    serial_to_id: dict[str, int] = {}
    for rec in source.iter_drives():
        drive = existing.get(rec.serial_number)
        if drive is None:
            drive = Drive(
                serial_number=rec.serial_number,
                model=rec.model,
                capacity_bytes=rec.capacity_bytes,
                first_seen=rec.first_seen,
                last_seen=rec.last_seen,
                status=rec.status,
            )
            session.add(drive)
            stats.drives_inserted += 1
        else:
            drive.model = rec.model
            drive.capacity_bytes = rec.capacity_bytes
            drive.first_seen = min(drive.first_seen, rec.first_seen)
            drive.last_seen = max(drive.last_seen, rec.last_seen)
            drive.status = rec.status
            stats.drives_updated += 1
        session.flush()  # assign PK
        serial_to_id[rec.serial_number] = drive.id
    session.commit()

    # ---- existing (drive_id, date) pairs to skip ----
    seen: set[tuple[int, object]] = {
        (row.drive_id, row.date)
        for row in session.execute(
            select(Telemetry.drive_id, Telemetry.date)
        ).all()
    }

    # ---- insert telemetry in batches ----
    buffer: list[Telemetry] = []
    for rec in source.iter_telemetry():
        drive_id = serial_to_id.get(rec.serial_number)
        if drive_id is None:
            # Telemetry for a drive the source didn't declare — skip defensively.
            continue
        key = (drive_id, rec.date)
        if key in seen:
            stats.telemetry_skipped += 1
            continue
        seen.add(key)
        buffer.append(
            Telemetry(
                drive_id=drive_id,
                date=rec.date,
                power_on_hours=rec.power_on_hours,
                temperature=rec.temperature,
                reallocated_sectors=rec.reallocated_sectors,
                media_wearout_indicator=rec.media_wearout_indicator,
                pct_used=rec.pct_used,
                raw_smart=rec.raw_smart,
            )
        )
        if len(buffer) >= _BATCH:
            session.add_all(buffer)
            session.commit()
            stats.telemetry_inserted += len(buffer)
            buffer.clear()

    if buffer:
        session.add_all(buffer)
        session.commit()
        stats.telemetry_inserted += len(buffer)

    return stats


def _build_source(args: argparse.Namespace) -> TelemetrySource:
    if args.source == "synthetic":
        from app.etl.sources.synthetic import SyntheticSource

        return SyntheticSource(
            num_drives=args.drives,
            days=args.days,
            seed=args.seed,
            failure_rate=args.failure_rate,
        )
    if args.source == "backblaze":
        from app.etl.sources.backblaze import BackblazeSource

        return BackblazeSource(csv_dir=args.csv_dir)
    raise ValueError(f"unknown source: {args.source}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load SSD telemetry into the database.")
    parser.add_argument("--source", choices=["synthetic", "backblaze"], default="synthetic")
    parser.add_argument("--drives", type=int, default=200, help="synthetic: fleet size")
    parser.add_argument("--days", type=int, default=90, help="synthetic: days of history")
    parser.add_argument("--seed", type=int, default=42, help="synthetic: RNG seed")
    parser.add_argument("--failure-rate", type=float, default=0.15, help="synthetic")
    parser.add_argument("--csv-dir", default="data/backblaze", help="backblaze: CSV dir")
    args = parser.parse_args(argv)

    configure_logging()
    source = _build_source(args)

    session = SessionLocal()
    try:
        stats = load_source(source, session)
    finally:
        session.close()

    logger.info("etl load complete", extra=stats.as_dict())
    print(json.dumps(stats.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
