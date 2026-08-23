"""Observability middleware: correlation IDs, structured request logs, metrics."""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger("app.request")

_REQUEST_ID_HEADER = "X-Request-ID"


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start
        # Use the matched route template as the label to bound cardinality.
        route = request.scope.get("route")
        path = getattr(route, "path", None) or "unmatched"

        REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(duration)
        response.headers[_REQUEST_ID_HEADER] = request_id

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        return response
