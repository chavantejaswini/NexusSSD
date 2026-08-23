"""Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.core.metrics import refresh_domain_gauges
from app.db.session import get_db

router = APIRouter(tags=["system"])


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)) -> Response:
    refresh_domain_gauges(db)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
