"""Aggregate API router. New route modules are registered here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import drives, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(drives.router)

# Phase 3+ routers (predict, retrieve, chat) get included here as they land.
