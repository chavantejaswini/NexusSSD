"""Aggregate API router. New route modules are registered here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import drives, health, predict

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(drives.router)
api_router.include_router(predict.router)

# Phase 4+ routers (retrieve, chat) get included here as they land.
