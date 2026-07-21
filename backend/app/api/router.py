"""Aggregate API router. New route modules are registered here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)

# Phase 2+ routers (drives, predict, retrieve, chat) get included here as they land.
