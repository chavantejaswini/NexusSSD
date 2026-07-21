"""Health check endpoint — reports app + database status."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """Return service health, actively pinging the database with SELECT 1."""
    db_status: str = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - report any DB failure as degraded
        logger.warning("health check DB ping failed: %s", exc)
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        db=db_status,  # type: ignore[arg-type]
        version=settings.version,
        environment=settings.environment,
    )
