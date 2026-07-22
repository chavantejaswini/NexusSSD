"""Drive listing and detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.drive import DriveDetail, PaginatedDrives
from app.services import drive_service

router = APIRouter(prefix="/drives", tags=["drives"])


@router.get("", response_model=PaginatedDrives)
def list_drives(
    status: str | None = Query(default=None, description="Filter by drive status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedDrives:
    items, total = drive_service.list_drives(db, status=status, limit=limit, offset=offset)
    return PaginatedDrives(items=items, total=total, limit=limit, offset=offset)


@router.get("/{drive_id}", response_model=DriveDetail)
def get_drive(
    drive_id: int,
    telemetry_limit: int = Query(default=180, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> DriveDetail:
    detail = drive_service.get_drive_detail(db, drive_id, telemetry_limit=telemetry_limit)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"drive {drive_id} not found")
    return DriveDetail.model_validate(detail)
