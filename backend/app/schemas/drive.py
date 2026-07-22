"""Pydantic response schemas for drive endpoints."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TelemetryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    power_on_hours: int
    temperature: float
    reallocated_sectors: int
    media_wearout_indicator: float
    pct_used: float


class LatestPrediction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_version: str
    failure_probability: float
    horizon_days: int
    predicted_at: datetime


class DriveSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_number: str
    model: str
    capacity_bytes: int
    status: str
    first_seen: date
    last_seen: date
    latest_failure_probability: float | None = None


class DriveDetail(DriveSummary):
    telemetry: list[TelemetryPoint] = []
    latest_prediction: LatestPrediction | None = None


class PaginatedDrives(BaseModel):
    items: list[DriveSummary]
    total: int
    limit: int
    offset: int
