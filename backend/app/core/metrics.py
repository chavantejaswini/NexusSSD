"""Prometheus metrics definitions and DB-derived gauge updates."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# ---- HTTP request metrics (updated by middleware) ----
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

# ---- Application/domain gauges (refreshed on scrape) ----
DRIVES_TOTAL = Gauge("nexus_drives_total", "Total drives in the fleet")
DRIVES_FAILED = Gauge("nexus_drives_failed", "Drives with status=failed")
HIGH_RISK_DRIVES = Gauge(
    "nexus_high_risk_drives", "Drives whose latest prediction probability >= 0.7"
)
PREDICTIONS_TOTAL = Gauge("nexus_predictions_total", "Prediction rows stored")
OPEN_ALERTS = Gauge("nexus_open_alerts", "Unacknowledged alerts")


def refresh_domain_gauges(session: Session) -> None:
    """Refresh app gauges from the database. Resilient to a missing schema."""
    # Import here to avoid a circular import at module load.
    from app.models.drive import Drive, DriveStatus
    from app.models.fleet import Alert, Prediction

    try:
        DRIVES_TOTAL.set(
            session.execute(select(func.count()).select_from(Drive)).scalar_one()
        )
        DRIVES_FAILED.set(
            session.execute(
                select(func.count())
                .select_from(Drive)
                .where(Drive.status == DriveStatus.FAILED.value)
            ).scalar_one()
        )
        PREDICTIONS_TOTAL.set(
            session.execute(select(func.count()).select_from(Prediction)).scalar_one()
        )
        OPEN_ALERTS.set(
            session.execute(
                select(func.count()).select_from(Alert).where(Alert.acknowledged.is_(False))
            ).scalar_one()
        )

        # Latest prediction per drive with probability >= 0.7.
        latest = (
            select(Prediction.drive_id, func.max(Prediction.predicted_at).label("t"))
            .group_by(Prediction.drive_id)
            .subquery()
        )
        high_risk = session.execute(
            select(func.count())
            .select_from(Prediction)
            .join(
                latest,
                (latest.c.drive_id == Prediction.drive_id)
                & (latest.c.t == Prediction.predicted_at),
            )
            .where(Prediction.failure_probability >= 0.7)
        ).scalar_one()
        HIGH_RISK_DRIVES.set(high_risk)
    except Exception:  # noqa: BLE001 - never let metrics scraping fail the endpoint
        pass
