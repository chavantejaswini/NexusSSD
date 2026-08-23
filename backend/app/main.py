"""FastAPI application factory and entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import ObservabilityMiddleware


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    logger = get_logger(__name__)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Agentic AI Fleet Health Copilot for SSD telemetry.",
    )

    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"name": settings.app_name, "version": settings.version, "docs": "/docs"}

    logger.info(
        "application initialized",
        extra={"environment": settings.environment, "version": settings.version},
    )
    return app


app = create_app()
