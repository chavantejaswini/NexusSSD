"""Aggregate API router. New route modules are registered here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import drives, health, predict, retrieve

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(drives.router)
api_router.include_router(predict.router)
api_router.include_router(retrieve.router)

# Phase 5+ routers (chat) get included here as they land.
