"""Query logic for drive listing and detail views."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.drive import Drive
from app.models.fleet import Prediction
from app.models.telemetry import Telemetry


def _latest_predictions(session: Session, drive_ids: list[int]) -> dict[int, Prediction]:
    """Map drive_id -> its most recent Prediction, for the given drives."""
    if not drive_ids:
        return {}
    rows = session.execute(
        select(Prediction)
        .where(Prediction.drive_id.in_(drive_ids))
        .order_by(Prediction.drive_id, Prediction.predicted_at.desc())
    ).scalars()
    latest: dict[int, Prediction] = {}
    for pred in rows:
        latest.setdefault(pred.drive_id, pred)  # first per drive = most recent
    return latest


def list_drives(
    session: Session,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return a page of drive summaries (as dicts) and the total count."""
    base = select(Drive)
    count_q = select(func.count()).select_from(Drive)
    if status:
        base = base.where(Drive.status == status)
        count_q = count_q.where(Drive.status == status)

    total = session.execute(count_q).scalar_one()
    drives = list(
        session.execute(
            base.order_by(Drive.status, Drive.serial_number).limit(limit).offset(offset)
        ).scalars()
    )

    latest = _latest_predictions(session, [d.id for d in drives])
    items: list[dict] = []
    for d in drives:
        pred = latest.get(d.id)
        items.append(
            {
                "id": d.id,
                "serial_number": d.serial_number,
                "model": d.model,
                "capacity_bytes": d.capacity_bytes,
                "status": d.status,
                "first_seen": d.first_seen,
                "last_seen": d.last_seen,
                "latest_failure_probability": pred.failure_probability if pred else None,
            }
        )
    return items, total


def get_drive_detail(
    session: Session, drive_id: int, telemetry_limit: int = 180
) -> dict | None:
    """Return a drive with recent telemetry + latest prediction, or None."""
    drive = session.get(Drive, drive_id)
    if drive is None:
        return None

    telemetry = list(
        session.execute(
            select(Telemetry)
            .where(Telemetry.drive_id == drive_id)
            .order_by(Telemetry.date.desc())
            .limit(telemetry_limit)
        ).scalars()
    )
    telemetry.reverse()  # chronological for charting

    pred = _latest_predictions(session, [drive_id]).get(drive_id)

    return {
        "id": drive.id,
        "serial_number": drive.serial_number,
        "model": drive.model,
        "capacity_bytes": drive.capacity_bytes,
        "status": drive.status,
        "first_seen": drive.first_seen,
        "last_seen": drive.last_seen,
        "latest_failure_probability": pred.failure_probability if pred else None,
        "telemetry": telemetry,
        "latest_prediction": pred,
    }
