"""Tests for the ETL synthetic source and loader."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.etl.loader import load_source
from app.etl.sources.synthetic import SyntheticSource
from app.models.drive import Drive, DriveStatus
from app.models.telemetry import Telemetry


def test_synthetic_load_counts(seeded, db_session) -> None:
    drives = db_session.execute(select(func.count()).select_from(Drive)).scalar_one()
    telem = db_session.execute(select(func.count()).select_from(Telemetry)).scalar_one()
    failed = db_session.execute(
        select(func.count()).select_from(Drive).where(Drive.status == DriveStatus.FAILED.value)
    ).scalar_one()

    assert drives == 12
    assert seeded.drives_inserted == 12
    assert telem > 0
    assert failed >= 1  # ~25% of the fleet should be failing


def test_failed_drive_telemetry_stops_early(seeded, db_session) -> None:
    """A failed drive's last telemetry date should equal its last_seen date."""
    failed_drive = db_session.execute(
        select(Drive).where(Drive.status == DriveStatus.FAILED.value)
    ).scalars().first()
    assert failed_drive is not None

    last_telem_date = db_session.execute(
        select(func.max(Telemetry.date)).where(Telemetry.drive_id == failed_drive.id)
    ).scalar_one()
    assert last_telem_date == failed_drive.last_seen
    assert failed_drive.last_seen < date(2026, 1, 31)  # stopped before window end


def test_load_is_idempotent(db_session) -> None:
    source = SyntheticSource(num_drives=5, days=20, seed=1, end_date=date(2026, 1, 20))
    first = load_source(source, db_session)
    assert first.drives_inserted == 5
    assert first.telemetry_inserted > 0

    second = load_source(source, db_session)
    assert second.drives_inserted == 0
    assert second.telemetry_inserted == 0
    assert second.telemetry_skipped == first.telemetry_inserted
